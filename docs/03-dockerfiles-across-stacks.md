# 03 · Dockerfiles across stacks

> Time: 25 minutes

Seven applications, eight Dockerfiles (Laravel has two images). Put them side by side and the same handful of
patterns appears in every one, whatever the language.

## The eight images at a glance

Sizes are the "disk usage" of `docker images` on the machine that recorded this lab (Docker Desktop 29); the
application READMEs show the full output.

| Image | Base of the final image | Build stage? | Runs as | Final size | Build stage size |
|---|---|---|---|---|---|
| `node-api:1.0.0` | `node:24.21-alpine` | no | `node` (uid 1000) | 251 MB | – |
| `report-worker:1.0.0` | `node:24.21-alpine` | no | `node` (uid 1000) | 246 MB | – |
| `python-api:1.0.0` | `python:3.14-slim` | yes: `pip install` into a venv | uid 10001 | 261 MB | – |
| `go-status:1.0.0` | `gcr.io/distroless/static-debian12:nonroot` | yes: `go build` | `nonroot` (uid 65532) | **16.4 MB** | 381 MB (`golang:1.27-alpine`) |
| `java-api:1.0.0` | `eclipse-temurin:25-jre-alpine` | yes: Maven builds the JAR | uid 10001 | 348 MB | 677 MB |
| `frontend:1.0.0` | `nginxinc/nginx-unprivileged:1.30.5-alpine` | yes: `npm run build` | `nginx` (uid 101) | 81.8 MB | 334 MB |
| `laravel-fpm:1.0.0` | `php:8.5-fpm-alpine` | yes: `composer install` | `www-data` (uid 82) | 222 MB | – |
| `laravel-web:1.0.0` | `nginxinc/nginx-unprivileged:1.30-alpine` | no | `nginx` (uid 101) | 81.5 MB | – |

Startup time matters for Kubernetes too. Only `java-api`'s was measured in detail (Spring's own log line, see
[java-api/README.md](../applications/java-api/README.md)): 2.6 s with every CPU of a laptop, 4.6 s limited to one
CPU, 9.3 s limited to half a CPU. That number is why only `java-api` has a startup probe ([08](08-health-probes.md)).

## Three families

```text
 INTERPRETED: the image contains the runtime + your source code + dependencies
   node-api, report-worker (Node.js)   python-api (Python)   laravel-fpm (PHP)
   source ──► [runtime image + dependencies] ──► the runtime reads the source at start

 COMPILED: a build turns source into something else; the final image only needs what runs it
   go-status (Go):    source ──► go build ──► ONE static binary ──► [distroless: binary only]
   java-api (Java):   source ──► Maven    ──► app.jar (bytecode) ──► [JRE + app.jar]

 STATIC WEB: a build turns source into files that the BROWSER runs
   frontend (React):  source ──► npm run build ──► dist/ (HTML, JS, CSS) ──► [nginx + dist/]
```

| Family | What must be in the final image | What must NOT be |
|---|---|---|
| interpreted | the runtime, production dependencies, your code | development dependencies, test tools, caches |
| compiled | the binary (Go) or the JRE + JAR (Java) | the compiler, Maven, the source code |
| static web | a web server and the built files | Node.js, `node_modules`, the source code |

## Multi-stage builds

A multi-stage Dockerfile has several `FROM` lines. Each stage starts from a clean base; only what you explicitly
`COPY --from=` an earlier stage reaches the final image. The Go Dockerfile is the clearest example
([go-status/Dockerfile](../applications/go-status/Dockerfile)):

```dockerfile
FROM golang:1.27-alpine AS build            # 381 MB: the whole Go toolchain
...
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags "-s -w -X main.version=${APP_VERSION}" -o /out/go-status .

FROM gcr.io/distroless/static-debian12:nonroot   # no shell, no package manager, no libc
COPY --from=build /out/go-status /go-status      # ← the only thing that crosses over
USER nonroot:nonroot
ENTRYPOINT ["/go-status"]
```

Which images use it and what they leave behind:

| Image | Left behind in the build stage |
|---|---|
| `go-status` | the Go compiler and standard library sources |
| `java-api` | Maven, the full JDK, the downloaded dependency cache, the source code |
| `frontend` | Node.js, `node_modules`, the React and Vite sources |
| `python-api` | nothing large: the venv is copied over (the stage keeps the final image free of build leftovers) |
| `laravel-fpm` | Composer and its download cache |

`node-api` and `report-worker` have no build step, so one stage is enough: `npm ci --omit=dev` installs only what
runs in production.

## Why Go's image is 16 MB and Java's is 348 MB

| | `go-status` | `java-api` |
|---|---|---|
| What runs | one statically linked binary (`CGO_ENABLED=0`) | `java -jar app.jar` |
| What it needs at run time | the Linux kernel. Nothing else | a Java runtime (JRE): the JVM, its class library, its native libraries |
| Final base | distroless "static": certificates, a non-root user, timezone data | `eclipse-temurin:25-jre-alpine` |
| Final size | 16.4 MB | 348 MB |

The Go compiler resolves everything at build time, so the result can run on an almost empty image. Java compiles to
bytecode, which needs the JVM at run time; the JRE alone is most of the 348 MB. Neither is "better": the JVM buys
you a mature ecosystem and runtime optimisation, Go buys you a tiny, fast-starting image. What matters for operations
is that both final images contain **only what runs**, not the tools that built them.

## Dependency layers and the build cache

Docker reuses a layer from its cache as long as the instruction and its inputs have not changed. Every Dockerfile
here copies **the dependency description first**, installs, and only then copies the source code:

| Stack | Copied first | Install step | Cached until... |
|---|---|---|---|
| Node.js | `package.json`, `package-lock.json` | `npm ci --omit=dev` | the lock file changes |
| Python | `requirements.txt` | `pip install -r requirements.txt` | the requirements change |
| Go | `go.mod` | `go mod download` | the module file changes |
| Java | `pom.xml` | `mvn dependency:go-offline` | the POM changes |
| PHP | `composer.json`, `composer.lock` | `composer install --no-dev` | the lock file changes |
| React | `package.json`, `package-lock.json` | `npm ci` | the lock file changes |

Change one line of application code, rebuild, and only the layers after `COPY src ...` run again. The slow part
(downloading dependencies) is skipped; you see `CACHED` next to it in the build output. For `java-api`, whose Maven
dependency download is the longest step of any image here, this turns a long first build into a short rebuild.

## .dockerignore

`docker build` sends a folder (the build context) to the builder. `.dockerignore` keeps things out of it, for speed
and for safety:

| Image | Ignores, for example |
|---|---|
| `node-api`, `report-worker`, `frontend` | `node_modules` (installed inside the build), `.env` |
| `python-api` | `__pycache__/`, `.venv/` |
| `java-api` | `target/` (build output), IDE folders |
| `laravel-admin` | `src/vendor`, `src/.env`, `src/.env.*` (but not `.env.example`), logs and caches |

A local `node_modules` or `vendor` folder would overwrite the clean install inside the image; a local `.env` would put
your secrets into it.

## Non-root users

Every final image runs as an unprivileged user (the table above). Some base images bring one (`node`, `www-data`,
`nginx` in nginx-unprivileged, `nonroot` in distroless); `python-api` and `java-api` create one with a fixed number
(10001). A **numeric** user ID matters in Kubernetes: with `runAsNonRoot: true` the kubelet can only verify a number.
That is why the Deployments here also set `runAsUser` explicitly (for example `runAsUser: 1000` for
[node-api](../kubernetes/node-api/deployment.yaml), whose image says `USER node`).

## Check yourself

<details><summary>Why does the frontend image not contain Node.js?</summary>

Node.js is only needed to build the React app into static files. The final stage starts from nginx and copies only
`dist/`. The browser runs the JavaScript; the container only serves files.
</details>

<details><summary>Which line makes the Go binary able to run on an image without a C library?</summary>

`CGO_ENABLED=0` in the `go build` command: the binary is statically linked and needs nothing from the base image.
</details>

<details><summary>You change one line in <code>node-api/src/server.js</code>. Which steps run again on rebuild?</summary>

Only the layers from `COPY src ./src` onwards. `npm ci` comes from the cache because `package.json` and
`package-lock.json` did not change.
</details>

<details><summary>Why is <code>node_modules</code> in node-api's <code>.dockerignore</code>?</summary>

Dependencies are installed inside the image with `npm ci`; a local `node_modules` (possibly built for another OS)
would be sent to the builder for nothing and could overwrite the clean install.
</details>

<details><summary>Why do the Deployments set <code>runAsUser</code> even though the images have a USER line?</summary>

`runAsNonRoot: true` can only be verified for a numeric user. Images like node-api say `USER node` (a name), so the
Pod spec sets the number (1000) explicitly.
</details>

Next: [04 · Images, tags and registries](04-images-tags-and-registries.md)
