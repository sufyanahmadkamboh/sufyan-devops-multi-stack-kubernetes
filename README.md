# 🧩 Multi-Stack Applications on Kubernetes · From Docker Compose to Kubernetes

[![test-lessons](https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes/actions/workflows/test.yaml/badge.svg)](https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes/actions/workflows/test.yaml)

Take applications written in **seven different stacks**, package each one as a Docker image, run them together with
Docker Compose, and deploy the same images to Kubernetes, with the right resource for each job.

```text
Build → Dockerize → Compose → Run → Verify → Convert → Deploy to Kubernetes → Troubleshoot → Improve
```

The applications form one small platform, **Bookshop**, so you also learn how services find and depend on each
other:

```text
                                   Browser
                 bookshop.localhost:8080      admin.bookshop.localhost:8080
                                │                          │
                                ▼                          ▼
                      ┌──────────────── Ingress (Traefik) ─────────────────┐
                      │                                                     │
   /            /api/users       /api/books      /api/stats     /api/status        (host rule)
   ▼               ▼                ▼               ▼              ▼                  ▼
 React UI      Node.js API      Java API       Python API     Go status board     Laravel admin
 (nginx)       (Express)        (Spring Boot)  (FastAPI)      (checks everyone)   (nginx + PHP-FPM)
                   │                │               │                                 │
                   └────────────────┴───────┬───────┴─────────────────────────────────┘
                                            ▼
                         PostgreSQL 18 (StatefulSet + persistent volume)
                                            ▲
                    report-worker (plain JavaScript): a CronJob that writes reports
```

**Kubernetes does not care which language a container was written in.** It manages containers: an image, a port,
environment variables, health endpoints, signals, exit codes, logs on stdout. That is the lesson this lab makes
concrete, seven times.

**Every command is tested.** The lessons run automatically, every application on Docker, the platform on Docker
Compose and on a real Kubernetes cluster (kind) in GitHub Actions. The outputs shown in the lessons are the real
outputs of those runs ([tests/](tests/README.md)).

## 1. Who it is for

You know basic terminal commands and have run a container before (if not: start with Docker basics). You have never
deployed several applications to Kubernetes, and YAML files full of `selector`, `targetPort` and `readinessProbe` still
look like magic. No knowledge of the seven languages is needed: you read the code, you don't write it.

## 2. What you will learn

- How applications in **Node.js, React, Python, Go, Java, PHP/Laravel and plain JavaScript** are containerised, and why
  their Dockerfiles differ (interpreted vs compiled, multi-stage builds, image sizes from 16 MB to 348 MB)
- JavaScript (the language) vs Node.js (a runtime); server vs batch job; the React build vs dev server
- **Docker Compose**: services, networks, volumes, environment, service discovery, health-aware dependencies
- **From Compose to Kubernetes**: what every Compose line becomes, and why it is not a mechanical conversion
- Deployments, Pods, Services, ConfigMaps, Secrets, StatefulSets, PersistentVolumeClaims, Jobs, CronJobs, Ingress,
  multi-container Pods
- **Health probes** (startup, liveness, readiness), **resources** (requests, limits, OOMKilled)
- **Scaling, rolling updates, rollbacks**, with versioned image tags
- **Troubleshooting**: twelve realistic failures, from a wrong image name to a frontend that cannot reach its backend

## 3. Prerequisites

| Tool | Version used | Install |
|---|---|---|
| Docker (Desktop on Windows/macOS, Engine on Linux) with Compose v2 | 29.x | <https://docs.docker.com/get-docker/> |
| kind | v0.33.0 | Windows: `winget install Kubernetes.kind` · macOS: `brew install kind` · Linux: [binary](https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries) |
| kubectl | v1.37 | Windows: `winget install Kubernetes.kubectl` · macOS: `brew install kubectl` · Linux: [binary](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) |
| Helm | v3 or v4 | Windows: `winget install Helm.Helm` · macOS: `brew install helm` · Linux: [script](https://helm.sh/docs/intro/install/) |
| Git, a bash shell (Linux/macOS terminal, WSL2 or Git Bash on Windows), curl, Python 3 | | |

About 8 GB of free memory for the whole platform on kind, and 10 GB of disk for the images. No cloud account.
No language toolchains (Node, Python, Go, JDK, PHP) are needed: every build runs inside Docker.

## 4. The roadmap

| Level | Goal | Where |
|---|---|---|
| 1 | Understand the architecture | [docs/01](docs/01-architecture.md), [docs/02](docs/02-why-multiple-stacks.md), [the contract](docs/CONTRACT.md) |
| 2 | Build the applications | [applications/](applications/README.md) (read the code of each) |
| 3 | Dockerize every application | each application's lesson, [docs/03](docs/03-dockerfiles-across-stacks.md), [docs/04](docs/04-images-tags-and-registries.md) |
| 4 | Run containers individually | each application's lesson |
| 5 | Docker Compose | [compose/](compose/README.md) |
| 6 | Understand the Compose architecture | [docs/05](docs/05-docker-compose.md) |
| 7 | Convert Compose concepts to Kubernetes | [docs/06](docs/06-compose-to-kubernetes.md), [kubernetes/00](kubernetes/00-cluster.md), [01](kubernetes/01-foundation.md) |
| 8 | Deploy Node.js | [kubernetes/02](kubernetes/02-node-api.md) |
| 9 | Deploy React | [kubernetes/03](kubernetes/03-frontend.md) |
| 10 | Deploy Python | [kubernetes/04](kubernetes/04-python-api.md) |
| 11 | Deploy Go | [kubernetes/05](kubernetes/05-go-status.md) |
| 12 | Deploy Java | [kubernetes/06](kubernetes/06-java-api.md) |
| 13 | Deploy Laravel (and the JavaScript worker) | [kubernetes/07](kubernetes/07-laravel-admin.md), [08](kubernetes/08-report-worker.md), [docs/14](docs/14-jobs-and-cronjobs.md), [docs/15](docs/15-multi-container-pods.md) |
| 14 | Networking, Services, Ingress | [kubernetes/09](kubernetes/09-ingress.md), [docs/11](docs/11-services-networking-and-ingress.md) |
| 15 | ConfigMaps and Secrets | [kubernetes/10](kubernetes/10-config-and-secrets.md), [docs/07](docs/07-configmaps-and-secrets.md) |
| 16 | Health checks | [kubernetes/11](kubernetes/11-health-probes.md), [docs/08](docs/08-health-probes.md) |
| 17 | Storage | [kubernetes/12](kubernetes/12-storage.md), [docs/10](docs/10-storage-and-databases.md) |
| 18 | Resources, scaling, rolling updates, rollbacks | [kubernetes/13](kubernetes/13-resources.md), [14](kubernetes/14-scaling-rolling-updates.md), [docs/09](docs/09-resources-requests-and-limits.md), [docs/12](docs/12-scaling-rolling-updates-rollbacks.md) |
| 19 | Troubleshooting | [troubleshooting/](troubleshooting/README.md), [docs/13](docs/13-logging-and-debugging.md) |
| 20 | The complete multi-stack platform | [capstone/](capstone/README.md) |

**Start here:** the guided [tutorial](tutorial/README.md) walks you through the twenty levels in order, like a senior
engineer sitting next to you. To revise or read offline: the [study guide PDF](study/study-guide.pdf), with the
[glossary](study/glossary.md) and [25 interview questions](study/interview-questions.md).

Practical challenges come after every major section: in each application lesson, in the Compose lesson, and in
[labs/](labs/README.md).

## 5. Repository structure

```text
.
├── applications/   7 applications, each with its Dockerfile(s) and a tested lesson
├── compose/        docker-compose.yml for the whole platform + the Compose lesson
├── kubernetes/     manifests per application + 15 tested lessons (cluster → scaling → cleanup)
├── docs/           15 concept lessons + the service contract
├── troubleshooting/ 12 failures: break it, investigate, fix, verify
├── labs/           practical challenges with hidden solutions
├── capstone/       the complete platform, verified by one script
├── tutorial/       the guided course: 14 chapters through the repository, level by level
├── study/          glossary, 25 interview questions, the printable study guide (PDF)
└── tests/          the runner that executes every lesson (mdrun.py), link checker, screenshot helper
```

## 6. Versions (checked against the official registries)

| Component | Version |
|---|---|
| Node.js / Express / pg | 24 LTS / 5.2 / 8.23 |
| React / Vite | 19.3 / 8.3 |
| Python / FastAPI / uvicorn / psycopg | 3.14 / 0.142 / 0.54 / 3.3 |
| Go | 1.27 (standard library only) |
| Java / Spring Boot | 25 LTS (Temurin) / 4.1.1 |
| PHP / Laravel | 8.5 / 13 |
| PostgreSQL | 18.6 |
| nginx (unprivileged) | 1.30 |
| Kubernetes (kind node image) / kind | 1.37.0 / v0.33.0 |
| Traefik (Helm chart) | v3.7 (41.6.1) |

## 7. Images and registry

Local images are named `<service>:<version>` (for example `node-api:1.0.0`) and copied into the kind cluster with
`kind load docker-image`. CI publishes the same images to GitHub Container Registry as
`ghcr.io/sufyanahmadkamboh/bookshop-<service>:<version>`. Never `latest`: [docs/04](docs/04-images-tags-and-registries.md).

## 8. License

[MIT](LICENSE). Node.js, React, Python, Go, Java, Spring, PHP, Laravel, PostgreSQL, nginx, Traefik, Docker and
Kubernetes are trademarks of their respective owners.
