# java-api · Java 25 + Spring Boot 4

> The **books** service of the Bookshop. Time: about 30 minutes. Every command below was run, from the repository
> root, and the output under it is the real output.

## What is it?

**Java** is a compiled, statically typed language. Java source code is compiled to *bytecode* (`.class` files) that
runs on the **JVM** (Java Virtual Machine), not directly on the CPU. So a Java application needs two different things
at two different times:

| When | What you need | In this lab |
|---|---|---|
| **build time** | a **JDK** (compiler + tools) and **Maven** (downloads libraries, compiles, packages) | the `maven:3.9-eclipse-temurin-25-alpine` image |
| **run time** | only a **JRE** (the JVM) and the packaged application | the `eclipse-temurin:25-jre-alpine` image |

**Spring Boot** is the most widely used Java framework for web services. It packages the application, all its
libraries and an embedded web server (Tomcat) into **one executable JAR file**: `java -jar app.jar` is all it needs.
That single file is what makes Java applications easy to put into a container.

## What does the application do?

A small REST API for books, stored in PostgreSQL. It follows the lab's [service contract](../../docs/CONTRACT.md):

| Endpoint | Answer |
|---|---|
| `GET /` | name, version, language and runtime of the service |
| `GET /health` | `{"status":"ok",...}`: the process can serve requests (does **not** touch the database) |
| `GET /ready` | `{"status":"ready",...}` when PostgreSQL answers, otherwise HTTP **503** `{"status":"not ready","reason":...}` |
| `GET /api/books` | all books |
| `GET /api/books/{id}` | one book, or HTTP **404** `{"error":"book not found"}` |

| File | What it does |
|---|---|
| [pom.xml](pom.xml) | the Maven project: Spring Boot 4.1.1, Java 25, three dependencies (web, JDBC, PostgreSQL driver) |
| [BookshopApplication.java](src/main/java/lab/bookshop/BookshopApplication.java) | `main()`: refuses to start without `DB_PASSWORD` |
| [BookController.java](src/main/java/lab/bookshop/BookController.java) | the endpoints |
| [SchemaInitializer.java](src/main/java/lab/bookshop/SchemaInitializer.java) | creates the `books` table and 5 sample books ([schema.sql](src/main/resources/schema.sql), [data.sql](src/main/resources/data.sql)); retries on the next request if the database was not reachable at startup |
| [RequestLogFilter.java](src/main/java/lab/bookshop/RequestLogFilter.java) | one log line per request, to stdout |
| [application.properties](src/main/resources/application.properties) | all settings, taken from environment variables |

All configuration comes from **environment variables**: `PORT` (8080), `DB_HOST` (`postgres`), `DB_PORT` (5432),
`DB_NAME` (`bookshop`), `DB_USER` (`bookshop`) and `DB_PASSWORD` (required, no default).

Two design decisions matter later, in Kubernetes:

- **The API starts even when the database is down.** The connection pool is told not to fail at startup
  (`initialization-fail-timeout=-1`); `/health` answers, `/ready` says 503, and the table is created on the first
  request that reaches the database. Starting order no longer matters.
- **A missing password stops it immediately**, with one clear log line and exit code 1. A configuration error should
  be loud, not hidden behind failing requests.

## How do I run it locally?

With **JDK 25** installed, the Maven Wrapper (`mvnw`, in this folder) downloads the right Maven version by itself:

<!-- test: skip -->
```bash
cd applications/java-api
DB_HOST=localhost DB_PASSWORD=example-only ./mvnw spring-boot:run
```

This needs a PostgreSQL on `localhost:5432`. You do not need Java or Maven on your computer for this lab: the tested
path below builds and runs everything in containers.

## How do I build the Docker image?

The [Dockerfile](Dockerfile) has **two stages**:

| Line | Why |
|---|---|
| `FROM maven:3.9-eclipse-temurin-25-alpine AS build` | stage 1: Maven + a full JDK 25, only for building |
| `COPY pom.xml .` then `RUN mvn -B -q dependency:go-offline` | download all libraries **before** copying the code: this layer comes from the cache as long as `pom.xml` is unchanged, so a code change does not download everything again |
| `COPY src ./src` then `RUN mvn -B -q package -DskipTests` | compile and package `target/app.jar` (the `finalName` in `pom.xml`) |
| `FROM eclipse-temurin:25-jre-alpine` | stage 2 starts **from scratch** with only a Java runtime: no Maven, no compiler, no source code |
| `ARG APP_VERSION=1.0.0` / `ENV APP_VERSION=...` | the version, shown by `/` and `/health`; the image tag is the same number |
| `RUN addgroup ... adduser -u 10001 ...` / `USER 10001` | run as an unprivileged user with a fixed numeric ID |
| `COPY --from=build /src/target/app.jar app.jar` | the **only** thing taken from stage 1 |
| `ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]` | size the Java heap from the **container's** memory limit (75 %), not from the host's memory |

Build it (the first build downloads the build image and all libraries; on the computer where this lesson was
recorded it took about two minutes):

<!-- test: timeout=1800; contains=java-api:1.0.0 -->
```bash
docker build -t java-api:1.0.0 applications/java-api
docker image ls java-api:1.0.0
```

Why two stages? Build only stage 1 and compare:

<!-- test: timeout=1800; contains=java-api; output -->
```bash
docker build -q --target build -t java-api:build-stage applications/java-api > /dev/null
docker image ls --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E 'REPOSITORY|java-api'
```

```text
REPOSITORY:TAG                        SIZE
java-api:1.0.0                        348MB
java-api:build-stage                  677MB
```

The build stage carries the JDK, Maven, the source and the whole Maven cache; the final image carries a JRE and one
JAR. On the computer where this lesson was recorded (Docker Desktop 29, containerd image store) the build stage used
677 MB on disk (221 MB compressed) and the final image 348 MB (96 MB compressed). Smaller images download faster to
every Kubernetes node and contain fewer packages that could have vulnerabilities.

<!-- test-run: docker image rm java-api:build-stage > /dev/null -->

What is inside the final image? The JAR, owned by root (read-only for the app), and the app runs as user 10001:

<!-- test: contains=app.jar; contains=uid=10001; output -->
```bash
docker run --rm --entrypoint sh java-api:1.0.0 -c 'ls -l /app && id'
```

```text
total 22072
-rw-r--r-- 1 root root 22600356 Oct  4 17:55 app.jar
uid=10001(app) gid=10001(app) groups=10001(app)
```

## How do I run the container?

The API needs PostgreSQL. Put both on a user-defined network, so the API can reach the database by its **container
name**:

<!-- test: contains=java-lab-db -->
```bash
docker network create java-lab
docker run -d --name java-lab-db --network java-lab \
  -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only \
  postgres:18.6-alpine
docker ps --filter name=java-lab-db --format '{{.Names}} {{.Status}}'
```

<!-- test-run: for i in $(seq 60); do docker exec java-lab-db pg_isready -U bookshop -d bookshop -q && exit 0; sleep 1; done; exit 1 -->

Then the API. `-e DB_HOST=java-lab-db` tells it where the database is; `-p 8084:8080` publishes container port 8080 on
port 8084 of your computer:

<!-- test: contains=java-lab-api -->
```bash
docker run -d --name java-lab-api --network java-lab -p 8084:8080 \
  -e DB_HOST=java-lab-db -e DB_PASSWORD=example-only \
  java-api:1.0.0
docker ps --filter name=java-lab-api --format '{{.Names}} {{.Status}} {{.Ports}}'
```

A JVM application is not ready the moment the container starts. Wait for `/health`, then look at the log:

<!-- test: retry=60; contains=Started BookshopApplication; output -->
```bash
curl -sf http://localhost:8084/health > /dev/null
docker logs java-lab-api 2>&1 | grep -E 'Starting|Started|Tomcat started|books table'
```

```text
2026-10-04T17:56:00.794Z INFO  BookshopApplication - Starting BookshopApplication v1.0.0 using Java 25.0.4.1 with PID 1 (/app/app.jar started by app in /app)
2026-10-04T17:56:02.803Z INFO  TomcatWebServer - Tomcat started on port 8080 (http) with context path '/'
2026-10-04T17:56:02.818Z INFO  BookshopApplication - Started BookshopApplication in 2.607 seconds (process running for 3.296)
2026-10-04T17:56:02.825Z INFO  HikariDataSource - HikariPool-1 - Starting...
2026-10-04T17:56:03.055Z INFO  SchemaInitializer - books table ready
```

`Started BookshopApplication in ... seconds`: the JVM starts, Spring wires the application together, Tomcat opens
the port. A few seconds with all CPUs of a laptop, as you see; **much longer** with the small CPU limits containers
usually get in Kubernetes (measured below).

## How does Docker Compose run it?

In [compose/docker-compose.yml](../../compose/README.md) the service `java-api` is this same image with the same
environment variables, on the same network as `postgres`. Compose replaces the `docker network create` and
`docker run` commands above with one file. See the [Compose lesson](../../compose/README.md).

## How does Kubernetes run it?

A **Deployment** keeps the wanted number of `java-api` Pods running from the image `java-api:1.0.0`; a **Service**
named `java-api` gives them one stable address and DNS name inside the cluster. The database settings come from a
**ConfigMap**, the password from a **Secret**. See the [Kubernetes lessons](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why java-api needs it |
|---|---|
| **Deployment** | runs and replaces the Pods; rolling updates from `1.0.0` to a new tag |
| **Service** (ClusterIP, port 8080) | a stable name, `java-api`, for the frontend and the Ingress |
| **ConfigMap** | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` (not secret) |
| **Secret** | `DB_PASSWORD` |
| **startupProbe** on `/health` | the JVM starts slowly; without it, a liveness probe could kill the container before it has even started |
| **livenessProbe** on `/health` | restart the container if the process hangs |
| **readinessProbe** on `/ready` | send traffic only when the database answers |
| **resources**: memory request/limit | the heap is 75 % of the limit (`MaxRAMPercentage`), so the limit directly sizes the JVM |

How slow is "slow"? Start the same image with the CPU limits a Pod typically gets, and read Spring's own startup time:

<!-- test: timeout=300; contains=Started BookshopApplication; output -->
```bash
for cpus in 0.5 1; do
  docker run -d --name java-lab-cpu --network java-lab --cpus=$cpus --memory=512m \
    -e DB_HOST=java-lab-db -e DB_PASSWORD=example-only java-api:1.0.0 > /dev/null
  until docker logs java-lab-cpu 2>&1 | grep -q 'Started BookshopApplication'; do sleep 1; done
  echo "cpus=$cpus: $(docker logs java-lab-cpu 2>&1 | grep -o 'Started BookshopApplication in [0-9.]* seconds')"
  docker rm -f java-lab-cpu > /dev/null
done
```

```text
cpus=0.5: Started BookshopApplication in 9.302 seconds
cpus=1: Started BookshopApplication in 4.607 seconds
```

With half a CPU, startup takes several times longer than with a whole laptop. A liveness probe that starts checking
after 5 seconds and restarts after 3 failures would kill this container in a loop. The **startupProbe** gives it time
to start; only when the startupProbe has succeeded do the liveness and readiness probes take over.

## How do I verify it?

Every endpoint, with the HTTP status code at the end:

<!-- test: contains=java-api; contains=[200]; output -->
```bash
curl -s -w ' [%{http_code}]\n' http://localhost:8084/
curl -s -w ' [%{http_code}]\n' http://localhost:8084/health
curl -s -w ' [%{http_code}]\n' http://localhost:8084/ready
```

```text
{"service":"java-api","version":"1.0.0","language":"Java 25","runtime":"Spring Boot 4 on the JVM","description":"Books API of the Bookshop: GET /api/books, GET /api/books/{id}"} [200]
{"status":"ok","service":"java-api","version":"1.0.0"} [200]
{"status":"ready","service":"java-api","version":"1.0.0"} [200]
```

<!-- test: contains=Moby-Dick; contains=book not found; output -->
```bash
curl -s -w ' [%{http_code}]\n' http://localhost:8084/api/books
curl -s -w ' [%{http_code}]\n' http://localhost:8084/api/books/2
curl -s -w ' [%{http_code}]\n' http://localhost:8084/api/books/99
```

```text
[{"id":1,"title":"Pride and Prejudice","author":"Jane Austen","year":1813},{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851},{"id":3,"title":"Crime and Punishment","author":"Fyodor Dostoevsky","year":1866},{"id":4,"title":"The Adventures of Sherlock Holmes","author":"Arthur Conan Doyle","year":1892},{"id":5,"title":"The Time Machine","author":"H. G. Wells","year":1895}] [200]
{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851} [200]
{"error":"book not found","id":99} [404]
```

And the request log, one line per request, on stdout (which is where `docker logs` and `kubectl logs` read it):

<!-- test: contains=GET /api/books; output -->
```bash
docker logs java-lab-api 2>&1 | grep ' request - ' | tail -4
```

```text
2026-10-04T17:56:25.187Z INFO  request - GET /ready 200 12ms
2026-10-04T17:56:25.331Z INFO  request - GET /api/books 200 28ms
2026-10-04T17:56:25.394Z INFO  request - GET /api/books/2 200 22ms
2026-10-04T17:56:25.441Z INFO  request - GET /api/books/99 404 3ms
```

## How do I troubleshoot it?

### The container exits immediately

<!-- test: fail; contains=DB_PASSWORD; output -->
```bash
docker run --rm --network java-lab -e DB_HOST=java-lab-db java-api:1.0.0
```

```text
FATAL java-api: environment variable DB_PASSWORD is not set; refusing to start
```

Exit code 1 and one line that names the problem. In Kubernetes this shows up as `CrashLoopBackOff`, and
`kubectl logs --previous` shows the same line: the Secret with the password is missing or not referenced.

### The database is down

Stop PostgreSQL and ask again:

<!-- test: contains=not ready; contains=[503]; output -->
```bash
docker stop java-lab-db > /dev/null
curl -s -w ' [%{http_code}]\n' http://localhost:8084/health
curl -s -w ' [%{http_code}]\n' http://localhost:8084/ready
curl -s -w ' [%{http_code}]\n' http://localhost:8084/api/books
```

```text
{"status":"ok","service":"java-api","version":"1.0.0"} [200]
{"status":"not ready","service":"java-api","reason":"PSQLException: This connection has been closed."} [503]
{"error":"database unavailable","reason":"PSQLException: This connection has been closed."} [503]
```

`/health` still says ok: the process is fine, restarting it would not help. `/ready` and the API say 503 with the
reason. In Kubernetes, the readiness probe takes the Pod out of the Service until the database is back; nobody
restarts anything. Start the database again, and the API recovers by itself:

<!-- test: retry=30; contains="status":"ready"; output -->
```bash
docker start java-lab-db > /dev/null
sleep 3
curl -s -w ' [%{http_code}]\n' http://localhost:8084/ready
```

```text
{"status":"ready","service":"java-api","version":"1.0.0"} [200]
```

### Wrong database host name

<!-- test: timeout=180; contains=not ready; contains=postgress; output -->
```bash
docker run -d --name java-lab-wronghost --network java-lab -p 8085:8080   -e DB_HOST=postgress -e DB_PASSWORD=example-only java-api:1.0.0 > /dev/null
until curl -sf http://localhost:8085/health > /dev/null; do sleep 1; done
curl -s -w ' [%{http_code}]
' http://localhost:8085/ready
docker rm -f java-lab-wronghost > /dev/null
```

```text
{"status":"not ready","service":"java-api","reason":"UnknownHostException: postgress"} [503]
```

A typo in `DB_HOST` (`postgress`): the API runs, but readiness reports exactly what is wrong, a host name that does
not resolve. The same mistake in a Kubernetes ConfigMap gives Pods that run but never become ready: `kubectl describe
pod` shows `Readiness probe failed: HTTP probe failed with statuscode: 503`, and `curl .../ready` from inside the
cluster shows the reason.

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · deletes the two containers and the network (the database's data is lost).
```

<!-- test: contains=java-lab -->
```bash
docker rm -f java-lab-api java-lab-db
docker network rm java-lab
```

The image `java-api:1.0.0` stays: Compose and Kubernetes use it next. `docker image rm java-api:1.0.0` deletes it.

## Practical challenge

### Task

Ship version **1.1.0** of the API without changing a single line of Java code, and prove which container runs which
version.

### Requirements

- An image `java-api:1.1.0` next to `java-api:1.0.0`.
- Both running at the same time (no database needed for this check).
- `/health` of each shows its own version.

### Hints

- Look at the `ARG` in the Dockerfile; `docker build --help | grep build-arg`.
- Without `DB_PASSWORD` the app refuses to start. Any value works for this check.

### Expected result

`"version":"1.0.0"` from one container and `"version":"1.1.0"` from the other.

### Solution

<details>
<summary>Try it yourself first. Then open the solution.</summary>

<!-- test: timeout=600; contains="version":"1.1.0"; contains="version":"1.0.0"; output -->
```bash
docker build -q --build-arg APP_VERSION=1.1.0 -t java-api:1.1.0 applications/java-api > /dev/null
docker run -d --name java-v1 -p 8091:8080 -e DB_PASSWORD=x java-api:1.0.0 > /dev/null
docker run -d --name java-v2 -p 8092:8080 -e DB_PASSWORD=x java-api:1.1.0 > /dev/null
until curl -sf http://localhost:8091/health > /dev/null && curl -sf http://localhost:8092/health > /dev/null; do sleep 1; done
curl -s http://localhost:8091/health; echo
curl -s http://localhost:8092/health; echo
docker rm -f java-v1 java-v2 > /dev/null
```

```text
{"status":"ok","service":"java-api","version":"1.0.0"}
{"status":"ok","service":"java-api","version":"1.1.0"}
```

</details>

### Explanation

The version is a **build argument** baked into the image as an environment variable, and the tag repeats it. The code
did not change, the build did: the cached layers were reused, only the layers after the `ARG` were rebuilt. One image
per version, with an immutable tag, is what lets Kubernetes roll forward to `1.1.0` and back to `1.0.0` later.

<!-- test-run: docker image rm java-api:1.1.0 > /dev/null -->
