# 13 · Knowledge check

> Time: about 30 minutes. Answer without notes first.

## Skills checklist

Tick only what you can do **without looking it up**.

| Level | I can... |
|---|---|
| 1 | draw the Bookshop platform and explain why it uses seven stacks |
| 2 | explain the service contract and why every service follows it |
| 3 | write a Dockerfile for an interpreted, a compiled and a static-web application, multi-stage where useful |
| 4 | run a container with environment variables, a network and a port, and read its logs |
| 5 | run a multi-service platform with Docker Compose, with health-aware start order |
| 6 | explain Compose networks, volumes, `.env`, profiles and one-off services |
| 7 | map every Compose block to a Kubernetes resource and create a kind cluster with an ingress controller |
| 8–12 | deploy an API in any language: image into the cluster, Deployment, Service, probes, resources |
| 13 | choose between Deployment, Job and CronJob, and put two containers in one Pod when they belong together |
| 14 | route a host and several paths to Services with an Ingress, and trace a request to a Pod |
| 15 | use ConfigMaps and Secrets, and roll a Deployment to pick up a change |
| 16 | design liveness, readiness and startup probes, and predict what each failure does |
| 17 | keep data in a StatefulSet's volume claim and explain what survives what |
| 18 | set requests and limits, recognise OOMKilled, scale, update and roll back |
| 19 | diagnose image, crash, readiness, Service and scheduling failures from the status column |
| 20 | deploy and verify the whole platform from scratch, and fix it under pressure |

## Self-test

<details><summary>1. What does Kubernetes need to know about an application to run it?</summary>

The image, the port it listens on, its configuration (environment variables), how to check that it is alive and ready
(health endpoints), how much CPU and memory it needs, and that it stops on SIGTERM. Not its language. ([docs/02](../docs/02-why-multiple-stacks.md))
</details>

<details><summary>2. JavaScript or Node.js: which one is a runtime?</summary>

Node.js. JavaScript is the language; Node.js runs it outside the browser. In this course JavaScript runs in the
browser (React), in a server (node-api) and in a batch job (report-worker). ([docs/02](../docs/02-why-multiple-stacks.md))
</details>

<details><summary>3. Why is go-status's image 16.4 MB and java-api's 348 MB?</summary>

Go compiles to a static binary that needs no runtime, so the final image can be distroless. Java compiles to bytecode
that needs a JVM in the image. Multi-stage builds leave the build tools out in both cases. ([docs/03](../docs/03-dockerfiles-across-stacks.md))
</details>

<details><summary>4. Why never `latest`?</summary>

It is a moving pointer: you cannot tell which build runs, nodes may run different builds, and "roll back to the
previous version" has nothing to point to. Versioned, immutable tags make deployments predictable and rollbacks
possible. ([docs/04](../docs/04-images-tags-and-registries.md))
</details>

<details><summary>5. What does `depends_on: {condition: service_healthy}` give you that plain `depends_on` does not?</summary>

Plain `depends_on` waits only until the other container started. With the condition, Compose waits until its health
check passes, so the application inside is actually ready. ([compose/README.md](../compose/README.md))
</details>

<details><summary>6. What does a Compose service usually become in Kubernetes?</summary>

A Deployment (plus a Service if others call it). A database becomes a StatefulSet; a one-off task a Job; a scheduled
task a CronJob. ([docs/06](../docs/06-compose-to-kubernetes.md))
</details>

<details><summary>7. How does Kubernetes replace `depends_on`?</summary>

It doesn't order starts. Readiness probes keep a Pod out of traffic until its dependencies answer, and applications
retry their connections. ([docs/06](../docs/06-compose-to-kubernetes.md))
</details>

<details><summary>8. Why does the cluster need `kind load docker-image`?</summary>

The kind nodes have their own image store, separate from your Docker. Without loading the image (or pushing it to a
registry), the node tries to pull it from Docker Hub and fails. ([troubleshooting 02](../troubleshooting/02-image-pull-failure.md))
</details>

<details><summary>9. What are a Service's endpoints?</summary>

The IP addresses and ports of the Pods that match the Service's selector **and are Ready**. No endpoints means no
traffic, whatever the Pods' state. ([docs/11](../docs/11-services-networking-and-ingress.md))
</details>

<details><summary>10. Why do laravel-web and laravel-fpm share one Pod?</summary>

They always run and scale together, and nginx must reach exactly its own PHP-FPM; in one Pod they share the network
namespace and talk over 127.0.0.1:9000. ([docs/15](../docs/15-multi-container-pods.md))
</details>

<details><summary>11. Why do migrations run as a Job?</summary>

They must run once per release, before the application uses the new schema. Running them at startup in every replica
can run them twice at the same time. ([docs/14](../docs/14-jobs-and-cronjobs.md))
</details>

<details><summary>12. You changed a ConfigMap. Why does the application still use the old value?</summary>

Environment variables are read when the container starts. A `rollout restart` (or a change to the Pod template)
creates new Pods that read the new value. ([kubernetes/10](../kubernetes/10-config-and-secrets.md))
</details>

<details><summary>13. Is a Kubernetes Secret encrypted?</summary>

Not by itself: it is base64-encoded. It is protected by access control, by staying out of images and Git, and, when
the cluster is configured for it, by encryption at rest. ([docs/07](../docs/07-configmaps-and-secrets.md))
</details>

<details><summary>14. The database is down. What should the APIs' probes do?</summary>

Readiness fails, so the Pods leave their Services; liveness keeps passing, so nothing restarts. When the database
returns, readiness passes again. ([kubernetes/11](../kubernetes/11-health-probes.md))
</details>

<details><summary>15. Why does java-api have a startupProbe?</summary>

The JVM takes seconds to start (9.3 s measured at 0.5 CPU). The startup probe gives it time; liveness starts only
after it succeeds, so a slow start is not mistaken for a hang. ([kubernetes/06](../kubernetes/06-java-api.md))
</details>

<details><summary>16. What does exit code 137 mean?</summary>

128 + 9: the process was killed with SIGKILL, in Kubernetes typically `OOMKilled` because it exceeded its memory
limit. ([kubernetes/13](../kubernetes/13-resources.md))
</details>

<details><summary>17. Why did the bad memory limit not cause an outage?</summary>

The change started a rolling update. The new Pod never became Ready, so Kubernetes never removed the old Pods; the
rollout simply stalled. ([kubernetes/13](../kubernetes/13-resources.md))
</details>

<details><summary>18. What makes `kubectl rollout undo` work?</summary>

The Deployment keeps the previous ReplicaSet (scaled to 0) and the image it references still exists under its
version tag. Undo scales the old ReplicaSet up again. ([docs/12](../docs/12-scaling-rolling-updates-rollbacks.md))
</details>

<details><summary>19. A Pod is `Pending`. Where is the reason?</summary>

In the events (`kubectl describe pod` or `kubectl get events`), written by the scheduler or the volume controller.
No container has started, so there are no logs. ([troubleshooting 09](../troubleshooting/09-volume-problem.md))
</details>

<details><summary>20. All Deployments are Available, but the platform is broken. How?</summary>

Rolling updates keep old Pods serving while new ones fail, so the Deployments stay Available; and a Service whose
selector matches nothing breaks traffic without touching any Deployment. Check that rollouts finished and that every
Service has endpoints. ([capstone](../capstone/README.md))
</details>

## What next

- Revise with the [study guide PDF](../study/study-guide.pdf), the [glossary](../study/glossary.md) and the
  [interview questions](../study/interview-questions.md).
- Redo the [labs](../labs/README.md) without opening the solutions.
- Add an eighth service in a language the course does not cover, following the [contract](../docs/CONTRACT.md).

Back to the [course overview](README.md).
