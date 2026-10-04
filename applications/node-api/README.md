# node-api · Node.js 24 + Express 5

> The users API of the Bookshop. Time: 30 minutes. You need Docker; nothing else has to be installed.
> All commands run from the root of the repository.

## What is it?

**Node.js** is a runtime that runs JavaScript outside the browser: on a server, in a container, on your laptop.
**Express** is the most widely used web framework for Node.js: it maps URLs like `GET /api/users` to JavaScript
functions. Together they are one of the most common ways to build HTTP APIs.

Like every service in this lab, `node-api` follows the [service contract](../../docs/CONTRACT.md): it listens on
`PORT`, takes all configuration from environment variables, logs to stdout, and has `/health` and `/ready` endpoints.
That contract, not the language, is what Docker, Compose and Kubernetes care about.

## What does the application do?

| Endpoint | Answer |
|---|---|
| `GET /` | `service`, `version`, `language`, `runtime`, `description` |
| `GET /health` | `{"status":"ok"}` as soon as the process serves requests (**liveness**: no database check) |
| `GET /ready` | `{"status":"ready"}` when PostgreSQL answers, otherwise HTTP 503 (**readiness**) |
| `GET /api/users` | all users from the table `users` |
| `POST /api/users` | adds a user: `{"name": "...", "email": "..."}` → 201, or 409 if the e-mail exists |

At startup it creates the table `users` if it does not exist and adds three example users. The code is one file:
[src/server.js](src/server.js).

```text
 client ── HTTP :3000 ──► node-api (Express) ── SQL :5432 ──► postgres  (table users)
```

## How do I run it locally?

With Node.js 24 installed, the usual developer workflow is:

<!-- test: skip -->
```bash
cd applications/node-api
npm ci                                   # install the exact versions from package-lock.json
DB_HOST=localhost DB_PASSWORD=example-only npm start
```

You also need a PostgreSQL to talk to. The rest of this page does everything with Docker instead, so you do not need
Node.js or PostgreSQL on your computer; this is also the path the repository's tests run.

## How do I build the Docker image?

The [Dockerfile](Dockerfile):

```dockerfile
FROM node:24.21-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY src ./src
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    NODE_ENV=production \
    PORT=3000
USER node
EXPOSE 3000
CMD ["node", "src/server.js"]
```

| Line | Why |
|---|---|
| `FROM node:24.21-alpine` | the official Node.js image, version pinned (24 is the current LTS line); Alpine keeps it small |
| `WORKDIR /app` | all following paths are relative to `/app` |
| `COPY package.json package-lock.json ./` | **only** the dependency list first, so the next layer is cached until the dependencies change |
| `RUN npm ci --omit=dev ...` | installs exactly the versions in the lockfile, without development tools; then drops npm's cache |
| `COPY src ./src` | the code last: changing code does not re-run `npm ci` |
| `ARG` / `ENV APP_VERSION` | the version is baked into the image (and equals the image tag); `/` and `/health` report it |
| `ENV NODE_ENV=production PORT=3000` | production mode for Express; the default port (overridable) |
| `USER node` | the official image ships a non-root user `node`: the app never runs as root |
| `EXPOSE 3000` | documentation: the container listens on 3000 (publishing a port is a run-time decision) |
| `CMD [...]` | the process the container runs; exec form, so the app receives SIGTERM directly and shuts down cleanly |

The [.dockerignore](.dockerignore) keeps `node_modules` and other local files out of the build context.

Build it, with a version tag (never `latest`):

<!-- test: timeout=900; contains=naming to -->
```bash
docker build -t node-api:1.0.0 applications/node-api
```

<!-- test: contains=node-api; contains=1.0.0; output -->
```bash
docker images node-api
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE            ID             DISK USAGE   CONTENT SIZE   EXTRA
node-api:1.0.0   af5effd7a983        251MB           63MB        
```

## How do I run the container?

The API needs a database. Create a network, so the containers find each other by name, and start PostgreSQL on it:

<!-- test-run: docker rm -f lesson-node-api lesson-node-db >/dev/null 2>&1 || true; docker network rm lesson-node >/dev/null 2>&1 || true -->

<!-- test: timeout=300 -->
```bash
docker network create lesson-node
docker run -d --name lesson-node-db --network lesson-node \
  -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only \
  postgres:18.6-alpine
```

<!-- test: retry=30; contains=accepting connections -->
```bash
docker exec lesson-node-db pg_isready -U bookshop -d bookshop
```

Now the API. `DB_HOST` is the **container name** of the database: on a user-defined network Docker's DNS resolves it.
`-p 3000:3000` publishes the container port on your computer:

<!-- test: contains=lesson-node-api -->
```bash
docker run -d --name lesson-node-api --network lesson-node -p 3000:3000 \
  -e DB_HOST=lesson-node-db -e DB_PASSWORD=example-only \
  node-api:1.0.0
docker ps --filter name=lesson-node-api --format '{{.Names}} {{.Status}} {{.Ports}}'
```

<!-- test: retry=15; contains="status":"ok"; output -->
```bash
curl -s http://localhost:3000/
echo
curl -s http://localhost:3000/health
```

```text
{"service":"node-api","version":"1.0.0","language":"JavaScript","runtime":"Node.js 24.21.0","description":"Users API of the Bookshop (Express)"}
{"status":"ok","service":"node-api","version":"1.0.0"}
```

<!-- test: retry=10; contains=Grace Hopper; output -->
```bash
curl -s http://localhost:3000/api/users
```

```text
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T17:50:01.376Z"},{"id":2,"name":"Grace Hopper","email":"grace@example.com","created_at":"2026-10-04T17:50:01.381Z"},{"id":3,"name":"Linus Torvalds","email":"linus@example.com","created_at":"2026-10-04T17:50:01.384Z"}]
```

Add a user:

<!-- test: contains="id":4; output -->
```bash
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"name":"Alan Turing","email":"alan@example.com"}' http://localhost:3000/api/users
```

```text
{"id":4,"name":"Alan Turing","email":"alan@example.com","created_at":"2026-10-04T17:50:02.029Z"}
```

The logs show one line per request (to stdout, where Docker, Compose and Kubernetes collect them):

<!-- test: contains=POST /api/users 201; output -->
```bash
docker logs lesson-node-api
```

```text
2026-10-04T17:50:01.317Z node-api version 1.0.0 listening on port 3000
2026-10-04T17:50:01.387Z node-api table users ready
2026-10-04T17:50:01.628Z node-api GET / 200
2026-10-04T17:50:01.701Z node-api GET /health 200
2026-10-04T17:50:01.871Z node-api GET /api/users 200
2026-10-04T17:50:02.043Z node-api POST /api/users 201
```

### What happens without a password?

`DB_PASSWORD` has no default on purpose: a missing secret must stop the app with a clear message, not let it start
and fail later.

<!-- test: fail; contains=DB_PASSWORD is not set; output -->
```bash
docker run --rm node-api:1.0.0
```

```text
2026-10-04T17:50:03.210Z node-api ERROR: DB_PASSWORD is not set. Set it (Compose: environment, Kubernetes: a Secret) and start again.
```

The exit code is 1. In Kubernetes this shows up as a Pod in `CrashLoopBackOff`, and `kubectl logs` shows exactly
this line (see the [troubleshooting labs](../../troubleshooting/README.md)).

## How does Docker Compose run it?

In [compose/docker-compose.yml](../../compose/README.md) the same image becomes the service `node-api`: the environment
variables come from the Compose file, `DB_HOST` is simply `postgres` (the database's service name), and Compose creates
the network for you. See the [Compose lesson](../../compose/README.md).

## How does Kubernetes run it?

A **Deployment** keeps two replicas of this image running and replaces them when they fail; a **Service** named
`node-api` gives them one stable address (`http://node-api:3000`), exactly the name the other services and the Ingress
use. See the [Kubernetes lessons](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why |
|---|---|
| Deployment `node-api` | runs and replaces the Pods; rolling updates from `1.0.0` to `1.1.0` |
| Service `node-api` (ClusterIP, port 3000) | stable name and load balancing across the replicas |
| ConfigMap `bookshop-config` | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` (non-secret settings) |
| Secret `bookshop-db` | `DB_PASSWORD` |
| livenessProbe `GET /health` | restart the container if the process hangs |
| readinessProbe `GET /ready` | send traffic only while the database answers |
| resources (requests / limits) | the scheduler reserves 100m CPU / 128Mi; the limit stops a leak from eating the node |

## How do I verify it?

`/health` says the process runs, `/ready` says it can do its job, and `/api/users` proves the whole path to the
database:

<!-- test: contains="status":"ready"; output -->
```bash
curl -s http://localhost:3000/ready
```

```text
{"status":"ready","service":"node-api","version":"1.0.0"}
```

## How do I troubleshoot it?

Two failures, reproduced with the containers above.

**The database is down.** Stop PostgreSQL and ask both endpoints:

<!-- test: contains="status":"ok"; contains=503; output -->
```bash
docker stop lesson-node-db > /dev/null
curl -s -w ' HTTP %{http_code}\n' --max-time 10 http://localhost:3000/ready
curl -s -w ' HTTP %{http_code}\n' http://localhost:3000/health
```

```text
{"status":"not ready","service":"node-api","reason":"Connection terminated due to connection timeout"} HTTP 503
{"status":"ok","service":"node-api","version":"1.0.0"} HTTP 200
```

`/ready` turns 503 (the database connection times out), `/health` stays 200. That is the point of having two
endpoints: Kubernetes takes the Pod out of the Service until the database is back, but does **not** restart it,
because restarting would not fix a database outage.

<!-- test: retry=30; contains="status":"ready" -->
```bash
docker start lesson-node-db > /dev/null
curl -s http://localhost:3000/ready
```

**Duplicate data.** The table has a unique e-mail; the API answers 409 instead of crashing:

<!-- test: contains=409; output -->
```bash
curl -s -w ' HTTP %{http_code}\n' -X POST -H 'Content-Type: application/json' \
  -d '{"name":"Alan Turing","email":"alan@example.com"}' http://localhost:3000/api/users
```

```text
{"error":"email already exists"} HTTP 409
```

General order when the API misbehaves: `docker ps -a` (running? exit code?), `docker logs`, then the endpoints from the
inside (`docker exec lesson-node-api wget -qO- localhost:3000/health`).

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · removes the two containers (and the database data in them) and the network.
```

<!-- test: contains=lesson-node -->
```bash
docker rm -f lesson-node-api lesson-node-db
docker network rm lesson-node
```

The image `node-api:1.0.0` stays: Compose and Kubernetes use it next. Remove it with `docker rmi node-api:1.0.0`.

## Practical challenge

### Task

Add an endpoint `GET /api/users/count` that returns `{"count": <number of users>}`, and ship it as version `1.1.0`.

### Requirements

- The new endpoint works; all existing endpoints still work.
- The image is tagged `node-api:1.1.0` and `/health` reports version `1.1.0`.
- `node-api:1.0.0` still exists (you can always go back).

### Hints

- Express matches routes in order: define `/api/users/count` next to `/api/users`.
- `SELECT count(*)::int AS count FROM users` returns a number, not a string.
- The version is a build argument: `--build-arg APP_VERSION=1.1.0`.

### Expected result

`curl -s localhost:3000/api/users/count` → `{"count":3}` on a fresh database, and
`curl -s localhost:3000/health` → `{"status":"ok","service":"node-api","version":"1.1.0"}`.

### Solution

<details>
<summary>Show the solution</summary>

In `src/server.js`, before `app.listen(...)`:

```javascript
app.get("/api/users/count", async (req, res) => {
  try {
    await ensureSchema();
    const { rows } = await pool.query("SELECT count(*)::int AS count FROM users");
    res.json({ count: rows[0].count });
  } catch (err) {
    res.status(503).json({ error: "database unavailable", detail: err.message });
  }
});
```

Then:

```text
docker build --build-arg APP_VERSION=1.1.0 -t node-api:1.1.0 applications/node-api
```

and run it exactly as above, with `node-api:1.1.0`.

</details>

### Explanation

A new feature is a new **image**, with a new **tag**; the old image is untouched. That is what makes rolling updates
and rollbacks in Kubernetes possible later: `kubectl set image ... node-api=node-api:1.1.0`, and if something goes
wrong, back to `1.0.0` in seconds.
