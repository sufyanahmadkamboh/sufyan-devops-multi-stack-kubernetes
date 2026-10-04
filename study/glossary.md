# Glossary

Every term used in this course, in plain words. The link points to where it is explained or used.

| Term | Meaning |
|---|---|
| **.dockerignore** | A list of files Docker must not send to the build. Keeps images small and secrets out of them. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **.env file** | A file of `NAME=value` lines Compose reads for variables in `docker-compose.yml`. Holds secrets locally; never committed. [compose/README.md](../compose/README.md) |
| **Allocated resources** | The sum of all requests and limits of the Pods on a node, shown by `kubectl describe node`. [kubernetes/13](../kubernetes/13-resources.md) |
| **APP_KEY** | Laravel's encryption key, needed to sign sessions and cookies. Here it comes from a Secret. [applications/laravel-admin](../applications/laravel-admin/README.md) |
| **Base64** | A way to write any bytes as text. Kubernetes stores Secret values in base64: an encoding, not encryption. [kubernetes/10](../kubernetes/10-config-and-secrets.md) |
| **Build context** | The folder Docker sends to the builder; everything a `COPY` can use. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **Build stage** | The first part of a multi-stage Dockerfile, with compilers and package managers, whose results are copied into a small final image. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **ClusterIP** | The default Service type: a virtual IP reachable only inside the cluster. [docs/11](../docs/11-services-networking-and-ingress.md) |
| **ConfigMap** | A Kubernetes object holding non-secret configuration as key–value pairs, injected as environment variables or files. [docs/07](../docs/07-configmaps-and-secrets.md) |
| **Container** | A running instance of an image: an isolated process with its own filesystem, network and limits. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **containerPort** | The port a container listens on, declared in the Pod template; the Service's `targetPort` must match it. [troubleshooting 03](../troubleshooting/03-wrong-container-port.md) |
| **Contract (service contract)** | The rules every Bookshop service follows: PORT, /health, /ready, environment configuration, stdout logs, SIGTERM. [docs/CONTRACT.md](../docs/CONTRACT.md) |
| **CrashLoopBackOff** | A Pod status: the container keeps exiting and Kubernetes waits longer before each restart. The cause is in `kubectl logs --previous`. [troubleshooting 05](../troubleshooting/05-application-crashes.md) |
| **CronJob** | A Kubernetes object that creates a Job on a schedule (cron syntax), like report-worker every 10 minutes. [docs/14](../docs/14-jobs-and-cronjobs.md) |
| **depends_on** | A Compose setting for start order; with a `condition` it waits for health or completion. Kubernetes has no equivalent. [docs/05](../docs/05-docker-compose.md) |
| **Deployment** | A Kubernetes object that keeps a number of identical Pods running and replaces them with rolling updates. [kubernetes/02](../kubernetes/02-node-api.md) |
| **Distroless** | A base image with only what a program needs to run: no shell, no package manager. Used by go-status. [kubernetes/05](../kubernetes/05-go-status.md) |
| **DNS (cluster DNS)** | The name service that resolves Service names such as `node-api` to their IPs inside the cluster. [docs/11](../docs/11-services-networking-and-ingress.md) |
| **Docker Compose** | A tool that runs several containers from one YAML file on one machine. [compose/README.md](../compose/README.md) |
| **Dockerfile** | The recipe for an image: base image, files, commands, user, port, start command. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **Endpoints / EndpointSlice** | The list of Ready Pod IPs and ports behind a Service. Empty endpoints mean no traffic. [troubleshooting 04](../troubleshooting/04-service-selector-mismatch.md) |
| **Environment variable** | A named value given to a process at start; the way every service here is configured. [docs/CONTRACT.md](../docs/CONTRACT.md) |
| **ErrImagePull / ImagePullBackOff** | Pod statuses when a node cannot pull the image: wrong name, missing tag, or no access. [troubleshooting 01](../troubleshooting/01-wrong-image-name.md) |
| **Events** | Short messages Kubernetes records about objects: scheduling, pulls, probe failures, kills. `kubectl get events`. [docs/13](../docs/13-logging-and-debugging.md) |
| **Exit code 137** | 128 + 9: the process was killed with SIGKILL, usually OOMKilled at the memory limit. [kubernetes/13](../kubernetes/13-resources.md) |
| **Express** | A web framework for Node.js, used by node-api. [applications/node-api](../applications/node-api/README.md) |
| **FastAPI** | A Python web framework, used by python-api, served by uvicorn. [applications/python-api](../applications/python-api/README.md) |
| **GHCR** | GitHub Container Registry; CI publishes this course's images there. [docs/04](../docs/04-images-tags-and-registries.md) |
| **Graceful shutdown** | Stopping cleanly on SIGTERM (finish requests, close connections) instead of being killed. [docs/CONTRACT.md](../docs/CONTRACT.md) |
| **Headless Service** | A Service without a cluster IP (`clusterIP: None`); its name resolves directly to Pod IPs. Used for PostgreSQL. [docs/10](../docs/10-storage-and-databases.md) |
| **Health check (Compose)** | A command Compose runs to decide whether a container is healthy; maps to Kubernetes probes. [docs/05](../docs/05-docker-compose.md) |
| **Helm** | The package manager for Kubernetes; installs Traefik in this course. [kubernetes/00](../kubernetes/00-cluster.md) |
| **Image** | A packaged, read-only filesystem plus start settings, from which containers are created. [docs/04](../docs/04-images-tags-and-registries.md) |
| **Image tag** | The version part of an image name (`node-api:1.0.0`). Versioned, immutable tags make rollbacks possible. [docs/04](../docs/04-images-tags-and-registries.md) |
| **imagePullPolicy** | When a node pulls an image: `IfNotPresent` (use the local one if there) or `Always`. [docs/04](../docs/04-images-tags-and-registries.md) |
| **Ingress** | A Kubernetes object with HTTP routing rules (host, path → Service). [kubernetes/09](../kubernetes/09-ingress.md) |
| **Ingress controller** | The program that carries out Ingress rules; Traefik in this course. [docs/11](../docs/11-services-networking-and-ingress.md) |
| **JavaScript vs Node.js** | JavaScript is the language; Node.js is a runtime that runs JavaScript outside the browser. [docs/02](../docs/02-why-multiple-stacks.md) |
| **Job** | A Kubernetes object that runs Pods until a task completes successfully, like the Laravel migrations. [docs/14](../docs/14-jobs-and-cronjobs.md) |
| **kind** | "Kubernetes in Docker": runs Kubernetes nodes as Docker containers on your computer. [kubernetes/00](../kubernetes/00-cluster.md) |
| **kind load docker-image** | Copies an image from your Docker into the kind nodes' image store. [kubernetes/02](../kubernetes/02-node-api.md) |
| **kubectl** | The command-line client for the Kubernetes API. [kubernetes/README.md](../kubernetes/README.md) |
| **Label / selector** | Key–value tags on objects, and the queries that select them; how Services and Deployments find their Pods. [labs/05](../labs/05-break-the-selector.md) |
| **Laravel** | A PHP web framework, used by laravel-admin. [applications/laravel-admin](../applications/laravel-admin/README.md) |
| **Limits** | The maximum CPU (throttled above it) and memory (killed above it) a container may use. [docs/09](../docs/09-resources-requests-and-limits.md) |
| **Liveness probe** | A periodic check; when it fails repeatedly, the kubelet restarts the container. [docs/08](../docs/08-health-probes.md) |
| **Multi-container Pod** | A Pod with several containers that share network and lifecycle, like nginx + PHP-FPM. [docs/15](../docs/15-multi-container-pods.md) |
| **Multi-stage build** | A Dockerfile with several `FROM` stages; only the last one becomes the shipped image. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **Namespace** | A named group of Kubernetes objects; everything of this platform is in `bookshop`. [kubernetes/01](../kubernetes/01-foundation.md) |
| **Named volume** | Storage managed by Docker that outlives containers, like `pgdata`. [compose/README.md](../compose/README.md) |
| **Network (Compose)** | A virtual network for containers, with DNS by service name; separate networks isolate services. [docs/05](../docs/05-docker-compose.md) |
| **nginx** | A web server and reverse proxy; serves the React files and fronts PHP-FPM. [applications/frontend](../applications/frontend/README.md) |
| **NodePort** | A Service type that opens the same port on every node; Traefik listens on 30080 here. [docs/11](../docs/11-services-networking-and-ingress.md) |
| **Non-root** | Running a container as an ordinary user, enforced with `runAsNonRoot`. [docs/03](../docs/03-dockerfiles-across-stacks.md) |
| **OOMKilled** | The container went over its memory limit and the kernel killed it. [kubernetes/13](../kubernetes/13-resources.md) |
| **Pending** | A Pod that has no node yet (no resources, or an unbound volume claim); reason in the events. [troubleshooting 09](../troubleshooting/09-volume-problem.md) |
| **PersistentVolume (PV)** | A piece of storage in the cluster, created by a provisioner for a claim. [docs/10](../docs/10-storage-and-databases.md) |
| **PersistentVolumeClaim (PVC)** | A request for storage by a Pod; bound to a PersistentVolume. [kubernetes/12](../kubernetes/12-storage.md) |
| **PHP-FPM** | The process manager that runs PHP code for a web server over FastCGI (port 9000). [docs/15](../docs/15-multi-container-pods.md) |
| **Pod** | The smallest unit Kubernetes runs: one or more containers with one IP. [kubernetes/02](../kubernetes/02-node-api.md) |
| **port-forward** | `kubectl port-forward`: a temporary tunnel from your computer to a Service or Pod. [kubernetes/02](../kubernetes/02-node-api.md) |
| **Profile (Compose)** | A label that keeps a service out of `up` unless asked for, like `jobs` for report-worker. [docs/05](../docs/05-docker-compose.md) |
| **Readiness probe** | A periodic check; while it fails, the Pod gets no traffic from its Services. [docs/08](../docs/08-health-probes.md) |
| **Registry** | A server that stores images (Docker Hub, GHCR, ECR). [docs/04](../docs/04-images-tags-and-registries.md) |
| **ReplicaSet** | The object a Deployment uses to keep N Pods of one template; old ones are kept for rollbacks. [kubernetes/14](../kubernetes/14-scaling-rolling-updates.md) |
| **Replicas** | The number of identical Pods a Deployment keeps running. [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md) |
| **Requests** | The CPU and memory the scheduler reserves for a container. [docs/09](../docs/09-resources-requests-and-limits.md) |
| **Revision** | A numbered version of a Deployment's Pod template, listed by `kubectl rollout history`. [kubernetes/14](../kubernetes/14-scaling-rolling-updates.md) |
| **Rolling update** | Replacing Pods a few at a time, each new one first passing readiness, so there is no downtime. [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md) |
| **Rollback (rollout undo)** | Returning a Deployment to a previous revision. [kubernetes/14](../kubernetes/14-scaling-rolling-updates.md) |
| **Runtime configuration** | Settings read when a container starts (like the frontend's `/config.js`), so one image fits every environment. [kubernetes/03](../kubernetes/03-frontend.md) |
| **Secret** | A Kubernetes object for sensitive values, stored base64-encoded and protected by access control. [docs/07](../docs/07-configmaps-and-secrets.md) |
| **Service** | A stable name and virtual IP that load-balances to the Ready Pods matching its selector. [docs/11](../docs/11-services-networking-and-ingress.md) |
| **Service discovery** | Finding other services by name (Compose DNS, Kubernetes Service DNS) instead of by IP. [docs/01](../docs/01-architecture.md) |
| **SIGTERM** | The signal that asks a process to stop; sent by `docker stop` and by Kubernetes before killing a container. [docs/CONTRACT.md](../docs/CONTRACT.md) |
| **Spring Boot** | A Java framework for applications that run as one executable JAR, used by java-api. [applications/java-api](../applications/java-api/README.md) |
| **Startup probe** | A check that gives slow starters time; liveness and readiness wait until it succeeds. [kubernetes/06](../kubernetes/06-java-api.md) |
| **StatefulSet** | A workload with stable Pod names and one volume claim per Pod; used for PostgreSQL. [docs/10](../docs/10-storage-and-databases.md) |
| **StorageClass** | A kind of storage the cluster can provision; kind's default is `standard`. [troubleshooting 09](../troubleshooting/09-volume-problem.md) |
| **targetPort** | The Pod port a Service forwards to. [troubleshooting 10](../troubleshooting/10-works-in-pod-not-through-service.md) |
| **Traefik** | The ingress controller used in this course, installed with Helm. [kubernetes/00](../kubernetes/00-cluster.md) |
| **Vite** | The build tool that turns the React source into static files. [applications/frontend](../applications/frontend/README.md) |
