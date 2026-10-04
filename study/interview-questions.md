# Interview questions

25 questions that come up in interviews for junior and intermediate DevOps, platform and cloud roles. Answer each one
out loud first, then open the model answer. Each answer links to the lesson where you did it yourself: in an interview,
"I did this in a lab, and here is what I saw" beats any memorised definition.

## Containers and Dockerfiles

<details><summary>1. How would you containerise an application written in a language you don't know?</summary>

Find out four things: how it is built, how it is started, which port it listens on, and how it is configured. Then pick
the official runtime image, copy the dependency manifest before the source so the dependency layer is cached, run as
a non-root user, and start the process in exec form so it receives signals. A health endpoint and environment-based
configuration make it deployable anywhere. ([docs/CONTRACT.md](../docs/CONTRACT.md))
</details>

<details><summary>2. What is a multi-stage build and when is it worth it?</summary>

A Dockerfile with several `FROM` stages: early stages compile or install with full toolchains, the last stage copies
only the results into a small runtime image. It is worth it whenever a build step exists: go-status shrank from a
381 MB build image to 16.4 MB, the frontend from 334 MB to 81.8 MB. Fewer files also means fewer vulnerabilities.
([docs/03](../docs/03-dockerfiles-across-stacks.md))
</details>

<details><summary>3. Why is the order of Dockerfile instructions important?</summary>

Each instruction is a cached layer; a change invalidates that layer and every layer after it. Copying the dependency
manifest (`package-lock.json`, `requirements.txt`, `pom.xml`, `go.mod`, `composer.lock`) and installing before copying
the source means code changes do not reinstall dependencies. Builds go from minutes to seconds.
([docs/03](../docs/03-dockerfiles-across-stacks.md))
</details>

<details><summary>4. Why should images use versioned tags instead of latest?</summary>

`latest` is a moving pointer: you cannot tell which build a node runs, different nodes may run different builds, and
there is no previous version to roll back to. A versioned, immutable tag such as `node-api:1.0.0` always means the same
image, which makes deployments predictable and `rollout undo` meaningful. ([docs/04](../docs/04-images-tags-and-registries.md))
</details>

<details><summary>5. JavaScript and Node.js: what is the difference, and why does it matter for deployment?</summary>

JavaScript is a language; Node.js is a runtime that executes it outside the browser. React code runs in the user's
browser, so its container only serves files; node-api is a long-running server (a Deployment); report-worker runs once
and exits (a Job or CronJob). The same language ends up in three different Kubernetes workload types.
([docs/02](../docs/02-why-multiple-stacks.md))
</details>

## Docker Compose

<details><summary>6. What does depends_on guarantee in Docker Compose?</summary>

Without a condition, only that the other container was started first, not that its application is ready. With
`condition: service_healthy` Compose waits for the health check, and with `service_completed_successfully` for a
one-off task such as a migration to finish. It only orders startup; it does not react to later failures.
([compose/README.md](../compose/README.md))
</details>

<details><summary>7. How do containers in Compose find each other, and how can you isolate them?</summary>

Compose creates networks with built-in DNS, so a container reaches another by its service name (`http://java-api:8080`).
Services on different networks cannot even resolve each other: in this lab the frontend is not on the backend network,
so `postgres` is an unknown name for it. Networks are the first isolation layer. ([compose/README.md](../compose/README.md))
</details>

<details><summary>8. What is the difference between docker compose down and down -v?</summary>

`down` removes containers and networks; named volumes survive, so the database keeps its data. `down -v` also removes
the volumes and therefore the data. In this lab a user added before `down` was still there after `up`; `down -v` is
treated as a destructive command. ([compose/README.md](../compose/README.md))
</details>

## From Compose to Kubernetes

<details><summary>9. How do the parts of a Compose file map to Kubernetes resources?</summary>

A service becomes a Deployment (a StatefulSet for a database, a Job or CronJob for one-off work); ports become a Service
inside the cluster and an Ingress from outside; environment becomes ConfigMaps and Secrets; volumes become
PersistentVolumeClaims; health checks become probes. `depends_on` has no equivalent: readiness probes and retrying
applications replace it. ([docs/06](../docs/06-compose-to-kubernetes.md))
</details>

<details><summary>10. Why not simply convert a Compose file with a tool?</summary>

Converters produce a starting point, but the decisions that make a deployment reliable are not in the Compose file:
which probe checks what, how much CPU and memory to request, which values are secret, which workload type fits, how
storage survives. You still have to understand and review the YAML, so you need to know the mapping anyway.
([docs/06](../docs/06-compose-to-kubernetes.md))
</details>

<details><summary>11. How does a kind cluster get your locally built images?</summary>

The kind nodes are containers with their own image store, separate from your Docker. `kind load docker-image` copies
an image into every node; with `imagePullPolicy: IfNotPresent` the node uses it. Forgetting this makes the node try to
pull from Docker Hub and fail with ImagePullBackOff; on real clusters you push to a registry instead.
([troubleshooting 02](../troubleshooting/02-image-pull-failure.md))
</details>

## Workloads

<details><summary>12. When do you use a Deployment, a StatefulSet, a Job and a CronJob?</summary>

A Deployment for stateless processes that run forever (the APIs, the frontend). A StatefulSet when each Pod needs a
stable name and its own storage (PostgreSQL). A Job for a task that must run to completion once (migrations). A CronJob
for a Job on a schedule (the report worker). The choice depends on the program's lifecycle, not its language.
([docs/14](../docs/14-jobs-and-cronjobs.md))
</details>

<details><summary>13. When do two containers belong in the same Pod?</summary>

When they always run and scale together, share their lifecycle and talk over localhost: nginx in front of its own
PHP-FPM is the classic example. Containers in a Pod share the network namespace and can share volumes. If the two parts
could scale independently, they should be separate Deployments with a Service between them.
([docs/15](../docs/15-multi-container-pods.md))
</details>

<details><summary>14. How should database migrations run on Kubernetes?</summary>

Once per release, before the new version serves traffic, typically as a Job (or a pipeline step / Helm hook). Running
them at application startup in every replica can run them concurrently and corrupt or lock the schema. In this lab the
`laravel-migrate` Job runs `migrate --force --seed` and must complete before the application is rolled out.
([kubernetes/07](../kubernetes/07-laravel-admin.md))
</details>

## Networking

<details><summary>15. What is the difference between a Service and an Ingress?</summary>

A Service gives a set of Pods a stable name and virtual IP and load-balances to the Ready ones, mainly inside the
cluster. An Ingress is a set of HTTP rules (host and path to Service) for traffic from outside, carried out by an
ingress controller such as Traefik. One Ingress can route a whole platform. ([docs/11](../docs/11-services-networking-and-ingress.md))
</details>

<details><summary>16. A Service returns 503. How do you debug it?</summary>

Check its endpoints first. Empty endpoints mean either the selector matches no Pod labels or the Pods are not Ready;
compare the selector with `--show-labels` and look at readiness events. If endpoints exist, check the ports: the
Service's `targetPort` must match the port the application really listens on. ([troubleshooting 04](../troubleshooting/04-service-selector-mismatch.md),
[troubleshooting 10](../troubleshooting/10-works-in-pod-not-through-service.md))
</details>

<details><summary>17. Why do the same service names work in Compose and in Kubernetes?</summary>

Both provide DNS for service discovery: Compose resolves service names on its networks, Kubernetes resolves Service
names in the namespace (`node-api`, or fully `node-api.bookshop.svc.cluster.local`). Keeping the names identical lets
the same images and configuration values work in both. ([docs/01](../docs/01-architecture.md))
</details>

## Configuration and Secrets

<details><summary>18. Are Kubernetes Secrets encrypted?</summary>

Not inherently: the values are base64-encoded, which anyone can decode. They are protected by RBAC, by never being
in images or Git, by being mounted only into Pods that reference them, and, if the cluster is configured for it, by
encryption at rest in etcd. External secret stores add rotation and auditing. ([docs/07](../docs/07-configmaps-and-secrets.md))
</details>

<details><summary>19. You changed a ConfigMap and nothing happened. Why?</summary>

Values injected as environment variables are read when the container starts, so running Pods keep the old values.
A `kubectl rollout restart` creates new Pods that read the new values. Mounted ConfigMap files update after a delay,
but the application must re-read them. ([kubernetes/10](../kubernetes/10-config-and-secrets.md))
</details>

## Probes and resources

<details><summary>20. Explain liveness, readiness and startup probes.</summary>

Liveness asks "should this container be restarted?"; readiness asks "should this Pod receive traffic now?"; a startup
probe protects slow starters by delaying the other two until it succeeds. In this lab `/health` (process alive) is the
liveness check, `/ready` (database reachable) the readiness check, and java-api has a startup probe because the JVM
needed 9.3 s at 0.5 CPU. ([docs/08](../docs/08-health-probes.md))
</details>

<details><summary>21. What happens to your APIs when the database goes down, if the probes are designed well?</summary>

Readiness fails, so the Pods leave their Services and the Ingress answers 503 quickly instead of timing out; liveness
keeps passing, so no Pod restarts. When the database returns, readiness passes and traffic resumes without any
restart. A liveness probe that checked the database would cause a restart storm instead. ([kubernetes/11](../kubernetes/11-health-probes.md))
</details>

<details><summary>22. What are requests and limits, and what happens when a limit is exceeded?</summary>

Requests are what the scheduler reserves on a node; limits are the maximum. Above the CPU limit a container is
throttled (slower); above the memory limit it is killed (`OOMKilled`, exit code 137). Requests should match real usage,
limits leave headroom; JVMs need their heap sized to fit the limit. ([docs/09](../docs/09-resources-requests-and-limits.md))
</details>

## Operations and troubleshooting

<details><summary>23. How does a rolling update protect you from a bad release?</summary>

New Pods are added and old ones removed step by step, and each new Pod must pass its readiness probe first. If the new
version never becomes Ready (crash, OOM, wrong probe, missing image), the rollout stalls and the old Pods keep serving.
In this lab a memory limit that was too small caused no outage. The stalled rollout must still be noticed and fixed.
([kubernetes/13](../kubernetes/13-resources.md))
</details>

<details><summary>24. How do you roll back a Deployment, and what makes it possible?</summary>

`kubectl rollout undo` returns to the previous revision: the Deployment keeps old ReplicaSets at zero replicas and
scales one up again. It works because the old image still exists under its version tag. Afterwards, update the
manifest in Git, or the next apply re-deploys the bad version. ([kubernetes/14](../kubernetes/14-scaling-rolling-updates.md))
</details>

<details><summary>25. A Pod is not working. What is your first command, depending on its status?</summary>

`ImagePullBackOff` → `kubectl describe pod` (the event names the image). `CrashLoopBackOff` → `kubectl logs --previous`.
`Running` but `0/1` → probe events and the readiness endpoint. Ready but unreachable → `kubectl get endpoints` and the
ports. `Pending` → events (resources or volume claims). The status column decides where to look.
([docs/13](../docs/13-logging-and-debugging.md), [troubleshooting](../troubleshooting/README.md))
</details>
