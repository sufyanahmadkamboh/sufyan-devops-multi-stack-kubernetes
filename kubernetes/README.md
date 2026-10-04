# Kubernetes · deploy the platform, one application at a time

> Levels 7–18 of the [roadmap](../README.md). Before you start: the platform must work in
> [Docker Compose](../compose/README.md), and you should have read
> [docs/06 · From Docker Compose to Kubernetes](../docs/06-compose-to-kubernetes.md).

Run the lessons in order. Each one adds one piece and verifies it before moving on; every command was run on a real
kind cluster, and the outputs you see are the real ones.

| # | Lesson | Level | What you add | New Kubernetes ideas |
|---|---|---|---|---|
| 00 | [A local cluster](00-cluster.md) | 7 | kind cluster (2 nodes, Kubernetes 1.37), Traefik ingress controller | nodes, Helm, IngressClass |
| 01 | [Foundation](01-foundation.md) | 7 | namespace, ConfigMap, Secrets, PostgreSQL | Namespace, ConfigMap, Secret, StatefulSet, PVC |
| 02 | [node-api](02-node-api.md) | 8 | Node.js API | Deployment, Pod, Service, endpoints, port-forward, logs |
| 03 | [frontend](03-frontend.md) | 9 | React UI | runtime configuration, one image everywhere |
| 04 | [python-api](04-python-api.md) | 10 | Python API | the same pattern, another language |
| 05 | [go-status](05-go-status.md) | 11 | Go status board | DNS service discovery, distroless images |
| 06 | [java-api](06-java-api.md) | 12 | Java API | startupProbe, JVM memory |
| 07 | [laravel-admin](07-laravel-admin.md) | 13 | Laravel admin | Job (migrations), two containers in one Pod |
| 08 | [report-worker](08-report-worker.md) | 13 | JavaScript batch job | CronJob, Job from a CronJob |
| 09 | [Ingress](09-ingress.md) | 14 | one entry point for everything | Service types, EndpointSlices, Ingress rules |
| 10 | [Config and Secrets](10-config-and-secrets.md) | 15 | change configuration | rollout restart, what base64 means |
| 11 | [Health probes](11-health-probes.md) | 16 | take the database away | readiness vs liveness, in action |
| 12 | [Storage](12-storage.md) | 17 | delete the database Pod | PersistentVolumes, StatefulSet identity |
| 13 | [Resources](13-resources.md) | 18 | a limit that is too small | requests, limits, OOMKilled, safe rollouts |
| 14 | [Scaling and updates](14-scaling-rolling-updates.md) | 18 | v1.0.0 → v1.1.0 → back | scale, set image, rollout history, undo |
| – | [Cleanup](cleanup.md) | | | delete namespace, delete cluster |

Then: [troubleshooting](../troubleshooting/README.md) (level 19) and the [capstone](../capstone/README.md) (level 20).

## The files

```text
kubernetes/
├── cluster/            kind-config.yaml (the cluster), traefik-values.yaml (the ingress controller)
├── namespace.yaml
├── config/             ConfigMap bookshop-config
├── secrets/            README + an EXAMPLE Secret (real ones are created with kubectl, never committed)
├── database/           PostgreSQL: headless Service + StatefulSet with a volume claim
├── node-api/  python-api/  java-api/  go-status/  frontend/     Deployment + Service each
├── laravel-admin/      Deployment (nginx + PHP-FPM in one Pod), Service, migration Job
├── report-worker/      CronJob
└── ingress/            the Ingress: host and path rules for everything
```

Apply everything at once (after the cluster, namespace and Secrets exist, and the images are loaded) with
`kubectl apply -R -f kubernetes/ --dry-run=server` to check, then without `--dry-run`. The lessons apply them one by
one, so you see what each piece adds.
