# 05 · Docker Compose

> Time: 25 minutes

Eight containers started by hand mean eight long `docker run` commands, two networks, a volume and the right order.
Docker Compose describes all of it in one file, [compose/docker-compose.yml](../compose/docker-compose.yml), and
starts it with one command.

```text
 Dockerfile ──docker build──► image ──┐
 Dockerfile ──docker build──► image ──┼── docker-compose.yml ──docker compose up──► 8 running containers
 Dockerfile ──docker build──► image ──┘    (services, networks,                     on 2 networks, 1 volume
       ... × 8                               volumes, environment)
```

## Services: build or image

Each entry under `services:` becomes one or more containers. A service either **builds** its image or **uses** one:

```yaml
  node-api:
    build: { context: ../applications/node-api, args: { APP_VERSION: "1.0.0" } }   # how to build it
    image: node-api:1.0.0                                                            # the name to give it
```

With both `build:` and `image:`, Compose builds the image and tags it `node-api:1.0.0`: the very same name the
Kubernetes manifests use. `postgres` only has `image: postgres:18.6-alpine`: it is downloaded, never built.
`laravel-fpm` has no `build:` because `laravel-migrate` already builds that same image.

## Networks: who may talk to whom

```text
        frontend network                         backend network
  ┌──────────────────────────────┐   ┌───────────────────────────────────────────────┐
  │ frontend   laravel-web        │   │ frontend  laravel-web  node-api  python-api    │
  │ go-status                     │   │ java-api  go-status    laravel-fpm  postgres   │
  └──────────────────────────────┘   │ laravel-migrate  report-worker                  │
                                      └───────────────────────────────────────────────┘
```

`postgres` is only on `backend`. A container that is only on `frontend` could not even resolve the name `postgres`.
Containers that must bridge the two (the frontend proxies to the APIs, go-status checks everyone) are on both.

## Service discovery: names, not IP addresses

On a Compose network every service is reachable by its **service name**: Docker's embedded DNS (127.0.0.11) answers
`postgres`, `node-api`, `laravel-fpm` with the containers' current addresses. That is why the configuration says
`DB_HOST: postgres` and never an IP address. Containers get new addresses when they are recreated; names stay.

## Environment and the .env file

The database settings are written once and reused with a YAML anchor:

```yaml
x-db-env: &db-env
  DB_HOST: postgres
  DB_PORT: "5432"
  DB_NAME: bookshop
  DB_USER: bookshop
  DB_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD in compose/.env}
```

- `${DB_PASSWORD}` is read from the shell or from `compose/.env` (not committed; `.env.example` shows the shape).
- `:?message` makes the variable **required**: `docker compose up` stops with that message instead of starting a
  database with an empty password.
- `environment: *db-env` gives a service the whole block; `<<: *db-env` merges it and lets you add keys (the
  Laravel services add `APP_KEY`).

## Volumes: data that outlives containers

```yaml
    volumes:
      - pgdata:/var/lib/postgresql
...
volumes:
  pgdata: {}
```

`pgdata` is a named volume managed by Docker. `docker compose down` removes the containers but keeps the volume;
only `docker compose down -v` deletes it, and the data with it.

## Ports: from your computer into a container

```yaml
    ports: ["127.0.0.1:8081:8080"]       # frontend: host 127.0.0.1:8081 → container port 8080
```

`HOST_IP:HOST_PORT:CONTAINER_PORT`. Binding to `127.0.0.1` keeps the port off your network: only your own computer
can reach it. Only two services publish ports, `frontend` (8081) and `laravel-web` (8082). The APIs and the database
are reachable **only** from other containers: nothing outside needs them directly.

## Start order: depends_on and healthchecks

`depends_on` alone only waits until a container has **started**, not until the program inside is ready. A Spring Boot
API that has started may still need seconds before it answers. The lab therefore combines `depends_on` with
**conditions**:

| Condition | Meaning | Used for |
|---|---|---|
| `service_started` | the container is running | `go-status` (its distroless image has no shell or wget to run a check) |
| `service_healthy` | the container's `healthcheck` passes | `postgres` before the APIs; the APIs before `frontend` |
| `service_completed_successfully` | a one-off container exited with 0 | `laravel-migrate` before `laravel-fpm` |

The healthchecks call each API's `/ready` endpoint, for example:

```yaml
    healthcheck:                       # Compose's version of a readiness check (Kubernetes: readinessProbe)
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8080/ready"]
      interval: 3s
      timeout: 3s
      retries: 40
```

## One-off tasks and profiles

- **`laravel-migrate`** runs `php artisan migrate --force --seed` once and exits (`restart: "no"`). The real FPM
  service starts only after it succeeded. One image, two roles: the same `laravel-fpm:1.0.0` with a different command.
- **`report-worker`** has `profiles: [jobs]`. `docker compose up` ignores it; you run it on demand with
  `docker compose run --rm report-worker`, and it exits after saving its report.

## The commands

| Command | Does |
|---|---|
| `docker compose build` | builds every service that has `build:` |
| `docker compose up -d` | creates networks and volumes, starts everything in dependency order, in the background |
| `docker compose ps` | the containers of this project, their state and health |
| `docker compose logs -f node-api` | the stdout/stderr of a service (follow with `-f`) |
| `docker compose exec node-api sh` | a shell (or any command) inside a running container |
| `docker compose run --rm report-worker` | a new one-off container of a service, removed afterwards |
| `docker compose down` | stops and removes containers and networks (volumes stay) |
| `docker compose down -v` | ... and the volumes: **the database is gone** |

## What Compose is for, and where it stops

Compose is excellent for **one machine**: development, demos, tests in CI, small single-server deployments. It does
not:

- spread containers over several machines, or move them when a machine dies;
- replace a crashed container on another host (it can only restart it in place with a `restart:` policy);
- update a service without downtime (no rolling updates with readiness gating);
- give you per-service traffic routing from outside without an extra proxy;
- scale based on load.

Those are exactly the things Kubernetes adds. The next lesson maps every part of this file to a Kubernetes resource.

## Check yourself

<details><summary>What is the difference between <code>depends_on: [x]</code> and <code>depends_on: {x: {condition: service_healthy}}</code>?</summary>

The first waits only until container x has started. The second waits until x's healthcheck passes, i.e. until the
application inside actually answers.
</details>

<details><summary>Why can no container on only the <code>frontend</code> network connect to PostgreSQL?</summary>

`postgres` is only on the `backend` network. Containers can only reach (and resolve the names of) containers on a
network they share.
</details>

<details><summary>What does <code>${DB_PASSWORD:?set DB_PASSWORD in compose/.env}</code> do when the variable is missing?</summary>

Compose refuses to start and prints the message. Nothing starts with an empty password.
</details>

<details><summary>You run <code>docker compose down</code>. Are the reviews and users still there after <code>up -d</code>?</summary>

Yes. `down` keeps named volumes; the data lives in the `pgdata` volume. Only `down -v` deletes it.
</details>

<details><summary>Why is report-worker in a profile?</summary>

It is a batch job, not a server. With the `jobs` profile, `up` does not start it; you run it when you want a report
with `docker compose run --rm report-worker`.
</details>

Next: [06 · From Docker Compose to Kubernetes](06-compose-to-kubernetes.md)
