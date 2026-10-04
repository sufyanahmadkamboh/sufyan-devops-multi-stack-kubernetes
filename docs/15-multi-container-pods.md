# 15 · Multi-container Pods

> Time: 20 minutes

## Why Laravel is two programs

A Node.js, Python, Go or Java API is **one process** that both speaks HTTP and runs the application. PHP traditionally
works differently:

```text
 browser ──HTTP──► nginx ──FastCGI──► PHP-FPM ──runs──► Laravel (index.php)
                   web server          PHP process manager
                   - static files      - a pool of PHP worker processes
                   - HTTP, buffering   - runs one PHP request per worker
```

- **nginx** handles HTTP: it serves CSS, JS and images directly and forwards only `*.php` requests.
- **PHP-FPM** (FastCGI Process Manager) keeps a pool of PHP processes and runs the PHP code. It does not speak HTTP;
  it speaks **FastCGI**, on port 9000.

Two programs, two images: `laravel-web:1.0.0` (nginx with the `public/` assets) and `laravel-fpm:1.0.0` (PHP 8.5 with
the application). One process per container keeps each image small, lets each be updated on its own, and gives each
its own logs and health check.

## In Compose: two services

From [compose/docker-compose.yml](../compose/docker-compose.yml):

```text
  laravel-fpm:
    image: laravel-fpm:1.0.0
    ...
  laravel-web:
    image: laravel-web:1.0.0
    environment:
      FPM_HOST: laravel-fpm          ← nginx reaches FPM over the Compose network, by service name
    ports: ["127.0.0.1:8082:8080"]
```

## In Kubernetes: one Pod, two containers

From [kubernetes/laravel-admin/deployment.yaml](../kubernetes/laravel-admin/deployment.yaml):

```text
    spec:
      containers:
        - name: laravel-web
          image: laravel-web:1.0.0
          env:
            - name: FPM_HOST
              value: "127.0.0.1"               # the other container of this Pod
        - name: laravel-fpm
          image: laravel-fpm:1.0.0
          ports:
            - name: fastcgi
              containerPort: 9000
```

All containers of a Pod share **one network namespace**: one IP address, one `localhost`. nginx reaches PHP-FPM at
`127.0.0.1:9000` without any Service. They are also scheduled together (same node), scaled together (a replica is the
pair) and started and stopped together.

```text
 Pod laravel-admin-...   (one Pod IP, one localhost)
   laravel-web (nginx :8080)  ──127.0.0.1:9000──►  laravel-fpm (php-fpm :9000)
          ▲
 Service laravel-admin:8080 → only port 8080 is exposed; FPM is reachable only inside the Pod
```

## Sidecar in one Pod, or two Deployments?

Both designs work; they make different trade-offs.

| | One Pod, two containers (this lab) | Two Deployments + a Service for FPM |
|---|---|---|
| Communication | `127.0.0.1`, no Service, no network hop | over the cluster network, through a Service |
| Scaling | together: every replica is one nginx + one FPM | independently (e.g. 2 nginx, 6 FPM) |
| Updates | one rollout replaces both | separately |
| Fits when | the two are tightly coupled and always used as a pair | they scale very differently, or one serves several others |

Rule of thumb: put containers in one Pod only when they **must** run together on the same machine and share its
network (or files). Otherwise, give each its own Deployment. Classic sidecars: a web server in front of an app server
(this lab), a log shipper, a proxy of a service mesh.

## Init containers and native sidecars

A Pod can also have **init containers**: they run to completion, one after another, **before** the main containers
start (for example: wait until the database answers, or prepare files in a shared volume). Since Kubernetes 1.29,
an init container with `restartPolicy: Always` is a **native sidecar**: it starts before the main containers, keeps
running alongside them, and is stopped after them, which fixes ordering problems of classic sidecars (for example in
Jobs, where a classic sidecar would keep the Pod from ever completing).

## Probing a container that doesn't speak HTTP

nginx has an HTTP probe on `/health` and `/ready`. PHP-FPM speaks FastCGI, not HTTP, so an `httpGet` probe can't
talk to it. Its liveness probe only checks that it accepts TCP connections:

```text
          livenessProbe:
            tcpSocket: { port: fastcgi }        # FPM speaks FastCGI, not HTTP: check that it accepts connections
            periodSeconds: 10
```

The readiness of the whole Pod is checked through nginx: `laravel-web`'s `/ready` passes through PHP-FPM to Laravel,
which checks the database. One request tests nginx, FPM, Laravel and PostgreSQL. A Pod is Ready only when **all** its
containers are Ready.

## Check yourself

<details><summary>Why does `laravel-web` use `FPM_HOST=127.0.0.1` in Kubernetes but `laravel-fpm` in Compose?</summary>

In Kubernetes both containers are in one Pod and share its network namespace, so FPM is on localhost. In Compose they
are separate containers on a network, reached by service name.
</details>

<details><summary>What do you lose by putting nginx and PHP-FPM in one Pod?</summary>

Independent scaling and independent updates: each replica is always one nginx plus one FPM, and both are replaced in
the same rollout.
</details>

<details><summary>Why is FPM's liveness probe `tcpSocket` instead of `httpGet`?</summary>

PHP-FPM speaks FastCGI, not HTTP. A TCP check verifies it accepts connections; the HTTP checks go through nginx.
</details>

<details><summary>When is a Pod with two containers Ready?</summary>

When every one of its containers is Ready. Only then does the Service send it traffic.
</details>

<details><summary>What runs before the main containers of a Pod start?</summary>

The init containers, in order, each to completion. Native sidecars (init containers with `restartPolicy: Always`)
start before the main containers and keep running.
</details>

Next: [Deploy it](../kubernetes/README.md)
