# 09 · Resources: requests and limits

> Time: 20 minutes

Every container in this lab declares how much CPU and memory it needs. Kubernetes uses these numbers twice: once
to **decide where a Pod runs**, and again to **stop a container from taking more than its share**.

```text
 resources:
   requests: { cpu: 50m, memory: 64Mi }    ← "reserve at least this much for me"   (used by the scheduler)
   limits:   { cpu: "500m", memory: 256Mi } ← "never let me use more than this"     (enforced by the kernel)
```

## Units

| Unit | Meaning |
|---|---|
| `1` CPU | one full CPU core (a vCPU in the cloud, a hyperthread on a laptop) |
| `100m` | 100 **milli**cores = 0.1 of a core. `250m` = a quarter of a core |
| `64Mi` | 64 mebibytes (64 × 1024 × 1024 bytes). `Mi`/`Gi` are binary units; `M`/`G` are decimal |

## What this lab asks for

Taken from the manifests in [kubernetes/](../kubernetes/):

| Container | Requests (CPU / memory) | Limits (CPU / memory) | Why this size |
|---|---|---|---|
| `frontend` (nginx) | 10m / 32Mi | 200m / 128Mi | serves static files: almost no work |
| `node-api` | 50m / 64Mi | 500m / 256Mi | a small Node.js process |
| `python-api` | 50m / 96Mi | 500m / 256Mi | Python + FastAPI + uvicorn need a bit more memory at start |
| `java-api` | 250m / 256Mi | 1 / 512Mi | the JVM: more memory, and CPU to start quickly |
| `go-status` | 10m / 16Mi | 200m / 64Mi | one small compiled binary |
| `laravel-web` (nginx) | 10m / 32Mi | 200m / 128Mi | static files + FastCGI forwarding |
| `laravel-fpm` | 50m / 64Mi | 500m / 256Mi | PHP-FPM worker processes |
| `report-worker` | 10m / 32Mi | 200m / 128Mi | runs for a few seconds, then exits |
| `postgres` | 100m / 128Mi | 1 / 512Mi | the database: room for caches |

## Requests: the scheduler's budget

The scheduler places a Pod on a node only if the node's **allocatable** resources minus the **requests** of the Pods
already there are at least the new Pod's requests. It does not look at how much the Pods *really* use.

```text
 node: 4 CPU allocatable
 ├── Pods already placed: requests add up to 3.8 CPU (even if they only use 0.5 CPU right now)
 └── new Pod requests 250m → 3.8 + 0.25 > 4 → does not fit → Pending: "Insufficient cpu"
```

So requests that are too **high** waste capacity (Pods stay `Pending` although the node is idle), and requests that
are too **low** pack too many Pods onto a node, which then fight for CPU and memory.

## Limits: what happens at the ceiling

CPU and memory behave very differently at their limit:

| Resource | At the limit | What you see |
|---|---|---|
| **CPU** | the container is **throttled**: it gets no more CPU time in that period | it runs **slower** (higher latency); it is **not** killed |
| **Memory** | the kernel's OOM killer **ends the process** | the container restarts; `kubectl describe pod` shows `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` |

Exit code 137 is 128 + 9: the process was ended with signal 9 (SIGKILL). The application gets no chance to clean up.
A container that keeps hitting its memory limit ends up in `CrashLoopBackOff`.

## Quality of Service (QoS) classes

From requests and limits, Kubernetes gives every Pod a QoS class. When a **node** runs out of memory, the kubelet
evicts Pods in this order: BestEffort first, Guaranteed last.

| QoS class | Rule | In this lab |
|---|---|---|
| **Guaranteed** | every container: requests = limits, for CPU and memory | none |
| **Burstable** | at least one request or limit set, but not Guaranteed | every Pod here |
| **BestEffort** | no requests and no limits at all | none (and it should stay that way) |

Every Pod in the lab is **Burstable**: it reserves a small amount and may use more when the node has room. That fits a
laptop. Production services often set memory request = memory limit to avoid surprises.

## Java: the heap and the container's memory limit

A JVM decides its maximum heap size when it starts. The `java-api` image starts it with:

```text
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
```

Modern JVMs read the **container's** memory limit (512Mi here) instead of the host's memory. With
`MaxRAMPercentage=75`, the heap may grow to about 75 % of 512Mi; the rest is left for the JVM's own memory (threads,
classes, the garbage collector). Raise the limit and the heap grows with it; set the percentage too high and the
process can exceed the limit and be OOMKilled.

CPU matters for the JVM as well. The [java-api lesson](../applications/java-api/README.md) measured the same image
with different CPU limits:

```text
cpus=0.5: Started BookshopApplication in 9.302 seconds
cpus=1: Started BookshopApplication in 4.607 seconds
```

That is why `java-api` has a startupProbe ([docs/08](08-health-probes.md)) and the largest CPU limit in the lab.

## Sizing for a local kind cluster

The kind cluster in this lab is two Docker containers on your computer. Its "nodes" see your computer's CPUs and
memory, so the requests above fit easily on a normal laptop. Keep the requests small: three replicas of every service
should still fit. Measure before you change numbers:

```text
kubectl top pods -n bookshop          (needs the metrics-server add-on, which kind does not install by default)
kubectl describe node <node>          → "Allocated resources": the sum of requests and limits on that node
```

## Check yourself

<details><summary>A Pod is Pending with "Insufficient memory", but the node uses only 30 % of its memory. How?</summary>

The scheduler counts **requests**, not real usage. The requests already placed on the node, plus this Pod's request,
exceed the node's allocatable memory.
</details>

<details><summary>What happens when a container reaches its CPU limit? And its memory limit?</summary>

CPU: it is throttled and runs slower, but keeps running. Memory: the process is killed (OOMKilled, exit code 137) and
the container restarts.
</details>

<details><summary>Which QoS class do the Pods of this lab have, and why?</summary>

Burstable: they set requests and limits, but the requests are lower than the limits.
</details>

<details><summary>Why does `java-api` start with `-XX:MaxRAMPercentage=75`?</summary>

So the heap is sized from the container's memory limit and leaves room for the JVM's non-heap memory. Without a
sensible setting, the JVM could grow past the limit and be OOMKilled.
</details>

<details><summary>You double the memory request of every service. What can go wrong on a small cluster?</summary>

Pods may stop fitting on the nodes: new Pods (or new replicas during a rolling update) stay Pending with
"Insufficient memory", even though the real usage hasn't changed.
</details>

Next: [10 · Storage and databases](10-storage-and-databases.md)
