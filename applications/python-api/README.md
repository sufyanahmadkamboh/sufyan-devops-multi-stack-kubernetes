# python-api · Python + FastAPI

> The Bookshop's statistics service. Part of the [service contract](../../docs/CONTRACT.md). Time: 30 minutes.

## What is it?

**Python** is a general-purpose language; the program is run by an **interpreter** (CPython), so a Python container
needs the interpreter plus every library the code imports. **FastAPI** is a small web framework for JSON APIs, and
**uvicorn** is the web server that runs it. **psycopg** is the PostgreSQL driver.

Nothing is compiled ahead of time: the image ships source code, the interpreter and the installed packages. That is
why a Python image is much bigger than a Go image (compare with [go-status](../go-status/README.md)).

## What does the application do?

| Endpoint | Answer |
|---|---|
| `GET /` | name, version, language and runtime of the service |
| `GET /health` | `{"status":"ok"}` as soon as the web server runs (liveness) |
| `GET /ready` | `200` when the database answers, `503` with the reason when it does not (readiness) |
| `GET /api/stats` | the number of users, books and reviews, and the latest report row |

It only **reads**: the tables belong to other services (`users` → node-api, `books` → java-api, `reviews` →
laravel-admin, `reports` → report-worker). A table that does not exist yet counts as `0`, so the service works in any
start order.

| File | What it contains |
|---|---|
| [src/main.py](src/main.py) | the whole application (about 100 lines) |
| [requirements.txt](requirements.txt) | the dependencies, each pinned to an exact version |
| [Dockerfile](Dockerfile) | the two-stage image build |
| [.dockerignore](.dockerignore) | what is never sent to the image build |

Configuration comes only from environment variables: `PORT` (default 8000), `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`
and **`DB_PASSWORD`, which is required**: without it the service refuses to start with a clear message.

## How do I run it locally?

With Python 3.14 installed, from this folder:

<!-- test: skip -->
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DB_HOST=localhost DB_PASSWORD=example-only uvicorn src.main:app --port 8000
```

You also need a PostgreSQL to talk to. The tested path in this lab uses **Docker** for both, so you don't have to
install Python or PostgreSQL at all: that is what the rest of this page does.

## How do I build the Docker image?

From the repository root:

<!-- test: timeout=900; contains=python-api; output=tail:2 -->
```bash
docker build -t python-api:1.0.0 applications/python-api
docker images python-api
```

```text
...
IMAGE              ID             DISK USAGE   CONTENT SIZE   EXTRA
python-api:1.0.0   e43b578f2226        261MB           62MB        
```

The [Dockerfile](Dockerfile), line by line:

| Line | Why |
|---|---|
| `FROM python:3.14-slim AS build` | stage 1, the **build stage**: a slim Debian image with Python 3.14 |
| `RUN python -m venv /opt/venv` + `ENV PATH=...` | a virtual environment: all packages go into one folder we can copy later |
| `COPY requirements.txt .` then `RUN pip install ...` | dependencies first and code later: changing the code does not re-run `pip install` (layer cache) |
| `FROM python:3.14-slim` | stage 2, the **final image**, starts clean: no pip cache, no build leftovers |
| `ARG APP_VERSION=1.0.0` + `ENV APP_VERSION=...` | the version is baked in; the image tag says the same |
| `ENV PYTHONUNBUFFERED=1` | log lines reach `docker logs` / `kubectl logs` immediately instead of sitting in a buffer |
| `ENV PORT=8000` | default port, can be changed at run time |
| `RUN useradd --system --uid 10001 ...` + `USER 10001` | the process does **not** run as root |
| `COPY --from=build /opt/venv /opt/venv` | only the finished virtual environment is copied from stage 1 |
| `COPY src/ ./src/` | the application code, last (it changes most often) |
| `CMD ["sh", "-c", "exec uvicorn ... --port ${PORT}"]` | `sh -c` so `${PORT}` is expanded; `exec` so uvicorn becomes PID 1 and receives SIGTERM directly |

## How do I run the container?

The service needs a database. Create a private network and a PostgreSQL 18 container (the password is an example
value, used only in this lab):

<!-- test: contains=py-lab -->
```bash
docker network create py-lab
docker run -d --name py-lab-db --network py-lab \
  -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only \
  postgres:18.6-alpine
docker ps --filter name=py-lab-db --format '{{.Names}}  {{.Image}}  {{.Status}}'
```

<!-- test-run: for i in $(seq 60); do docker exec py-lab-db pg_isready -h 127.0.0.1 -U bookshop -d bookshop >/dev/null 2>&1 && exit 0; sleep 1; done; exit 1 -->

Now the API, on the same network, with port 8000 published as 18000 on your computer:

<!-- test: contains=py-lab-api -->
```bash
docker run -d --name py-lab-api --network py-lab -p 18000:8000 \
  -e DB_HOST=py-lab-db -e DB_PASSWORD=example-only \
  python-api:1.0.0
docker ps --filter name=py-lab --format '{{.Names}}  {{.Image}}  {{.Status}}'
```

`DB_HOST=py-lab-db`: on a Docker network, containers find each other **by name**.

## How does Docker Compose run it?

In [compose/docker-compose.yml](../../compose/README.md) the service is called `python-api`, gets its settings from
`environment:` and waits for PostgreSQL to be healthy (`depends_on: condition: service_healthy`). The database host is
simply `postgres`, the name of the database service.

## How does Kubernetes run it?

A **Deployment** keeps the wanted number of python-api Pods running, a **Service** named `python-api` gives them one
stable name and address, the database settings come from a **ConfigMap** and the password from a **Secret**. See
[kubernetes/README.md](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why |
|---|---|
| Deployment `python-api` | runs and replaces the Pods; rolling updates |
| Service `python-api` (port 8000) | the stable name the frontend, go-status and report-worker use |
| ConfigMap (`DB_HOST`, `DB_NAME`, ...) | non-secret settings, shared by all database clients |
| Secret (`DB_PASSWORD`) | the password, kept out of the image and the Deployment |
| `livenessProbe` → `/health` | restart the container only if the web server itself is stuck |
| `readinessProbe` → `/ready` | send traffic only while the database answers; a database outage does **not** restart the Pod |

## How do I verify it?

<!-- test: retry=20; contains="status":"ok"; output -->
```bash
curl -s http://localhost:18000/health
```

```text
{"status":"ok","service":"python-api","version":"1.0.0"}
```

<!-- test: retry=20; contains="status":"ready"; contains=Python; output -->
```bash
curl -s http://localhost:18000/
echo
curl -s http://localhost:18000/ready
```

```text
{"service":"python-api","version":"1.0.0","language":"Python","runtime":"CPython 3.14.8","description":"Statistics for the Bookshop: counts of users, books, reviews and the latest report"}
{"status":"ready","service":"python-api","version":"1.0.0"}
```

The statistics are all `0`: the tables belong to the other services and don't exist yet. Create a `users` table with
two rows, the way node-api will do it later, and ask again:

<!-- test: contains=INSERT 0 2 -->
```bash
docker exec py-lab-db psql -U bookshop -d bookshop -c \
  "CREATE TABLE users (id serial PRIMARY KEY, name text, email text);
   INSERT INTO users (name, email) VALUES ('Ada', 'ada@example.com'), ('Linus', 'linus@example.com');"
```

<!-- test: contains="users":2; output -->
```bash
curl -s http://localhost:18000/api/stats
```

```text
{"users":2,"books":0,"reviews":0,"latest_report":null}
```

Every request is one log line on standard output:

<!-- test: contains=GET /api/stats 200; output=tail:4 -->
```bash
docker logs py-lab-api
```

```text
...
2026-10-04 17:51:44,882 INFO python-api GET /health 200
2026-10-04 17:51:44,990 INFO python-api GET / 200
2026-10-04 17:51:45,052 INFO python-api GET /ready 200
2026-10-04 17:51:45,422 INFO python-api GET /api/stats 200
```

## How do I troubleshoot it?

### The database is down: ready says no, health says yes

<!-- test: contains=py-lab-db -->
```bash
docker stop py-lab-db
```

<!-- test: contains=HTTP 503; contains=HTTP 200; output -->
```bash
curl -s -w '  -> HTTP %{http_code}\n' http://localhost:18000/ready
curl -s -w '  -> HTTP %{http_code}\n' http://localhost:18000/health
```

```text
{"status":"not ready","service":"python-api","reason":"failed to resolve host 'py-lab-db': [Errno -2] Name or service not known"}  -> HTTP 503
{"status":"ok","service":"python-api","version":"1.0.0"}  -> HTTP 200
```

This is exactly the split Kubernetes needs: the Pod is taken **out of the Service** (not ready) but **not restarted**
(still healthy). Restarting the API would not bring the database back.

<!-- test: contains=py-lab-db -->
```bash
docker start py-lab-db
```

<!-- test: retry=30; contains="status":"ready" -->
```bash
curl -s http://localhost:18000/ready
```

### The password is missing

<!-- test: fail; contains=DB_PASSWORD; output -->
```bash
docker run --rm --network py-lab -e DB_HOST=py-lab-db python-api:1.0.0
```

```text
python-api: FATAL: the environment variable DB_PASSWORD is not set (the database password is required)
```

The container exits immediately with status 1 and says why. In Kubernetes this shows up as `CrashLoopBackOff`, and
`kubectl logs --previous` shows this line.

### The password is wrong

<!-- test: contains=py-lab-wrong -->
```bash
docker run -d --name py-lab-wrong --network py-lab -p 18001:8000 \
  -e DB_HOST=py-lab-db -e DB_PASSWORD=not-the-password python-api:1.0.0
docker ps --filter name=py-lab-wrong --format '{{.Names}} {{.Status}}'
```

<!-- test: retry=20; contains=password authentication failed; output -->
```bash
curl -s -w '  -> HTTP %{http_code}\n' http://localhost:18001/ready
```

```text
{"status":"not ready","service":"python-api","reason":"connection failed: connection to server at \"172.19.0.2\", port 5432 failed: FATAL:  password authentication failed for user \"bookshop\""}  -> HTTP 503
```

The service starts (a password is set), but every database call fails: `/ready` answers 503 with the reason, so the Pod
never becomes ready. Read the reason, then check the Secret's value.

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · removes the lab containers and their network (the image stays).
```

<!-- test: contains=py-lab -->
```bash
docker rm -f py-lab-api py-lab-wrong py-lab-db
docker network rm py-lab
```

To also delete the image: `docker rmi python-api:1.0.0`.

## Practical challenge

**Task:** add an endpoint `GET /api/stats/books` that returns only `{"books": n}`, and ship it as version `1.1.0`.

**Requirements**

1. The new endpoint uses the existing `count()` helper (a missing table still counts as 0).
2. The image is built as `python-api:1.1.0` with `--build-arg APP_VERSION=1.1.0`; `GET /` reports version `1.1.0`.
3. Rebuilding after a code change does **not** re-run `pip install`.

**Hints:** a FastAPI route is a decorated function (`@app.get(...)`); watch the build output for `CACHED`.

**Expected result:** `curl localhost:18000/api/stats/books` → `{"books":0}`, and `/` shows `"version":"1.1.0"`.

<details>
<summary>Solution</summary>

Add to `src/main.py`:

```python
@app.get("/api/stats/books")
def stats_books():
    with connect() as conn:
        return {"books": count(conn, "books")}
```

```text
docker build --build-arg APP_VERSION=1.1.0 -t python-api:1.1.0 applications/python-api
```

The `pip install` step shows `CACHED`, because `requirements.txt` did not change and it is copied before the code.

</details>

**Explanation:** dependencies change rarely and code changes often, so the Dockerfile copies them in that order. The
version is a build argument, so one Dockerfile produces every release, and the tag tells you exactly what runs.

Next: [go-status](../go-status/README.md)
