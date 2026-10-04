# Docker Compose · the whole platform on one machine

> Levels 5–6 of the [roadmap](../README.md). Time: about 45 minutes. You need Docker with Compose v2
> (`docker compose version`), and the images from the [application lessons](../applications/) (Compose builds any
> that are missing).

Every application already works **alone**, as one container. A real system is several containers that must find each
other, share a database, start in a sensible order and be configured consistently. Typing seven `docker run` commands
with the right networks, variables and ports every time is error-prone. **Docker Compose** describes all of it in one
file, [docker-compose.yml](docker-compose.yml), and runs it with one command.

```text
                        your computer
   http://localhost:8081            http://localhost:8082
            │                                 │
 ┌──────────┼─────────── frontend network ────┼──────────────────────────────────┐
 │          ▼                                 ▼                                  │
 │      frontend (React + nginx)          laravel-web (nginx)                    │
 │          │ /api/users  /api/books  /api/stats  /api/status                    │
 │          ▼            ▼            ▼            ▼                             │
 │      node-api      java-api    python-api    go-status ── checks every /health│
 └──────────┼────────────┼────────────┼──────────────────────────────────────────┘
 ┌──────────┼────────────┼────────────┼────────── backend network ───────────────┐
 │          ▼            ▼            ▼            laravel-fpm (PHP-FPM)         │
 │      postgres (PostgreSQL 18, volume pgdata)  ◄──────┘                         │
 │      report-worker (runs on demand) · laravel-migrate (runs once)             │
 └───────────────────────────────────────────────────────────────────────────────┘
```

The concepts behind each part of the file are in [docs/05](../docs/05-docker-compose.md). This lesson runs it.

## Step 1 · Configuration: the .env file

Compose reads variables for the file from `compose/.env`. Two values are secrets, so the repository contains only
[.env.example](.env.example), and `.gitignore` keeps `.env` out of Git. Generate real values:

<!-- test: contains=DB_PASSWORD -->
```bash
cd compose
printf 'DB_PASSWORD=%s\nAPP_KEY=base64:%s\n' "$(openssl rand -hex 16)" "$(openssl rand -base64 32)" > .env
cut -d= -f1 .env
```

(`cut -d= -f1` prints only the variable names: never print secrets to your screen, or into a lesson.)

The file uses them with a guard: `${DB_PASSWORD:?set DB_PASSWORD in compose/.env}` makes Compose refuse to start, with
that message, when the variable is missing. Ask Compose which services the file defines:

<!-- test: contains=node-api; contains=laravel-migrate; output -->
```bash
docker compose config --services
```

```text
go-status
postgres
laravel-migrate
python-api
java-api
node-api
frontend
laravel-fpm
laravel-web
```

`report-worker` is missing from the list on purpose: it is in the profile `jobs` and only runs when asked (Step 7).

## Step 2 · Build

`build:` tells Compose where each Dockerfile is; `image:` is the name and versioned tag of the result. One command
builds them all (the first time takes several minutes: Java and Laravel download many dependencies; afterwards the
layer cache makes it fast):

<!-- test: timeout=2400; output=tail:8 -->
```bash
docker compose build
```

```text
...
#107 DONE 0.0s
 Image java-api:1.0.0 Built 
 Image python-api:1.0.0 Built 
 Image go-status:1.0.0 Built 
 Image laravel-fpm:1.0.0 Built 
 Image laravel-web:1.0.0 Built 
 Image frontend:1.0.0 Built 
 Image node-api:1.0.0 Built 
```

<!-- test: contains=node-api; contains=laravel-fpm; output -->
```bash
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep -E 'REPOSITORY|1\.0\.0'
```

```text
REPOSITORY               TAG                             SIZE
laravel-fpm              1.0.0                           222MB
java-api                 1.0.0                           348MB
laravel-web              1.0.0                           81.5MB
frontend                 1.0.0                           81.8MB
go-status                1.0.0                           16.4MB
report-worker            1.0.0                           246MB
node-api                 1.0.0                           251MB
python-api               1.0.0                           261MB
```

Seven languages and frameworks, and Compose treated them all the same: a build context, a Dockerfile, an image.

## Step 3 · Start everything

`docker compose up` starts all services in the foreground and streams their logs into your terminal (Ctrl+C stops
them). That is useful when you develop; to get your terminal back, run it detached with `-d`. `--wait` waits until
every service is running and healthy:

<!-- test: skip -->
```bash
docker compose up
```

<!-- test: timeout=900; contains=Healthy; output=tail:10 -->
```bash
docker compose up -d --wait
```

```text
...
 Container bookshop-node-api-1 Waiting 
 Container bookshop-laravel-migrate-1 Exited 
 Container bookshop-go-status-1 Healthy 
 Container bookshop-frontend-1 Healthy 
 Container bookshop-node-api-1 Healthy 
 Container bookshop-java-api-1 Healthy 
 Container bookshop-laravel-fpm-1 Healthy 
 Container bookshop-laravel-web-1 Healthy 
 Container bookshop-postgres-1 Healthy 
 Container bookshop-python-api-1 Healthy 
```

The order is not random. `depends_on` with conditions in the file:

| Service | Waits for | Why |
|---|---|---|
| node-api, python-api, java-api | postgres **healthy** (`pg_isready`) | no point connecting to a database that is still starting |
| laravel-migrate | postgres healthy | creates the `reviews` table, then exits |
| laravel-fpm | laravel-migrate **completed successfully** | the app needs its table |
| frontend | node-api, python-api, java-api **healthy** (their `/ready` endpoint) | otherwise the first page shows errors while Java is still starting |

Without health conditions, `depends_on` only waits until the other **container started**, not until the application
inside is ready. That difference matters again in Kubernetes ([docs/08](../docs/08-health-probes.md)).

## Step 4 · ps and logs

<!-- test: contains=healthy; output -->
```bash
docker compose ps --format 'table {{.Service}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

```text
SERVICE       IMAGE                  STATUS                    PORTS
frontend      frontend:1.0.0         Up 1 second               127.0.0.1:8081->8080/tcp
go-status     go-status:1.0.0        Up 11 seconds             8080/tcp
java-api      java-api:1.0.0         Up 8 seconds (healthy)    8080/tcp
laravel-fpm   laravel-fpm:1.0.0      Up 7 seconds              9000/tcp
laravel-web   laravel-web:1.0.0      Up 6 seconds              127.0.0.1:8082->8080/tcp
node-api      node-api:1.0.0         Up 8 seconds (healthy)    3000/tcp
postgres      postgres:18.6-alpine   Up 11 seconds (healthy)   5432/tcp
python-api    python-api:1.0.0       Up 8 seconds (healthy)    8000/tcp
```

Only two services publish a port on your computer (`127.0.0.1:8081` and `127.0.0.1:8082`), and only on `127.0.0.1`
(your machine, not your network). Everything else is reachable only from other containers.

The logs of one service (`-f` follows them live; Ctrl+C to stop following):

<!-- test: contains=java-api; output=tail:4 -->
```bash
docker compose logs --tail 4 java-api
```

```text
java-api-1  | 2026-10-04T18:12:38.424Z INFO  SchemaInitializer - books table ready
java-api-1  | 2026-10-04T18:12:40.677Z INFO  DispatcherServlet - Initializing Servlet 'dispatcherServlet'
java-api-1  | 2026-10-04T18:12:40.679Z INFO  DispatcherServlet - Completed initialization in 2 ms
java-api-1  | 2026-10-04T18:12:40.745Z INFO  request - GET /ready 200 61ms
```

## Step 5 · Use it

The UI at <http://localhost:8081>, and the same APIs from the terminal, through the frontend's nginx:

<!-- test: retry=20; contains=Pride and Prejudice; output -->
```bash
curl -s http://localhost:8081/api/books | head -c 160; echo
curl -s http://localhost:8081/api/stats; echo
```

```text
[{"id":1,"title":"Pride and Prejudice","author":"Jane Austen","year":1813},{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851},{"id":3,"title":"
{"users":3,"books":5,"reviews":3,"latest_report":null}
```

<!-- test: retry=20; contains=6 of 6 services up; output -->
```bash
curl -s http://localhost:8081/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['up']} of {d['total']} services up\"); [print(f\"  {s['name']:14} {s['status']}\") for s in d['services']]"
```

```text
6 of 6 services up
  frontend       up
  go-status      up
  java-api       up
  laravel-admin  up
  node-api       up
  python-api     up
```

The reviews admin (Laravel) at <http://localhost:8082>:

<!-- test: contains=Reviews; output -->
```bash
curl -s http://localhost:8082/ | grep -o '<title>[^<]*</title>'
```

```text
<title>Bookshop · Reviews</title>
```

## Step 6 · Inside the network: exec, service discovery, isolation

`docker compose exec` runs a command in a running service's container. From `node-api`, every other service is
reachable **by its service name**: Compose runs a DNS server for the project's networks.

<!-- test: contains=Moby-Dick; output -->
```bash
docker compose exec node-api wget -qO- http://java-api:8080/api/books/2; echo
```

```text
{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851}
```

The database is on the `backend` network only. The frontend container is on the `frontend` network only, so for it
the name `postgres` does not even exist:

<!-- test: fail; contains=bad address; output -->
```bash
docker compose exec frontend wget -qO- -T 3 http://postgres:5432
```

```text
wget: bad address 'postgres:5432'
```

<!-- test: contains=bookshop_backend; contains=bookshop_frontend; output -->
```bash
docker network ls --filter name=bookshop
```

```text
NETWORK ID     NAME                DRIVER    SCOPE
1dcaecabbe44   bookshop_backend    bridge    local
73680aa65769   bookshop_frontend   bridge    local
```

A quick look into the database, with the `psql` client inside the `postgres` container:

<!-- test: contains=books; output -->
```bash
docker compose exec postgres psql -U bookshop -d bookshop -c '\dt'
```

```text
             List of tables
 Schema |    Name    | Type  |  Owner   
--------+------------+-------+----------
 public | books      | table | bookshop
 public | migrations | table | bookshop
 public | reviews    | table | bookshop
 public | users      | table | bookshop
(4 rows)
```

Tables created by three different applications in three languages: `users` (Node.js), `books` (Java) and `reviews`
(Laravel's migration; `migrations` is Laravel's own record of which migrations already ran). One more, `reports`,
appears in the next step.

## Step 7 · A one-off job: report-worker

The JavaScript worker is not a server: it starts, writes a report, and exits. It is in the profile `jobs`, so `up`
does not start it. `run --rm` starts it once and removes the container afterwards:

<!-- test: timeout=300; contains=saved; output=tail:1 -->
```bash
docker compose run --rm report-worker
```

```text
...
2026-10-04T18:12:52.220Z report-worker report #1 saved: users=3 books=5 reviews=3 services up=6/6
```

<!-- test: contains=latest_report; output -->
```bash
curl -s http://localhost:8081/api/stats; echo
```

```text
{"users":3,"books":5,"reviews":3,"latest_report":{"id":1,"created_at":"2026-10-04T18:12:52.217894+00:00","users":3,"books":5,"reviews":3,"services_up":6,"services_total":6}}
```

## Step 8 · Data survives `down`, unless you add `-v`

Add a user, stop and remove all containers, start again:

<!-- test: contains=Margaret Hamilton; output -->
```bash
curl -s -X POST http://localhost:8081/api/users -H 'Content-Type: application/json' -d '{"name":"Margaret Hamilton","email":"margaret@example.com"}'; echo
```

```text
{"id":4,"name":"Margaret Hamilton","email":"margaret@example.com","created_at":"2026-10-04T18:12:53.164Z"}
```

```text
⚠️ DESTRUCTIVE COMMAND · stops and removes all containers and networks of the project (the volume pgdata stays).
```

<!-- test: timeout=300; output=tail:4 -->
```bash
docker compose down
```

```text
...
 Network bookshop_backend Removing 
 Network bookshop_frontend Removing 
 Network bookshop_backend Removed 
 Network bookshop_frontend Removed 
```

<!-- test: timeout=900; retry=20; contains=Margaret Hamilton -->
```bash
docker compose up -d --wait > /dev/null 2>&1
curl -s http://localhost:8081/api/users
```

The containers are new; the user is still there, because PostgreSQL's files live in the named **volume** `pgdata`, not in
the container.

## Step 9 · Clean up

```text
⚠️ DESTRUCTIVE COMMAND · removes containers, networks AND the volume pgdata: every row in the database is deleted.
```

<!-- test: timeout=300; contains=Removed; output=tail:5 -->
```bash
docker compose --profile jobs down -v
```

```text
...
 Volume bookshop_pgdata Removing 
 Network bookshop_frontend Removing 
 Volume bookshop_pgdata Removed 
 Network bookshop_backend Removed 
 Network bookshop_frontend Removed 
```

<!-- test: absent=bookshop -->
```bash
docker volume ls --filter name=bookshop -q
docker ps -a --filter name=bookshop -q
cd ..
```

The images stay (Kubernetes uses them next). `docker image rm` would remove them.

## What Compose gave us, and what it did not

| Compose did | Compose did not |
|---|---|
| build 8 images from 7 stacks with one command | run on more than one machine |
| start them in a sensible order, waiting for health | restart a service elsewhere if this machine fails |
| networks with DNS names, isolation between them | roll out a new version without downtime |
| one place for configuration, with required variables | scale across machines, balance load across them |
| a volume that outlives the containers | give each team a separate, access-controlled namespace |

The right column is what Kubernetes is for. Next: how each line of this file becomes a Kubernetes resource:
[docs/06 · From Docker Compose to Kubernetes](../docs/06-compose-to-kubernetes.md), then
[the Kubernetes lessons](../kubernetes/README.md).

## Practical challenge

**Task.** Add a second copy of `python-api` to the Compose project, called `python-api-2`, and prove that both answer.

**Requirements.** Same image, same database settings (reuse the `x-db-env` anchor), no published port, reachable from
`node-api` by name.

**Hints.** Copy the `python-api` service block; you do not need `build:` again. `docker compose up -d python-api-2`.

**Expected result.** `docker compose exec node-api wget -qO- http://python-api-2:8000/health` prints the health JSON.

<details>
<summary>Solution</summary>

```text
  python-api-2:
    image: python-api:1.0.0
    environment: *db-env
    depends_on:
      postgres: { condition: service_healthy }
    networks: [frontend, backend]
```

Then `docker compose up -d python-api-2` and the `exec` command above.
</details>

**Explanation.** Compose services are named containers with a configuration. Two copies need two service names (or
`docker compose up --scale python-api=2`, which gives one name with DNS round-robin), and you manage them by hand.
In Kubernetes you change one number, `replicas`, and a Service balances the traffic: [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md).
