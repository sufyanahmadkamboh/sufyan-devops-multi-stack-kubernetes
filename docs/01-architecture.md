# 01 · The Bookshop architecture

> Time: 20 minutes

This lab is one small but complete platform, the **Bookshop**. It is made of seven applications written in six
languages and frameworks, plus a PostgreSQL database. Every application is deliberately simple: the subject of the
lab is **how they are packaged, connected and deployed**, not what they do.

## The services

| Service | Stack | Port | What it does | Talks to |
|---|---|---|---|---|
| `frontend` | React 19 + Vite 8, served by nginx | 8080 | the web page: books, users, statistics, service status | the APIs, through `/api/...` |
| `node-api` | Node.js 24 + Express 5 | 3000 | users: `GET/POST /api/users` | PostgreSQL |
| `python-api` | Python 3.14 + FastAPI | 8000 | statistics: `GET /api/stats` | PostgreSQL (read only) |
| `go-status` | Go 1.27, standard library only | 8080 | status board: `GET /api/status` checks every service's `/health` | every service, over HTTP |
| `java-api` | Java 25 + Spring Boot 4.1 | 8080 | books: `GET /api/books`, `GET /api/books/{id}` | PostgreSQL |
| `laravel-admin` | PHP 8.5 + Laravel 13 (nginx + PHP-FPM) | 8080 | book reviews: list and add (an HTML page) | PostgreSQL |
| `report-worker` | JavaScript on Node.js 24 | – | a batch job: collects statistics and status, saves one report row, exits | `python-api`, `go-status`, PostgreSQL |
| `postgres` | PostgreSQL 18 | 5432 | the database `bookshop` | – |

Each service owns its tables: `node-api` → `users`, `java-api` → `books`, `laravel-admin` → `reviews`,
`report-worker` → `reports`. `python-api` only reads. The full rules every service follows are in
[CONTRACT.md](CONTRACT.md).

## The picture

```text
                                 Browser
                                    │
                                    ▼
                   ┌──────────── entry point ────────────┐
                   │  Compose:    frontend's nginx        │
                   │  Kubernetes: Ingress (Traefik)       │
                   └──────────────────┬───────────────────┘
          ┌───────────────┬───────────┼──────────────┬───────────────┐
          ▼               ▼           ▼              ▼               ▼
      frontend        node-api    java-api      python-api       go-status ──► /health of
      (React)         /api/users  /api/books    /api/stats       /api/status   every service
                          │           │              │
                          └───────────┼──────────────┘
                                      ▼
   laravel-admin (nginx + FPM) ──► postgres ◄── report-worker (a Job: runs, saves a report, exits)
       admin page                (one volume)
```

## One request, from the browser to the database

You open the Bookshop page and the Books panel loads. This is what happens in Kubernetes:

```text
 1. Browser      GET http://bookshop.localhost:8080/            → the Ingress sends "/" to the frontend Service
 2. frontend     returns index.html and the JavaScript bundle   (nginx serves static files, nothing else runs)
 3. Browser      runs React; React calls GET /api/books         (a relative URL: same host, same port)
 4. Ingress      rule "path /api/books → java-api:8080"         (Traefik reads this rule from the Ingress object)
 5. Service      java-api picks one Ready java-api Pod          (only Pods that pass their readiness probe)
 6. java-api     SELECT id, title, author, year FROM books      (host "postgres", port 5432)
 7. Service      postgres → the postgres-0 Pod
 8. back         rows → JSON → Ingress → browser → React draws the list
```

The code that renders the page runs **in your browser**, not in the cluster. The frontend container only hands out
files. That is why the API calls go through the same entry point as the page.

## The same platform in Compose and in Kubernetes

The applications and images are identical. What changes is **who routes the traffic**:

```text
 Docker Compose (one machine)                     Kubernetes (a cluster)

 browser → localhost:8081                         browser → bookshop.localhost:8080
             │                                                 │
             ▼                                                 ▼
         frontend's nginx                                 Ingress (Traefik)
          ├─ "/"          → its own files                  ├─ "/"           → Service frontend
          ├─ /api/users   → node-api:3000                  ├─ /api/users    → Service node-api
          ├─ /api/books   → java-api:8080                  ├─ /api/books    → Service java-api
          ├─ /api/stats   → python-api:8000                ├─ /api/stats    → Service python-api
          └─ /api/status  → go-status:8080                 └─ /api/status   → Service go-status
 admin:  localhost:8082 → laravel-web                     admin: admin.bookshop.localhost:8080
```

The frontend's nginx can proxy `/api/...` by itself
([default.conf.template](../applications/frontend/nginx/default.conf.template)), which is what makes the page work
in Compose without anything else. In Kubernetes the [Ingress](../kubernetes/ingress/ingress.yaml) does that job for
every Pod, so the API traffic never passes through the frontend at all.

## Why every service keeps its name

`node-api` is called `node-api` in Compose **and** in Kubernetes. That is not a coincidence: both platforms give
every service a DNS name.

| | Compose | Kubernetes |
|---|---|---|
| Who answers the name `node-api`? | Docker's embedded DNS on the project network | CoreDNS: the Service `node-api` in namespace `bookshop` |
| What does the name point to? | the container(s) of the service | the Service's virtual IP, which spreads requests over the Ready Pods |
| Full name | `node-api` | `node-api.bookshop.svc.cluster.local` (short `node-api` works inside the namespace) |

Because the names match, the applications need **no change** between Compose and Kubernetes: `DB_HOST=postgres`
works in both, and so does `go-status`'s target list
(`node-api=http://node-api:3000/health,...`). Configuration differs; code does not.

## Check yourself

<details><summary>Which component runs the React code, the frontend container or the browser?</summary>

The browser. The frontend container (nginx) only serves `index.html` and the built JavaScript files. React then runs
in the browser and calls the APIs over HTTP.
</details>

<details><summary>In Kubernetes, does a request for <code>/api/books</code> pass through the frontend?</summary>

No. The Ingress has its own rule for `/api/books` and sends it straight to the `java-api` Service. In Compose there is
no Ingress, so the frontend's nginx forwards it.
</details>

<details><summary>Why does <code>DB_HOST=postgres</code> work in both Compose and Kubernetes?</summary>

Both give the database a DNS name `postgres`: in Compose the service name, in Kubernetes the Service name in the same
namespace. The application just resolves the name.
</details>

<details><summary>Which service writes to the <code>reviews</code> table, and which only reads it?</summary>

`laravel-admin` owns and writes it (its migrations create it). `python-api` reads it to count reviews.
</details>

<details><summary>What is special about <code>report-worker</code> compared with the other services?</summary>

It is not a server. It starts, does one job (collect statistics, save a report) and exits. In Compose it is run on
demand; in Kubernetes it becomes a Job, created on a schedule by a CronJob.
</details>

Next: [02 · Why multiple technology stacks?](02-why-multiple-stacks.md)
