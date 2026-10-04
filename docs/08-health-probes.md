# 08 · Health probes

> Time: 25 minutes

The kubelet on each node asks every container, again and again, three different questions. Each question is a
**probe**, and each one leads to a different action.

| Probe | The question | When it fails | Endpoint in this lab |
|---|---|---|---|
| **livenessProbe** | "Is this process still alive, or stuck?" | the container is **restarted** | `/health` |
| **readinessProbe** | "Should this Pod receive traffic **right now**?" | the Pod is **removed from the Service** (no restart) | `/ready` (services with a database) or `/health` |
| **startupProbe** | "Has it finished starting?" | after the limit: restarted; until then liveness and readiness wait | `/health` (only `java-api`) |

> Liveness answers "Should Kubernetes restart this container?"
> Readiness answers "Should this Pod receive traffic?"

## /health and /ready: two endpoints on purpose

The [contract](CONTRACT.md) gives every API two endpoints:

```text
 /health   → 200 as soon as the process can answer HTTP.          NEVER checks the database.   → livenessProbe
 /ready    → 200 when the database answers, 503 when it does not.                                → readinessProbe
```

Why must `/health` not check the database? Imagine it did, and PostgreSQL restarts for 30 seconds:

```text
 /health checks the DB (wrong)                         /health ignores the DB (this lab)
 ─────────────────────────────                         ──────────────────────────────────
 DB down → every API's liveness fails                  DB down → /ready fails → Pods leave the Services
 → Kubernetes restarts ALL API containers              → /health still passes → nothing is restarted
 → restarts do not fix the database                    DB back → /ready passes → traffic resumes at once
 → the APIs come back slowly, in a restart loop        No restarts, no cold starts, no lost in-memory state
```

A restart only helps when the **process itself** is broken. A missing dependency is a readiness problem.

## The probes in the lab

From [node-api/deployment.yaml](../kubernetes/node-api/deployment.yaml) (python-api is the same):

```yaml
          livenessProbe:                     # "should Kubernetes restart this container?"
            httpGet: { path: /health, port: http }
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:                    # "should this Pod receive traffic right now?"
            httpGet: { path: /ready, port: http }
            periodSeconds: 5
            failureThreshold: 2
```

- liveness: checked every 10 s; 3 failures in a row (about 30 s) → restart.
- readiness: checked every 5 s; 2 failures (about 10 s) → out of the Service until it passes again.
- `port: http` refers to the **named** container port, so the number lives in one place.

The other services:

| Service | liveness | readiness | Why |
|---|---|---|---|
| `go-status`, `frontend` | `/health` | `/health` | no database: ready as soon as they run |
| `java-api` | `/health` | `/ready` | plus a **startupProbe** (below) |
| `laravel-web` (nginx) | `/health` | `/ready` | nginx passes both to Laravel |
| `laravel-fpm` | `tcpSocket: 9000` | – | FPM speaks FastCGI, not HTTP: the probe only checks that it accepts connections |
| `postgres` | `exec: pg_isready` | `exec: pg_isready` | a command inside the container instead of an HTTP call |

## The startup probe for Java

`java-api` measured its own startup (Spring's log line `Started BookshopApplication in ... seconds`, see
[java-api/README.md](../applications/java-api/README.md)):

| CPU available | Startup |
|---|---|
| all CPUs of a laptop | 2.6 s |
| 1 CPU (the Pod's limit in this lab) | 4.6 s |
| 0.5 CPU | 9.3 s |

A liveness probe that starts checking right away could restart a JVM that is simply still starting, on a busy node
again and again. The startup probe holds the other probes back until the application has started once:

```yaml
          startupProbe:                      # the JVM needs several seconds: give it up to 60 s before liveness starts
            httpGet: { path: /health, port: http }
            periodSeconds: 2
            failureThreshold: 30
```

2 s × 30 attempts = up to 60 s to start, while the liveness probe can stay strict (3 × 10 s) for the rest of the
container's life. Node.js, Python and Go start fast enough not to need one.

## What a failing probe looks like

Readiness failing looks like this (an example; the troubleshooting labs record the real thing):

```text
NAME                        READY   STATUS    RESTARTS   AGE
node-api-6f678b5b5-kxsnl    0/1     Running   0          2m
```

`kubectl get endpoints node-api` no longer lists that Pod's IP. `kubectl describe pod` shows events such as
`Readiness probe failed: HTTP probe failed with statuscode: 503`.

Liveness failing looks like this (example):

```text
NAME                        READY   STATUS    RESTARTS      AGE
node-api-6f678b5b5-kxsnl    1/1     Running   3 (20s ago)   5m
```

`RESTARTS` goes up; `kubectl logs --previous` shows the output of the container before the restart.

## Common mistakes

| Mistake | Consequence |
|---|---|
| liveness checks a dependency (database, another API) | one outage restarts everything that depends on it |
| no readiness probe | traffic reaches Pods that are still starting: errors during every rollout |
| liveness without a startup probe on a slow starter | restart loop on slow nodes or with low CPU limits |
| probing the wrong port or path | the Pod never becomes Ready (readiness) or restarts forever (liveness) |
| timeouts shorter than the endpoint needs under load | healthy Pods are taken out or restarted when they are busy |
| readiness and liveness identical and heavy | double work, and a slow dependency turns into restarts |

## Check yourself

<details><summary>The database is down. Should node-api's containers be restarted?</summary>

No. Restarting does not fix the database. `/ready` fails, the Pods leave the Service; `/health` keeps passing, so
nothing restarts. When the database is back, they become Ready again on their own.
</details>

<details><summary>What does Kubernetes do when a readiness probe fails? And a liveness probe?</summary>

Readiness: removes the Pod from the Service endpoints (no traffic), no restart. Liveness: kills and restarts the
container.
</details>

<details><summary>Why does only java-api have a startupProbe?</summary>

The JVM and Spring need seconds to start (4.6 s with one CPU, 9.3 s with half a CPU in the lab's measurements). The
startup probe gives it up to 60 s before the liveness probe may restart it. The other services start fast.
</details>

<details><summary>Why is laravel-fpm's liveness probe a <code>tcpSocket</code> check?</summary>

PHP-FPM speaks FastCGI, not HTTP, so an `httpGet` probe cannot talk to it. A TCP check verifies that it accepts
connections on port 9000; the HTTP checks go through nginx (`laravel-web`).
</details>

<details><summary>A Pod shows <code>0/1 Running</code> with 0 restarts. Which probe is failing?</summary>

The readiness probe. The container runs (no restarts, so liveness passes) but is not Ready, so it receives no
traffic.
</details>

Next: [09 · Resources: requests and limits](09-resources-requests-and-limits.md)
