# Troubleshooting labs

> Level 19 of the [roadmap](../README.md). You need the complete platform from the
> [Kubernetes lessons](../kubernetes/README.md), running in the namespace `bookshop` (the current namespace of your
> kubectl context).

Each lab **breaks one thing on purpose**, shows the symptom exactly as you would meet it at work, and walks through the
investigation. Every lab ends by restoring the platform, so you can do them in any order, and repeat them. All outputs
are real: they were recorded while the labs ran against the lab cluster.

```text
Break it → Problem → Symptoms → Investigation → Commands → Root cause → Fix → Verification → Lesson learned
```

| # | Lab | What breaks | Typical symptom | Key commands |
|---|---|---|---|---|
| 01 | [Wrong image name](01-wrong-image-name.md) | a typo in the image name (go-status) | `ImagePullBackOff` | `describe pod`, `get events` |
| 02 | [Image pull failure](02-image-pull-failure.md) | an image built locally but never given to the cluster (python-api) | `ImagePullBackOff` with a correct name | `docker images`, `crictl images` on the node |
| 03 | [Wrong container port](03-wrong-container-port.md) | the app listens on another port than the manifest says (node-api) | Running, `0/1`, restarts | `get events`, `exec ... wget 127.0.0.1` |
| 04 | [Service selector mismatch](04-service-selector-mismatch.md) | a typo in the Service selector (node-api) | Ingress 503, healthy Pods | `get endpointslices`, `--show-labels` |
| 05 | [Application crashes](05-application-crashes.md) | a wrong start command (node-api) | `CrashLoopBackOff` | `logs --previous`, `describe` → Last State |
| 06 | [Missing environment variable](06-missing-environment-variable.md) | `DB_PASSWORD` removed (python-api) | `CrashLoopBackOff` with a clear message | `logs --previous`, the env list |
| 07 | [Database connection failure](07-database-connection-failure.md) | `DB_HOST` typo in the ConfigMap (node-api) | Running, `0/1`, no restarts | `/ready` from inside, `printenv` |
| 08 | [Readiness probe failure](08-readiness-probe-failure.md) | readiness path typo (python-api) | stuck rollout, `0/1` | `rollout status`, probe events |
| 09 | [Volume problem](09-volume-problem.md) | a claim with a non-existent StorageClass | `Pending` | Pod events, `describe pvc`, `get storageclass` |
| 10 | [Works in the Pod, not through the Service](10-works-in-pod-not-through-service.md) | wrong `targetPort` (python-api) | Ingress 502 | hop-by-hop tests, `describe service` |
| 11 | [Frontend cannot reach a backend](11-frontend-cannot-reach-backend.md) | the java-api Service port changed | UI panel error, 502 from the wrong component | `curl -i` headers, `describe ingress` |
| 12 | [Incorrect Secret](12-incorrect-configmap-secret.md) | a "rotated" password the database doesn't know | Running, `0/1` | `/ready`, checksum comparison |

## The method

```text
 1. What exactly is the symptom?          kubectl get pods (STATUS, READY, RESTARTS) · curl -i through the Ingress
 2. What does Kubernetes know?            kubectl describe pod / service / ingress · kubectl get events
 3. What does the application say?        kubectl logs [--previous] · its /health and /ready answers
 4. Which hop fails?                      inside the Pod (127.0.0.1) → through the Service → through the Ingress
 5. Change one thing, then verify         the command that showed the symptom must now show it fixed
```

| Status | First command | Usual causes |
|---|---|---|
| `Pending` | `kubectl describe pod` (Events) | no node with enough CPU/memory, unbound volume claim, taints |
| `ErrImagePull` / `ImagePullBackOff` | `kubectl describe pod` / events | wrong name or tag, image not in a reachable registry, missing pull credentials |
| `CreateContainerConfigError` | `kubectl describe pod` | a referenced ConfigMap/Secret or key does not exist |
| `CrashLoopBackOff` | `kubectl logs <pod> --previous` | the program exits: bad command, missing configuration, crash at startup |
| `Running` but `0/1` | events (readiness probe), `/ready` | dependency down, wrong probe path/port, app listens elsewhere |
| `Running`, `1/1`, but unreachable | `kubectl get endpointslices`, `describe service` | selector mismatch, wrong `targetPort`, Ingress rule |
| `OOMKilled` (exit 137) | `kubectl describe pod` → Last State | memory limit too low ([kubernetes/13](../kubernetes/13-resources.md)) |

The command reference is in [docs/13 · Logging and debugging](../docs/13-logging-and-debugging.md).
