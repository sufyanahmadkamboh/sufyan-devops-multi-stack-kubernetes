# 06 · From Docker Compose to Kubernetes

> Time: 40 minutes. The most important lesson of the lab.

Compose and Kubernetes solve related problems. Compose answers "how do I run these containers together on **this
machine**?". Kubernetes answers "how do I keep these applications running on **a cluster of machines**, update them
without downtime and recover from failures by itself?". The images are the same. The description is not.

Kubernetes does **not** mean "take docker-compose.yml and magically run it". Every line of the Compose file expresses
a requirement of the application; in Kubernetes each requirement becomes the resource made for it.

```text
                         docker-compose.yml
                                 │
     ┌──────────┬────────────┬───┴────────┬──────────────┬─────────────┬──────────────┐
  services    image      ports      environment       volumes     healthcheck   networks
     │          │            │            │                │             │            │
     ▼          ▼            ▼            ▼                ▼             ▼            ▼
 Deployment  container   Service     ConfigMap +     PersistentVolume  probes    cluster network
 StatefulSet  image      (+Ingress)  Secret          Claim                       + Service names
 Job/CronJob  in the Pod
     │
     └── each replica is a Pod: one or more containers
```

## The mapping table

| Docker Compose | Kubernetes | In this lab |
|---|---|---|
| a service (long-running) | **Deployment** (or **StatefulSet** when it has its own data) | `node-api` ... → Deployments; `postgres` → StatefulSet |
| a service that runs once | **Job** / **CronJob** | `laravel-migrate` → Job; `report-worker` → CronJob |
| a container | a **Pod** (one or more containers) | `laravel-web` + `laravel-fpm` → one Pod with two containers |
| `image:` | `containers[].image` | identical names: `node-api:1.0.0` |
| `ports:` | a **Service** (inside the cluster), an **Ingress** (from outside) | Services for every API; one Ingress |
| `environment:` | **ConfigMap** (plain values) and **Secret** (sensitive values) | `bookshop-config`, `db-credentials`, `laravel-app-key` |
| `volumes:` (named) | **PersistentVolumeClaim** | `postgres`' `volumeClaimTemplates` |
| `networks:` | one flat cluster network + **Services** for names (+ NetworkPolicies to restrict) | every Pod can reach every Service by name |
| `deploy.replicas` / `--scale` | `spec.replicas` | `node-api: 2`, `python-api: 2`, `frontend: 2` |
| `healthcheck:` | **probes**: readiness, liveness, startup | `/ready` → readinessProbe, `/health` → livenessProbe |
| `depends_on:` | no ordering: **readiness probes** + applications that retry | the APIs start before the database answers and become Ready later |
| `restart:` | built into the workload type (`restartPolicy`) | Deployments always restart; Jobs `Never`/`OnFailure` |

Each row, with the real files of the lab side by side:

### service → Deployment

```yaml
# compose/docker-compose.yml                    # kubernetes/node-api/deployment.yaml
  node-api:                                     kind: Deployment
    image: node-api:1.0.0                       metadata: { name: node-api, namespace: bookshop }
                                                spec:
                                                  replicas: 2
                                                  selector:
                                                    matchLabels: { app: node-api }
                                                  template:            # ← the Pod to create, as often as replicas says
                                                    metadata:
                                                      labels: { app: node-api, ... }
                                                    spec:
                                                      containers:
                                                        - name: node-api
                                                          image: node-api:1.0.0
```

A Deployment is not a container; it is a **promise**: "keep 2 Pods of this template running". If a Pod dies or a
node disappears, the Deployment's controller creates a replacement. Compose has no such controller across machines.

### service with data → StatefulSet

```yaml
# compose                                       # kubernetes/database/postgres.yaml
  postgres:                                     kind: StatefulSet
    image: postgres:18.6-alpine                 spec:
    volumes:                                      serviceName: postgres
      - pgdata:/var/lib/postgresql                replicas: 1
                                                  ...
                                                  volumeClaimTemplates:      # one disk per Pod, kept across restarts
                                                    - metadata: { name: data }
                                                      spec: { resources: { requests: { storage: 1Gi } } }
```

A StatefulSet gives each Pod a stable name (`postgres-0`) and its own PersistentVolumeClaim that follows it. A
Deployment's Pods are interchangeable and get random names: fine for stateless APIs, wrong for a database.

### one-off service → Job, batch service → CronJob

```yaml
# compose                                       # kubernetes/laravel-admin/migrate-job.yaml
  laravel-migrate:                              kind: Job
    image: laravel-fpm:1.0.0                    spec:
    command: ["php","artisan","migrate",          backoffLimit: 4
              "--force","--seed"]                 template:
    restart: "no"                                   spec:
                                                      restartPolicy: Never
                                                      containers:
                                                        - image: laravel-fpm:1.0.0
                                                          args: ["php","artisan","migrate","--force","--seed"]

# compose                                       # kubernetes/report-worker/cronjob.yaml
  report-worker:                                kind: CronJob
    profiles: [jobs]   # run by hand            spec:
                                                  schedule: "*/10 * * * *"
                                                  concurrencyPolicy: Forbid
```

A Job runs Pods **until one succeeds** (exit code 0). A CronJob creates such a Job on a schedule. See
[14](14-jobs-and-cronjobs.md).

### container → Pod

Most Pods here have one container. `laravel-admin` has two, because nginx and PHP-FPM are one unit: they always run,
scale and get replaced together, and they talk over `127.0.0.1` because containers in a Pod share one network
namespace:

```yaml
# compose: two services on a network            # kubernetes/laravel-admin/deployment.yaml: ONE Pod
  laravel-fpm:                                    containers:
    image: laravel-fpm:1.0.0                        - name: laravel-web
  laravel-web:                                        image: laravel-web:1.0.0
    image: laravel-web:1.0.0                          env: [{ name: FPM_HOST, value: "127.0.0.1" }]
    environment:                                    - name: laravel-fpm
      FPM_HOST: laravel-fpm                           image: laravel-fpm:1.0.0
```

The only change is one environment variable: `FPM_HOST` points to a service name in Compose and to `127.0.0.1` in the
Pod. See [15](15-multi-container-pods.md).

### ports → Service (+ Ingress)

```yaml
# compose                                       # kubernetes/node-api/service.yaml
  node-api:                                     kind: Service
    # no ports: only reachable by name          spec:
    # from other containers                       type: ClusterIP
                                                  selector: { app: node-api }   # all Ready Pods with this label
  frontend:                                       ports:
    ports: ["127.0.0.1:8081:8080"]                  - port: 3000
                                                      targetPort: http
```

A **Service** gives a set of Pods one stable name and virtual IP inside the cluster, and spreads requests over the
Ready ones. It replaces both Compose's DNS name and its load spreading. **Publishing a port to the outside** has no
one-to-one equivalent: the lab uses one **Ingress** ([ingress.yaml](../kubernetes/ingress/ingress.yaml)) that routes
`bookshop.localhost` paths to the Services, instead of one host port per service. See
[11](11-services-networking-and-ingress.md).

### environment → ConfigMap + Secret

```yaml
# compose                                       # kubernetes/config/bookshop-config.yaml (ConfigMap)
x-db-env: &db-env                               data:
  DB_HOST: postgres                               DB_HOST: postgres
  DB_PORT: "5432"                                 DB_PORT: "5432"
  DB_NAME: bookshop                               DB_NAME: bookshop
  DB_USER: bookshop                               DB_USER: bookshop
  DB_PASSWORD: ${DB_PASSWORD:?...}              # the password: a Secret, created with kubectl, never in Git

                                                # in the Deployment:
                                                - name: DB_PASSWORD
                                                  valueFrom: { secretKeyRef: { name: db-credentials, key: DB_PASSWORD } }
```

Same variable names, same values; they just come from two Kubernetes objects. See
[07](07-configmaps-and-secrets.md).

### healthcheck → probes

```yaml
# compose                                       # kubernetes/java-api/deployment.yaml
  java-api:                                     startupProbe:                    # give the JVM up to 60 s
    healthcheck:                                  httpGet: { path: /health, port: http }
      test: ["CMD", "wget", "-qO-",               periodSeconds: 2
             "http://127.0.0.1:8080/ready"]       failureThreshold: 30
      interval: 3s                              livenessProbe:                   # restart if the process hangs
      retries: 40                                 httpGet: { path: /health, port: http }
                                                readinessProbe:                  # traffic only when the DB answers
                                                  httpGet: { path: /ready, port: http }
```

A Compose healthcheck is one check that mostly gates `depends_on`. Kubernetes splits it into three questions and acts
on each one: restart, stop sending traffic, or wait. See [08](08-health-probes.md).

### depends_on → readiness and retrying applications

Kubernetes starts all Pods at the same time; there is no "start node-api after postgres". The lab handles that the
way production systems do:

1. the APIs **start without the database** (they do not crash when it is missing),
2. their **readinessProbe** (`/ready`) fails until the database answers, so the Service sends them no traffic,
3. the moment PostgreSQL is up, `/ready` passes and traffic flows.

Ordering by readiness is more robust than ordering by start: it also covers a database that restarts **later**, which
`depends_on` never could.

### networks → one flat network + Services

Every Pod in the cluster gets its own IP and can reach every other Pod and Service (the CNI plugin makes that work
across nodes). There is no `frontend`/`backend` split by default; isolation is added with **NetworkPolicies** when
needed. Names come from Services (`node-api`, `postgres`), resolved by CoreDNS.

## What does not translate

| Compose feature | In Kubernetes |
|---|---|
| `build:` | nothing: Kubernetes only runs images. You build (and load or push) them first |
| `depends_on` ordering | none: readiness probes + applications that retry |
| `ports: "8081:8080"` on your computer | a Service (inside), an Ingress or a NodePort/LoadBalancer (outside) |
| `.env` file substitution | ConfigMaps and Secrets, or a templating tool (Helm, Kustomize) |
| `profiles` | separate manifests you apply when you want them (or a CronJob instead of "run on demand") |

## Why not just convert the file?

Tools such as **kompose** read a `docker-compose.yml` and print Kubernetes YAML. They are a fine starting point, but
the output still has to be understood and fixed: kompose cannot know that `postgres` needs a StatefulSet, that
`laravel-migrate` is a Job, that `laravel-web` and `laravel-fpm` belong in one Pod, which values are secrets, or which
endpoint means "ready". Those are decisions about the application, and they are exactly what this lesson is about.

## Check yourself

<details><summary>node-api publishes no port in Compose. How do other Pods reach it in Kubernetes?</summary>

Through the `node-api` Service: a stable name and virtual IP in front of the Ready node-api Pods. In Compose, other
containers reach it by its service name on the shared network; publishing a host port was never needed.
</details>

<details><summary>Why is postgres a StatefulSet and node-api a Deployment?</summary>

postgres has data that must stay with it across restarts: a StatefulSet gives it a stable name and its own
PersistentVolumeClaim. node-api keeps no state; its Pods are interchangeable, which is what a Deployment manages.
</details>

<details><summary>What replaces <code>depends_on: postgres: condition: service_healthy</code>?</summary>

Nothing orders the start. The APIs start anyway, their readinessProbe (`/ready`) fails until the database answers,
and the Service only sends them traffic once they are Ready.
</details>

<details><summary>Why are laravel-web and laravel-fpm two services in Compose but one Pod in Kubernetes?</summary>

They form one unit that always runs and scales together. In a Pod they share the network namespace and talk over
127.0.0.1; only `FPM_HOST` changes. (Two separate Deployments would also work; the Pod keeps the pair together.)
</details>

<details><summary>Which Compose key has no equivalent at all in a Kubernetes manifest?</summary>

`build:`. Kubernetes never builds images; they must exist in the cluster or a registry before a Pod can use them.
</details>

Next: [07 · ConfigMaps and Secrets](07-configmaps-and-secrets.md)
