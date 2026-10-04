# Service contract

Every application in this lab follows the same small contract. This is what makes them interchangeable for Docker,
Compose and Kubernetes: **Kubernetes does not care which language a container was written in, only how it behaves.**

## The platform: "Bookshop"

| Service (name = Compose service = Kubernetes Service) | Stack | Port | What it does | Talks to |
|---|---|---|---|---|
| `frontend` | React 19 + Vite 8, served by nginx (unprivileged) | 8080 | the web UI: books, users, statistics, service status | the APIs, through `/api/...` |
| `node-api` | Node.js 24 + Express 5 | 3000 | users: `GET/POST /api/users` | PostgreSQL |
| `python-api` | Python 3.14 + FastAPI | 8000 | statistics: `GET /api/stats` (counts + latest report) | PostgreSQL (read only) |
| `go-status` | Go 1.27, standard library only | 8080 | service status board: `GET /api/status` checks every service's `/health` | all services over HTTP |
| `java-api` | Java 25 + Spring Boot 4.1 | 8080 | books: `GET /api/books`, `GET /api/books/{id}` | PostgreSQL |
| `laravel-admin` | PHP 8.5 + Laravel 13: `laravel-fpm` (PHP-FPM) + `laravel-web` (nginx) | 8080 (nginx) / 9000 (FPM) | book reviews: list and add (server-rendered HTML) | PostgreSQL |
| `report-worker` | JavaScript (plain, no framework) on Node.js 24 | – | a batch job: collects stats and status, stores a report row, exits | `python-api`, `go-status`, PostgreSQL |
| `postgres` | PostgreSQL 18 | 5432 | the database `bookshop` | – |

## Rules for every HTTP service

1. **Port from the environment:** listen on `PORT` (default = the port in the table), on `0.0.0.0`.
2. **`GET /health`** returns HTTP 200 and JSON `{"status":"ok","service":"<name>","version":"<version>"}` as soon as the
   process can serve requests. It does **not** check the database (a database outage must not make Kubernetes restart
   every API). Services with a database also expose **`GET /ready`**: 200 `{"status":"ready",...}` when the database
   answers, 503 `{"status":"not ready","reason":"..."}` when it does not. (`/health` → liveness, `/ready` → readiness.)
3. **`GET /`** returns JSON with `service`, `version`, `language`, `runtime` and a one-line `description`.
4. **Version:** baked in at build time (`ARG APP_VERSION=1.0.0` → env `APP_VERSION`). The image tag equals the version.
5. **Configuration only from environment variables.** Database: `DB_HOST` (default `postgres`), `DB_PORT` (5432),
   `DB_NAME` (`bookshop`), `DB_USER` (`bookshop`), `DB_PASSWORD` (**required**, no default: a missing password must
   produce a clear error message and exit code 1 at startup).
6. **Logs:** one line per request and per important event, to **stdout** (never to files).
7. **Graceful shutdown** on SIGTERM.
8. **Non-root user** in the image, no secrets in the image, versioned base images, small final images (multi-stage
   where a build step exists), a `.dockerignore`.
9. **Database tables:** each service creates the tables it owns if they do not exist and seeds a few rows:
   `node-api` → `users`, `java-api` → `books`, `laravel-admin` → `reviews` (Laravel migrations, run as a separate
   step), `report-worker` → `reports`. `python-api` only reads (a missing table counts as 0).

## Endpoints

| Service | Endpoints |
|---|---|
| `node-api` | `/`, `/health`, `/ready`, `GET /api/users`, `POST /api/users` (`{"name","email"}`) |
| `python-api` | `/`, `/health`, `/ready`, `GET /api/stats` → `{"users":n,"books":n,"reviews":n,"latest_report":{...}|null}` |
| `go-status` | `/`, `/health`, `GET /api/status` → `{"services":[{"name","url","status":"up|down","http_status","latency_ms"}],"up":n,"total":n}`; targets from `TARGETS` = `name=url,name=url` |
| `java-api` | `/`, `/health`, `/ready`, `GET /api/books`, `GET /api/books/{id}` |
| `laravel-admin` | `/` (reviews page + form), `POST /reviews`, `/health`, `/ready` |
| `frontend` | `/` (the app), `/health`; in Compose its nginx also proxies `/api/users`, `/api/books`, `/api/stats`, `/api/status` to the services (in Kubernetes the Ingress does that routing) |

## Images

Local names `<service>:<version>`, for example `node-api:1.0.0`; published to GHCR as
`ghcr.io/sufyanahmadkamboh/bookshop-<service>:<version>`. Never `latest`.
