# go-status · Go (standard library only)

> The Bookshop's service status board. Part of the [service contract](../../docs/CONTRACT.md). Time: 25 minutes.

## What is it?

**Go** is a **compiled** language: `go build` turns the source code into one machine-code file (a binary). With
`CGO_ENABLED=0` that binary is **static**: it needs no interpreter, no runtime and no system libraries. So the
container needs almost nothing besides the binary itself, and Go images are among the smallest you will build.

This service uses only Go's **standard library** (`net/http`, `encoding/json`): no external dependencies at all.

## What does the application do?

| Endpoint | Answer |
|---|---|
| `GET /` | name, version, language and runtime |
| `GET /health` | `{"status":"ok"}` (liveness and readiness: this service has no database) |
| `GET /api/status` | calls the `/health` endpoint of every service in `TARGETS`, **at the same time**, 2 s timeout each, and reports `up`/`down`, the HTTP status and the latency |

`TARGETS` is a comma-separated list of `name=url`, for example
`node-api=http://node-api:3000/health,python-api=http://python-api:8000/health`.

| File | What it contains |
|---|---|
| [main.go](main.go) | the whole application (about 150 lines) |
| [go.mod](go.mod) | the module name and the Go version; no `require` lines, because there are no dependencies |
| [Dockerfile](Dockerfile) | compile in a Go image, run in a minimal image |

## How do I run it locally?

With Go 1.27 installed, from this folder:

<!-- test: skip -->
```bash
TARGETS="example=https://example.com/" go run .
curl localhost:8080/api/status
```

The tested path in this lab uses **Docker**: no Go installation needed.

## How do I build the Docker image?

<!-- test: timeout=900; contains=go-status; output=tail:2 -->
```bash
docker build -t go-status:1.0.0 applications/go-status
docker images go-status
```

```text
...
IMAGE             ID             DISK USAGE   CONTENT SIZE   EXTRA
go-status:1.0.0   546243d3070b       16.4MB         3.79MB        
```

The [Dockerfile](Dockerfile), line by line:

| Line | Why |
|---|---|
| `FROM golang:1.27-alpine AS build` | the **build stage**: the full Go toolchain (compiler, standard library sources) |
| `COPY go.mod ./` + `RUN go mod download` | dependencies before code, for the layer cache (here there are none, but the pattern stays the same) |
| `COPY *.go ./` | the source code |
| `CGO_ENABLED=0 GOOS=linux go build` | a static Linux binary: no C libraries needed at run time |
| `-trimpath` | no paths of the build machine inside the binary |
| `-ldflags "-s -w -X main.version=${APP_VERSION}"` | strip debug information (smaller), and write the version into the variable `main.version` |
| `FROM gcr.io/distroless/static-debian12:nonroot` | the **final image**: no shell, no package manager, only CA certificates, time zone data and a non-root user |
| `COPY --from=build /out/go-status /go-status` | the only file we take from the build stage |
| `USER nonroot:nonroot` | runs as an unprivileged user (UID 65532) |
| `ENTRYPOINT ["/go-status"]` | the binary is PID 1 and receives SIGTERM directly |

### Why is the image so small?

Compare it with the image that compiled it:

<!-- test: timeout=600; contains=golang; contains=go-status; output -->
```bash
docker pull -q golang:1.27-alpine > /dev/null
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E 'REPOSITORY|golang|go-status'
```

```text
REPOSITORY:TAG                        SIZE
go-status:1.0.0                       16.4MB
golang:1.27-alpine                    381MB
```

16.4 MB for the final image (3.79 MB of compressed content, the amount a node actually downloads, in the build output
above) against 381 MB for the toolchain. The build stage needs the whole toolchain; the program does not. Multi-stage builds leave the toolchain behind. A
small image is pulled faster by every node, starts faster, and contains far fewer things that could have
vulnerabilities. The price: there is no shell in the container, so `docker exec ... sh` does not work (see
troubleshooting below).

## How do I run the container?

A status board needs something to watch. Start a tiny web server as a stand-in for a real service, and the status
board on the same network:

<!-- test: contains=go-lab -->
```bash
docker network create go-lab
docker run -d --name go-lab-web --network go-lab nginx:1.30-alpine
docker run -d --name go-lab-status --network go-lab -p 18080:8080 \
  -e TARGETS="web=http://go-lab-web/,ghost=http://ghost-api:9999/health" \
  go-status:1.0.0
docker ps --filter name=go-lab --format '{{.Names}}  {{.Image}}  {{.Status}}'
```

`ghost` does not exist, on purpose: the board must report it as down.

## How does Docker Compose run it?

In [compose/docker-compose.yml](../../compose/README.md) `go-status` gets `TARGETS` with the Compose service names
(`http://node-api:3000/health`, ...). It has no database, so it needs no password.

## How does Kubernetes run it?

A **Deployment** and a **Service** named `go-status`; `TARGETS` comes from a **ConfigMap** and uses the Kubernetes
Service names, which are the same names as in Compose. See [kubernetes/README.md](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why |
|---|---|
| Deployment `go-status` | runs and replaces the Pod |
| Service `go-status` (port 8080) | the stable name the frontend uses for `/api/status` |
| ConfigMap (`TARGETS`) | the list of services to check |
| `livenessProbe` and `readinessProbe` → `/health` | it has no database, so the same check answers both questions |
| no Secret | it holds no credentials |

## How do I verify it?

<!-- test: retry=20; contains="status":"ok"; contains=Go; output -->
```bash
curl -s http://localhost:18080/health
curl -s http://localhost:18080/
```

```text
{"service":"go-status","status":"ok","version":"1.0.0"}
{"description":"Service status board: checks the /health endpoint of every Bookshop service","language":"Go","runtime":"go1.27.1","service":"go-status","version":"1.0.0"}
```

<!-- test: retry=10; contains="up":1; contains="total":2; output -->
```bash
curl -s http://localhost:18080/api/status
```

```text
{"services":[{"name":"ghost","url":"http://ghost-api:9999/health","status":"down","http_status":0,"latency_ms":2001,"error":"Get \"http://ghost-api:9999/health\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)"},{"name":"web","url":"http://go-lab-web/","status":"up","http_status":200,"latency_ms":2}],"total":2,"up":1}
```

`web` is up (HTTP 200 in a few milliseconds); `ghost` is down with the reason. Both checks ran at the same time, so the
answer took about as long as the slowest check, not the sum of both.

<!-- test: contains=GET /api/status 200; output -->
```bash
docker logs go-lab-status
```

```text
go-status 2026/10/04 17:51:28 listening on :8080, version 1.0.0, 2 targets
go-status 2026/10/04 17:51:28 GET /health 200
go-status 2026/10/04 17:51:28 GET / 200
go-status 2026/10/04 17:51:30 GET /api/status 200
```

## How do I troubleshoot it?

### Every service is "down"

<!-- test: contains=go-lab-status2 -->
```bash
docker run -d --name go-lab-status2 -p 18081:8080 \
  -e TARGETS="web=http://go-lab-web/" go-status:1.0.0
docker ps --filter name=go-lab-status2 --format '{{.Names}}  {{.Status}}'
```

<!-- test: retry=10; contains="up":0; output -->
```bash
curl -s http://localhost:18081/api/status
```

```text
{"services":[{"name":"web","url":"http://go-lab-web/","status":"down","http_status":0,"latency_ms":2001,"error":"Get \"http://go-lab-web/\": context deadline exceeded (Client.Timeout exceeded while awaiting headers)"}],"total":1,"up":0}
```

The container was started **without** `--network go-lab`, so the name `go-lab-web` does not resolve from it. Containers
find each other by name only on a shared network. In Kubernetes the equivalent is a wrong Service name or a Service in
another namespace.

### "I can't open a shell in it"

<!-- test: fail; output -->
```bash
docker exec go-lab-status sh -c 'echo hi'
```

```text
OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file not found in $PATH
```

There is no shell in a distroless image: that is the point. Debug from outside (`docker logs`, the HTTP endpoints), or
start a debugging container on the same network: `docker run --rm --network go-lab busybox:1.37 wget -qO- http://go-lab-status:8080/health`
(in Kubernetes: `kubectl debug` or a temporary Pod).

<!-- test: contains="status":"ok"; output -->
```bash
docker run --rm --network go-lab busybox:1.37 wget -qO- http://go-lab-status:8080/health
```

```text
{"service":"go-status","status":"ok","version":"1.0.0"}
```

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · removes the lab containers and their network (the image stays).
```

<!-- test: contains=go-lab -->
```bash
docker rm -f go-lab-status go-lab-status2 go-lab-web
docker network rm go-lab
```

## Practical challenge

**Task:** make the status board answer HTTP **503** instead of 200 when at least one service is down, so that a
monitoring system (or a Kubernetes probe of another component) can react to the HTTP status alone.

**Requirements**

1. `GET /api/status` keeps the same JSON body.
2. Status code: 200 when `up == total`, 503 otherwise.
3. Release it as `go-status:1.1.0`.

**Hints:** look at the call to `writeJSON` in the `/api/status` handler; the version comes from `--build-arg`.

**Expected result:** with the `ghost` target in the list, `curl -s -o /dev/null -w '%{http_code}' localhost:18080/api/status`
prints `503`.

<details>
<summary>Solution</summary>

In `main.go`, replace the last line of the `/api/status` handler with:

```go
code := http.StatusOK
if up < len(results) {
    code = http.StatusServiceUnavailable
}
writeJSON(w, code, map[string]any{"services": results, "up": up, "total": len(results)})
```

```text
docker build --build-arg APP_VERSION=1.1.0 -t go-status:1.1.0 applications/go-status
```

</details>

**Explanation:** the body is for people; the status code is for machines. Load balancers, probes and monitoring look
at the code first. Do **not** use this endpoint as go-status's own liveness probe, though: one broken service would
then restart the status board, which is not broken.

Next: [java-api](../java-api/README.md)
