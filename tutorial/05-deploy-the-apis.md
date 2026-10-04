# 05 · Deploy the APIs

> Goal: four APIs in four languages run on Kubernetes, with the same pattern. Levels 8, 10, 11 and 12 of the
> [roadmap](../README.md#4-the-roadmap). Time: about 75 minutes.

## Before you start

Lessons 00 and 01 passed: the cluster, Traefik, the namespace, the ConfigMap, the Secrets and PostgreSQL exist.

## The walk

### 1. node-api: the pattern, in detail (kubernetes/02)

Run [kubernetes/02-node-api.md](../kubernetes/02-node-api.md). This lesson explains every important line of a
Deployment once; the following lessons only point out what is different. Watch for:

- **`kind load docker-image`**: the cluster's nodes have their own image store. An image in your Docker is not an
  image in the cluster until you load it (or push it to a registry). Troubleshooting lab 02 is about forgetting this.
- **Pods vs Service:** two Pods with their own IPs, one Service with a stable name. The endpoints are the IPs of the
  Ready Pods:

  ```text
  10.244.1.5:3000,10.244.1.6:3000
  ```

- **Logs from all Pods at once**, with `-l app=node-api --prefix`: each line tells you which Pod wrote it.

### 2. python-api: the same YAML, another language (kubernetes/04)

Run [kubernetes/04-python-api.md](../kubernetes/04-python-api.md) (the frontend, lesson 03, comes in the next
chapter; you can also run them in number order). The `diff` at the start of the lesson is the point: apart from the
name, image, port, user ID and resource numbers, the Python Deployment is the Node.js Deployment. Note the statistics:

```text
{"users":3,"books":0,"reviews":0,"latest_report":null}
```

`books` and `reviews` are 0 because their owners are not deployed yet. python-api treats a missing table as 0
instead of crashing: designing for partial availability.

### 3. go-status: names as service discovery (kubernetes/05)

Run [kubernetes/05-go-status.md](../kubernetes/05-go-status.md). Its configuration is a list of Service **names**.
At this point it reports what exists and what does not:

```text
4 of 6 services up
  frontend       up    200
  go-status      up    200
  java-api       down
  laravel-admin  down
  node-api       up    200
  python-api     up    200
```

(4 of 6 if you ran the frontend lesson before; the down ones are not deployed yet.) Then the distroless surprise:
`kubectl exec ... sh` fails with `exec: "sh": executable file not found in $PATH`. No shell in the image is a feature.

### 4. java-api: the slow starter (kubernetes/06)

Run [kubernetes/06-java-api.md](../kubernetes/06-java-api.md). The startup probe in action, from the Pod's events:

```text
Startup probe failed: Get "http://10.244.1.12:8080/health": dial tcp 10.244.1.12:8080: connect: connection refused
```

That warning is expected: the JVM was still starting. The startup probe gives it up to 60 seconds; only after it
succeeds do liveness and readiness start. Without it, a liveness probe could kill Java before it ever finished
starting, again and again.

## Expert commentary

- **Read events, not just status.** `kubectl describe pod` ends with the events: probe failures, image pulls,
  scheduling decisions. Most debugging in chapter 11 starts there.
- **`imagePullPolicy: IfNotPresent` + a versioned tag** is the correct pair. With `latest`, Kubernetes defaults to
  `Always` and you never know which build a node runs.
- **Interview angle:** "Your Java service gets restarted during startup in production. Why, and what do you do?"
  A liveness probe that starts too early; add a startupProbe sized from measured start times (like the
  `cpus=0.5` number from chapter 02), not a long `initialDelaySeconds` that also delays detecting real hangs.

## Checkpoint

- [ ] node-api, python-api, go-status and java-api are `Available`.
- [ ] You can explain Pod IPs vs Service vs endpoints with the output of `kubectl get endpoints node-api`.
- [ ] You saw the startup probe warning for java-api and can explain why it is harmless there.
- [ ] You can say why `kubectl exec` into go-status fails.

Next: [06 · Deploy the frontend](06-deploy-the-frontend.md)
