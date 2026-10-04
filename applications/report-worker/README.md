# report-worker · plain JavaScript on Node.js 24

> The Bookshop's report job. Time: 25 minutes. You need Docker; nothing else has to be installed.
> All commands run from the root of the repository.

## What is it?

**JavaScript is the programming language. Node.js is a runtime**: the program that runs JavaScript outside the browser.
So "JavaScript" and "Node.js" are not two different technologies to compare; every Node.js application *is* JavaScript.
This lab has two of them on purpose, because they show two different **kinds of workload**:

| | [node-api](../node-api/README.md) | report-worker (this one) |
|---|---|---|
| Language / runtime | JavaScript / Node.js 24 | JavaScript / Node.js 24 |
| Framework | Express (a web framework) | none: plain JavaScript and the `pg` database driver |
| Kind of program | a **server**: starts and keeps running, answers requests | a **batch job**: starts, does one task, **exits** |
| Port | 3000 | none |
| In Kubernetes | Deployment + Service | **Job** (run once) and **CronJob** (run on a schedule) |

The second row is the important one for Kubernetes: a Deployment expects its containers to run forever and restarts
any that exit. A job that exits after its work is done needs a different resource.

## What does the application do?

One run:

```text
 report-worker ── GET /api/stats  ──► python-api   (users, books, reviews)
               ── GET /api/status ──► go-status    (how many services are up)
               ── INSERT ─────────► postgres      (table reports)
               └─ prints a one-line summary, exits 0
```

It creates the table `reports` if it does not exist. It exits with code **1** and a clear message if `DB_PASSWORD` is
missing or one of the two calls fails, so a scheduler (Kubernetes) can see that the run failed and retry it. Both URLs
come from the environment (`STATS_URL`, `STATUS_URL`); the defaults are the Compose and Kubernetes service names. The
code: [src/worker.js](src/worker.js). It uses `fetch`, which is built into Node.js, so its only dependency is `pg`.

## How do I run it locally?

With Node.js 24 installed, and python-api, go-status and PostgreSQL reachable:

<!-- test: skip -->
```bash
cd applications/report-worker
npm ci
DB_HOST=localhost DB_PASSWORD=example-only \
  STATS_URL=http://localhost:8000/api/stats STATUS_URL=http://localhost:8080/api/status npm start
```

The rest of this page does everything with Docker (the tested path), and replaces the two APIs with a tiny stand-in,
so this lesson works on its own. With Compose and Kubernetes the worker talks to the real services.

## How do I build the Docker image?

The [Dockerfile](Dockerfile) is the node-api one without a port:

```dockerfile
FROM node:24.21-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY src ./src
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    NODE_ENV=production
USER node
CMD ["node", "src/worker.js"]
```

| Line | Why |
|---|---|
| `FROM node:24.21-alpine` | the same pinned runtime as node-api: same language, same runtime, same base image |
| `COPY package*.json` then `RUN npm ci --omit=dev` | dependencies in their own cached layer; only `pg`, no development tools |
| `COPY src ./src` | the code, last |
| `ARG` / `ENV APP_VERSION` | the version, printed in the first log line |
| `USER node` | non-root |
| no `EXPOSE` | nothing listens: a job does not receive requests |
| `CMD ["node", "src/worker.js"]` | runs once; when `worker.js` finishes, the container stops with its exit code |

<!-- test: timeout=900; contains=naming to -->
```bash
docker build -t report-worker:1.0.0 applications/report-worker
```

<!-- test: contains=report-worker; output -->
```bash
docker images report-worker
```

```text
WARNING: This output is designed for human readability. For machine-readable output, please use --format.
IMAGE                 ID             DISK USAGE   CONTENT SIZE   EXTRA
report-worker:1.0.0   0c4520430f03        246MB         62.3MB        
```

## How do I run the container?

The worker needs a database and the two APIs. Start PostgreSQL, and a stand-in for the APIs: a busybox web server
that serves two fixed JSON answers under the same paths:

<!-- test-run: docker rm -f lesson-worker-db lesson-worker-apis >/dev/null 2>&1 || true; docker network rm lesson-worker >/dev/null 2>&1 || true -->

<!-- test: timeout=300 -->
```bash
docker network create lesson-worker
docker run -d --name lesson-worker-db --network lesson-worker \
  -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only \
  postgres:18.6-alpine
docker run -d --name lesson-worker-apis --network lesson-worker busybox:1.37 sh -c '
  mkdir -p /www/api
  echo "{\"users\":4,\"books\":5,\"reviews\":2,\"latest_report\":null}" > /www/api/stats
  echo "{\"services\":[],\"up\":6,\"total\":6}" > /www/api/status
  httpd -f -p 8000 -h /www'
```

<!-- test: retry=30; contains=accepting connections -->
```bash
docker exec lesson-worker-db pg_isready -U bookshop -d bookshop
```

Run the job. No `-d`: it runs in the foreground, prints its summary and ends; `--rm` removes the stopped container:

<!-- test: contains=report #1 saved; output -->
```bash
docker run --rm --network lesson-worker \
  -e DB_HOST=lesson-worker-db -e DB_PASSWORD=example-only \
  -e STATS_URL=http://lesson-worker-apis:8000/api/stats \
  -e STATUS_URL=http://lesson-worker-apis:8000/api/status \
  report-worker:1.0.0
echo "exit code: $?"
```

```text
2026-10-04T17:51:00.463Z report-worker version 1.0.0 starting: stats from http://lesson-worker-apis:8000/api/stats, status from http://lesson-worker-apis:8000/api/status
2026-10-04T17:51:00.589Z report-worker report #1 saved: users=4 books=5 reviews=2 services up=6/6
exit code: 0
```

Run it again: every run adds one row. That is what a CronJob will do on a schedule.

<!-- test: contains=report #2 saved -->
```bash
docker run --rm --network lesson-worker \
  -e DB_HOST=lesson-worker-db -e DB_PASSWORD=example-only \
  -e STATS_URL=http://lesson-worker-apis:8000/api/stats \
  -e STATUS_URL=http://lesson-worker-apis:8000/api/status \
  report-worker:1.0.0
```

<!-- test: contains=(2 rows); output -->
```bash
docker exec lesson-worker-db psql -U bookshop -d bookshop -c 'SELECT id, users, books, reviews, services_up, services_total FROM reports'
```

```text
 id | users | books | reviews | services_up | services_total 
----+-------+-------+---------+-------------+----------------
  1 |     4 |     5 |       2 |           6 |              6
  2 |     4 |     5 |       2 |           6 |              6
(2 rows)
```

## How does Docker Compose run it?

In [the Compose file](../../compose/README.md) the worker is a service in a **profile** (`tools`), so
`docker compose up` does not start it with the long-running services; you run it on demand with
`docker compose run --rm report-worker`, and it talks to the real `python-api` and `go-status`. See the
[Compose lesson](../../compose/README.md).

## How does Kubernetes run it?

Not with a Deployment: a Deployment would restart the container every time it exits, forever. Kubernetes has two
resources for this kind of work: a **Job** runs it to completion once (and retries it if it fails), a **CronJob**
creates such a Job on a schedule. See the [Kubernetes lessons](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why |
|---|---|
| CronJob `report-worker` | creates a Job on a schedule (in the lab: every 5 minutes) |
| Job (created by the CronJob, or by hand with `kubectl create job --from=cronjob/report-worker`) | runs the Pod to completion; `backoffLimit` retries a failed run |
| `restartPolicy: OnFailure` / `Never` | a job's Pod must not be restarted forever like a Deployment's |
| ConfigMap `bookshop-config` + Secret `bookshop-db` | the same database settings as the APIs |
| no Service, no probes | nothing connects to the worker; success is its **exit code** |

## How do I verify it?

A batch job is verified by its **exit code** and its **result**, not by a health endpoint: exit code 0, the summary
line in its log, and a new row in `reports` (see the outputs above). In Kubernetes: `kubectl get jobs` shows
`COMPLETIONS 1/1`, and `kubectl logs job/<name>` the summary.

## How do I troubleshoot it?

**A dependency is missing.** Run the worker with its default URLs: on this network there is no `python-api` and no
`go-status`, exactly what happens when the job starts before the services exist:

<!-- test: fail; contains=ENOTFOUND; output -->
```bash
docker run --rm --network lesson-worker \
  -e DB_HOST=lesson-worker-db -e DB_PASSWORD=example-only \
  report-worker:1.0.0
```

```text
2026-10-04T17:51:03.215Z report-worker version 1.0.0 starting: stats from http://python-api:8000/api/stats, status from http://go-status:8080/api/status
2026-10-04T17:51:07.247Z report-worker ERROR: GET http://python-api:8000/api/stats failed: ENOTFOUND: getaddrinfo ENOTFOUND python-api
```

`ENOTFOUND` means a **DNS** failure: the name does not exist on this network. Exit code 1: Kubernetes would mark the
Job's Pod as failed and retry it (up to `backoffLimit`).

**The secret is missing.**

<!-- test: fail; contains=DB_PASSWORD is not set; output -->
```bash
docker run --rm report-worker:1.0.0
```

```text
2026-10-04T17:51:10.403Z report-worker ERROR: DB_PASSWORD is not set. Set it (Compose: environment, Kubernetes: a Secret) and run again.
```

When a job fails: read its log first (`docker logs`, `kubectl logs job/<name>`), then check the names and secrets it
depends on.

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · removes the database container (and the reports in it), the stand-in and the network.
```

<!-- test: contains=lesson-worker -->
```bash
docker rm -f lesson-worker-db lesson-worker-apis
docker network rm lesson-worker
```

The worker's own containers are already gone (`--rm`). The image `report-worker:1.0.0` stays for Compose and
Kubernetes.

## Practical challenge

### Task

Make the worker print how long the run took, in milliseconds, at the end of its summary line, as version `1.1.0`.

### Requirements

- The summary ends with `in <n> ms`.
- A failed run still exits with code 1.
- The image is tagged `report-worker:1.1.0`.

### Hints

- `const started = Date.now();` at the beginning of `main()`; `Date.now() - started` at the end.
- No new dependency is needed: this is plain JavaScript.

### Expected result

`... report #3 saved: users=4 books=5 reviews=2 services up=6/6 in 41 ms` (your number will differ).

### Solution

<details>
<summary>Show the solution</summary>

In `src/worker.js`, first line of `main()`:

```javascript
  const started = Date.now();
```

and in the summary log line, append `` ` in ${Date.now() - started} ms` ``. Then:

```text
docker build --build-arg APP_VERSION=1.1.0 -t report-worker:1.1.0 applications/report-worker
```

</details>

### Explanation

Everything that changes the behaviour of a container goes through a new image with a new tag. A CronJob in Kubernetes
would then point at `report-worker:1.1.0`; its next scheduled run uses the new version, and the next one after a
rollback uses the old one again.
