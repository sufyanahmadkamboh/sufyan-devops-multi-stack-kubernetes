# Capstone · the complete multi-stack platform

> Level 20 of the [roadmap](../README.md). Time: 1–2 hours.

Everything the course built, together, verified by a script. Then a final on-call scenario.

```text
                         Browser
                            │
                            ▼
                  Ingress (Traefik) ──────────────────────────────┐ admin host
       ┌──────────┬─────────┼──────────┬──────────────┐           ▼
       ▼          ▼         ▼          ▼              ▼       Laravel admin
    React UI   Node.js   Java API   Python API   Go status    (nginx + PHP-FPM, 1 Pod)
               users     books      statistics   board              │
                  │         │          │                            │
                  └─────────┴────┬─────┴────────────────────────────┘
                                 ▼
                     PostgreSQL (StatefulSet) ── PersistentVolume
                                 ▲
             report-worker (JavaScript, CronJob)   laravel-migrate (Job)
```

What the finished platform must demonstrate, and how it is checked:

| Capability | Where it lives | Checked by verify.sh |
|---|---|---|
| multiple languages, Dockerfiles, versioned images | applications/, `<service>:1.0.0` | no image without a version tag |
| Docker Compose | compose/ | (the Compose lesson) |
| Deployments, Services, Ingress | kubernetes/*/, ingress/ | all Available, every route answers through the Ingress |
| ConfigMaps, Secrets | config/, secrets created by kubectl | the password is not in the ConfigMap |
| health probes, startup probe | every Deployment | liveness/readiness everywhere, startupProbe on java-api |
| requests and limits | every container | CPU and memory requests and limits everywhere |
| storage | the PostgreSQL StatefulSet | claim Bound; data survives deleting the database Pod |
| Jobs and CronJobs, multi-container Pods | laravel-migrate, report-worker, laravel-admin | Job complete, CronJob exists, 2 containers |
| rolling updates done | every Deployment | no Deployment stuck mid-rollout |
| security basics | every Pod | non-root everywhere |

## Part A · Deploy it all, from nothing

[deploy.sh](deploy.sh) does what lessons 00–09 did, in the right order, in one command: build the images, create the
cluster and the ingress controller if they do not exist, load the images, create the namespace, configuration and
generated Secrets, start the database, run the migration Job, deploy every application, create the Ingress, and run
the first report. Read it first: every step is one you know. It is idempotent: running it again changes nothing that
is already correct.

<!-- test: timeout=2400; contains=Bookshop is up; output=tail:12 -->
```bash
bash capstone/deploy.sh
```

```text
...
deployment.apps/node-api condition met
deployment.apps/python-api condition met

==> 7/8 entry point
ingress.networking.k8s.io/bookshop unchanged

==> 8/8 first report
job.batch/capstone-report created
job.batch/capstone-report condition met

Bookshop is up:  http://bookshop.localhost:8080   admin: http://admin.bookshop.localhost:8080
Verify it:       capstone/verify.sh
```

## Part B · Verify everything

<!-- test: timeout=900; contains=0 failed; output -->
```bash
bash capstone/verify.sh
```

```text
Workloads
  PASS  6 Deployments, all Available
  PASS  no Deployment is stuck in the middle of a rollout
  PASS  PostgreSQL StatefulSet ready (1/1)
  PASS  database volume claim Bound
  PASS  migration Job completed
  PASS  report CronJob exists
  PASS  laravel-admin Pod runs 2 containers
Good practice in every Deployment
  PASS  every container has CPU and memory requests and limits
  PASS  every HTTP container has a liveness probe
  PASS  every Service-facing container has a readiness probe
  PASS  java-api has a startupProbe
  PASS  no image uses the tag latest (or no tag)
  PASS  every Pod runs as non-root
  PASS  the database password comes from a Secret, not a ConfigMap
Through the Ingress
  PASS  UI: /
  PASS  Node.js: /api/users
  PASS  Java: /api/books
  PASS  Python: /api/stats (with a report)
  PASS  Go: /api/status, every service up
  PASS  Laravel: admin host
Resilience
  PASS  data survives the loss of the database Pod
  PASS  every Deployment Available again afterwards

22 passed, 0 failed
```

## Part C · The final challenge: Monday morning

Over the weekend, three changes were made to the running platform. Users report that statistics are missing and the
status board looks odd. **Run [break.sh](break.sh) without reading it**, then find and fix every problem using only
what the course taught (`get`, `describe`, `logs`, endpoints, events, rollout history), until `verify.sh` passes
again.

<!-- test: contains=Good luck -->
```bash
bash capstone/break.sh
```

<!-- test: timeout=600; fail; contains=FAIL; output -->
```bash
bash capstone/verify.sh
```

```text
Workloads
  PASS  6 Deployments, all Available
  FAIL  no Deployment is stuck in the middle of a rollout
        ['go-status', 'java-api']
  PASS  PostgreSQL StatefulSet ready (1/1)
  PASS  database volume claim Bound
  PASS  migration Job completed
  PASS  report CronJob exists
  PASS  laravel-admin Pod runs 2 containers
Good practice in every Deployment
  PASS  every container has CPU and memory requests and limits
  PASS  every HTTP container has a liveness probe
  PASS  every Service-facing container has a readiness probe
  PASS  java-api has a startupProbe
  PASS  no image uses the tag latest (or no tag)
  PASS  every Pod runs as non-root
  PASS  the database password comes from a Secret, not a ConfigMap
Through the Ingress
  PASS  UI: /
  PASS  Node.js: /api/users
  PASS  Java: /api/books
  FAIL  Python: /api/stats (with a report)
            raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  FAIL  Go: /api/status, every service up
        5 6
  PASS  Laravel: admin host
Resilience
  PASS  data survives the loss of the database Pod
  PASS  every Deployment Available again afterwards

19 passed, 3 failed
```

Rules: fix the cause, not the symptom (no deleting and recreating everything), and write down for each problem:
symptom → command that showed the cause → root cause → fix.

<details>
<summary>Solution</summary>

1. **Statistics missing.** `/api/stats` returns `503 no available server`. The Pods of python-api are Running and
   Ready, but `kubectl get endpointslices -l kubernetes.io/service-name=python-api` shows no endpoints: the Service's
   selector says `app: python-apii`. Fix: `kubectl apply -f kubernetes/python-api/service.yaml`.
2. **go-status rollout stuck.** `kubectl get pods -l app=go-status` shows a new Pod in `ImagePullBackOff` next to the
   old, still-working Pod; `kubectl describe` says the image `go-status:1.0.1` cannot be pulled (it was never built).
   The status board itself still works: the rolling update protected it. Fix: `kubectl rollout undo deployment/go-status`.
3. **java-api rollout stuck.** A restart was triggered after the ConfigMap changed. The new java-api Pod never becomes
   Ready; its `/ready` (and the log) report that the database `bookshp` does not exist. The ConfigMap's `DB_NAME` is
   misspelled. Fix: `kubectl apply -f kubernetes/config/bookshop-config.yaml`, then
   `kubectl rollout restart deployment/java-api`. (Other services did not restart, so they still use the old, correct
   value: a ConfigMap change is a time bomb until the next restart.)

<!-- test: timeout=600; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/python-api/service.yaml
kubectl rollout undo deployment/go-status
kubectl apply -f kubernetes/config/bookshop-config.yaml
kubectl rollout restart deployment/java-api
kubectl rollout status deployment/go-status --timeout=240s
kubectl rollout status deployment/java-api --timeout=240s
```

<!-- test: timeout=900; retry=3; contains=0 failed; output=tail:3 -->
```bash
bash capstone/verify.sh
```

```text
...
  PASS  every Deployment Available again afterwards

22 passed, 0 failed
```

</details>

## What you can say now

> "I know how to take applications written in different languages, package them as Docker containers, run them
> together using Docker Compose, understand their dependencies and networking, and deploy those applications to
> Kubernetes using the appropriate Kubernetes resources."

When you are done: [kubernetes/cleanup.md](../kubernetes/cleanup.md).
