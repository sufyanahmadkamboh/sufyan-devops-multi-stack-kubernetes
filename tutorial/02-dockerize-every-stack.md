# 02 · Dockerize every stack

> Goal: every application builds into an image and runs as a container, and you can explain why their Dockerfiles
> differ. Levels 3–4 of the [roadmap](../README.md#4-the-roadmap). Time: about 3 hours (the first Java and Laravel
> builds download a lot; later builds use the cache).

## Before you start

Docker is running and you are in the repository root. Nothing else is needed: each lesson starts its own test
PostgreSQL container where the application needs one, and removes it at the end.

## The walk

### 1. node-api first, in full

Open [applications/node-api/README.md](../applications/node-api/README.md) and work through all of it. It is the
most detailed of the seven: every later lesson follows the same sections. Read the Dockerfile table line by line
before you build.

Watch for the size of the result:

```text
IMAGE            ID             DISK USAGE   CONTENT SIZE   EXTRA
node-api:1.0.0   af5effd7a983        251MB           63MB
```

Docker 29 shows two numbers: what the image uses on disk, and the compressed content that is downloaded. Then watch
the readiness logic with the database stopped: `/ready` fails, `/health` does not.

```text
{"status":"not ready","service":"node-api","reason":"Connection terminated due to connection timeout"} HTTP 503
{"status":"ok","service":"node-api","version":"1.0.0"} HTTP 200
```

That one pair of lines is the whole idea of liveness vs readiness. You will see it again in Kubernetes.

### 2. The other six, in any order

Work through [python-api](../applications/python-api/README.md), [go-status](../applications/go-status/README.md),
[java-api](../applications/java-api/README.md), [laravel-admin](../applications/laravel-admin/README.md),
[frontend](../applications/frontend/README.md) and [report-worker](../applications/report-worker/README.md). For each
one, fill in a row of this table in your notebook before you move on:

| Application | Build stage? | Final base image | User | Size you measured |
|---|---|---|---|---|
| node-api | no | node:24.21-alpine | node | |
| python-api | yes (venv) | python:3.14-slim | 10001 | |
| go-status | yes (compile) | distroless static | nonroot | |
| java-api | yes (Maven) | eclipse-temurin:25-jre-alpine | 10001 | |
| laravel-fpm / laravel-web | yes (Composer) | php:8.5-fpm-alpine / nginx-unprivileged | www-data / nginx | |
| frontend | yes (Vite build) | nginx-unprivileged | nginx | |
| report-worker | no | node:24.21-alpine | node | |

Watch for these moments:

- **go-status:** the final image against the image that built it.

  ```text
  REPOSITORY:TAG                        SIZE
  go-status:1.0.0                       16.4MB
  golang:1.27-alpine                    381MB
  ```

  A Go program compiles to one static binary; the runtime image needs nothing else, not even a shell.

- **java-api:** the same idea with a JVM. The JAR still needs a Java runtime, so the gain is smaller:

  ```text
  java-api:1.0.0                        348MB
  java-api:build-stage                  677MB
  ```

  And the start time depends on how much CPU the container gets. Remember these numbers for the startupProbe:

  ```text
  cpus=0.5: Started BookshopApplication in 9.302 seconds
  cpus=1: Started BookshopApplication in 4.607 seconds
  ```

- **laravel-admin:** two images, because nginx serves files and HTTP while PHP-FPM runs PHP. Without FPM, nginx
  answers with a 502 and says exactly why:

  ```text
  connect() failed (111: Connection refused) while connecting to upstream ... upstream: "fastcgi://127.0.0.1:9000"
  ```

- **frontend:** the build stage (Node.js, 334 MB) produces static files; the image you ship is nginx with those
  files (81.8 MB). The browser runs the React code, not the container.

- **Missing configuration, every stack:** each application refuses to start without its password, with a clear
  message and exit code 1. For example:

  ```text
  FATAL java-api: environment variable DB_PASSWORD is not set; refusing to start
  ```

### 3. Read docs/03 and docs/04

[docs/03](../docs/03-dockerfiles-across-stacks.md) puts your table next to the real one and explains the patterns
(interpreted vs compiled vs static web, multi-stage, dependency-layer caching). [docs/04](../docs/04-images-tags-and-registries.md)
explains the image names and tags you have been typing, and why `latest` never appears in this course.

## Expert commentary

- **Fail fast at startup.** A container that exits at once with "DB_PASSWORD is not set" is fixed in a minute. One
  that starts and answers every request with "500" costs an afternoon. Every application here was built that way on
  purpose; ask for it in code reviews.
- **Dependency layers first.** Copying `package-lock.json`, `requirements.txt`, `go.mod`, `pom.xml` or
  `composer.lock` before the source code means a code change rebuilds in seconds. Watch your second Java build use the
  cache.
- **Small is not the only goal.** Distroless (go-status) has no shell, which is great for security and a small
  surprise when you try to debug it. Chapter 05 shows `kubectl exec` failing on it.
- **Interview angle:** "Why are your images so different in size?" Explain runtime vs build toolchain, and that the
  size of the runtime the language needs (none for Go, a JVM for Java, an interpreter for Python and PHP) sets the
  floor.

## Checkpoint

- [ ] All seven lessons pass on your machine, and `docker images` lists all eight images with tag `1.0.0`.
- [ ] Your table has a real size in every row.
- [ ] You can explain, for each stack, what the build stage (if any) produces and what the final image contains.
- [ ] You triggered the missing-password failure in at least two stacks and read the message.

Next: [03 · Docker Compose](03-docker-compose.md)
