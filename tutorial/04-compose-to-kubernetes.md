# 04 · From Compose to Kubernetes

> Goal: you know what every Compose line becomes in Kubernetes, and the cluster has its entry point, configuration,
> secrets and database. Level 7 of the [roadmap](../README.md#4-the-roadmap). Time: about 60 minutes.

## Before you start

Stop the Compose platform (the Compose lesson's cleanup did that). kind uses port 8080 on your machine; Compose used
8081 and 8082, so they would not even collide, but memory is better spent on one platform at a time.

## The walk

### 1. Read docs/06 slowly

[docs/06](../docs/06-compose-to-kubernetes.md) is the heart of the course. Read the mapping table row by row with
[compose/docker-compose.yml](../compose/docker-compose.yml) open on one side and the [kubernetes/](../kubernetes/README.md)
folder on the other. The short version:

```text
 service ──────────────► Deployment (StatefulSet for the database, Job/CronJob for one-off work)
 ports ────────────────► Service (inside the cluster) + Ingress (from outside)
 environment / .env ───► ConfigMap / Secret
 volumes ──────────────► PersistentVolumeClaim
 healthcheck ──────────► probes (startup, liveness, readiness)
 depends_on ───────────► nothing: readiness + applications that retry
```

The last row is the one people get wrong. Kubernetes has no start order. Every application in this lab survives a
missing database (its `/ready` fails until the database answers), and that is what makes ordering unnecessary.

### 2. Create the cluster: kubernetes/00

Run [kubernetes/00-cluster.md](../kubernetes/00-cluster.md). Two things to watch:

- The two nodes are Docker containers (`bookshop-control-plane`, `bookshop-worker`), but the Kubernetes inside is
  real: version 1.37.0, the same API as any cloud cluster.
- The end of the lesson:

  ```text
  404 page not found
  ```

  A 404 is good news here. It comes from Traefik, so requests from your browser reach the ingress controller. There
  are just no routes yet.

### 3. The foundation: kubernetes/01

Run [kubernetes/01-foundation.md](../kubernetes/01-foundation.md). Watch for:

- `kubectl config set-context --current --namespace=bookshop`: from now on, every command works in the namespace
  `bookshop` without `-n`. A small step that saves a thousand typing mistakes.
- The Secrets are created from **random values**, directly in the cluster. They are not in any file. `describe` shows
  sizes, never values.
- The database's claim is `Bound` and PostgreSQL answers:

  ```text
  PostgreSQL 18.6 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
  ```

## Expert commentary

- **"Can't we just convert the Compose file?"** Tools such as kompose exist. They produce YAML you still have to
  understand, fix and maintain: probes, resources, Secrets and storage need decisions a converter cannot make. Learning
  the mapping is what lets you review such output.
- **One namespace per application** makes access control, quotas and cleanup simple: deleting the namespace deletes
  everything, which is exactly what the cleanup lesson does.
- **Interview angle:** "How do you handle service start order in Kubernetes?" You don't: readiness probes plus
  applications that retry their dependencies. Init containers exist for the rare hard dependency.

## Checkpoint

- [ ] You can map every block of the Compose file to a Kubernetes resource, out loud.
- [ ] Lessons 00 and 01 pass: two Ready nodes, Traefik answers 404, PostgreSQL answers.
- [ ] You can explain why the Secrets are not in Git, and what `describe secret` shows instead of the value.

Next: [05 · Deploy the APIs](05-deploy-the-apis.md)
