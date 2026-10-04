# 13 · Resources: requests, limits, and OOMKilled

> Part of level 18 of the [roadmap](../README.md). Time: 15 minutes. The concepts: [docs/09](../docs/09-resources-requests-and-limits.md).

Every container in the lab declares what it needs (**requests**: the scheduler reserves this) and the most it may
use (**limits**: CPU above the limit is throttled, memory above the limit gets the container killed).

<!-- test: contains=java-api; contains=512Mi; output -->
```bash
kubectl get deployments -o custom-columns='NAME:.metadata.name,CPU-REQ:.spec.template.spec.containers[*].resources.requests.cpu,MEM-REQ:.spec.template.spec.containers[*].resources.requests.memory,CPU-LIM:.spec.template.spec.containers[*].resources.limits.cpu,MEM-LIM:.spec.template.spec.containers[*].resources.limits.memory'
```

```text
NAME            CPU-REQ   MEM-REQ     CPU-LIM     MEM-LIM
frontend        10m       32Mi        200m        128Mi
go-status       10m       16Mi        200m        64Mi
java-api        250m      256Mi       1           512Mi
laravel-admin   10m,50m   32Mi,64Mi   200m,500m   128Mi,256Mi
node-api        50m       64Mi        500m        256Mi
python-api      50m       96Mi        500m        256Mi
```

What the worker node has reserved for all of them:

<!-- test: contains=Allocated resources; output -->
```bash
kubectl describe node bookshop-worker | sed -n '/Allocated resources:/,/Events:/p' | head -8
```

```text
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests    Limits
  --------           --------    ------
  cpu                740m (5%)   5300m (37%)
  memory             930Mi (5%)  2752Mi (17%)
  ephemeral-storage  0 (0%)      0 (0%)
  hugepages-1Gi      0 (0%)      0 (0%)
```

## Step 1 · A memory limit that is too small

Give python-api a memory limit of 24 MiB. Python with FastAPI needs more than that just to start:

<!-- test: contains=resource requirements updated -->
```bash
kubectl set resources deployment python-api --limits=memory=24Mi --requests=memory=24Mi
```

<!-- test: retry=60; contains=OOMKilled; output -->
```bash
kubectl get pods -l app=python-api
kubectl get pods -l app=python-api -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.status.containerStatuses[0].lastState.terminated.reason}{" exit "}{.status.containerStatuses[0].lastState.terminated.exitCode}{"\n"}{end}'
```

```text
NAME                          READY   STATUS    RESTARTS     AGE
python-api-54c69f569b-dwlkk   1/1     Running   0            4m35s
python-api-54c69f569b-fkbk2   1/1     Running   0            4m35s
python-api-798f8bf4fb-82h5h   0/1     Running   1 (1s ago)   2s
python-api-54c69f569b-dwlkk   exit 
python-api-54c69f569b-fkbk2   exit 
python-api-798f8bf4fb-82h5h  OOMKilled exit 137
```

`OOMKilled`, exit code 137 (128 + signal 9): the kernel killed the process when it went over its limit, and Kubernetes
restarts it (`CrashLoopBackOff` after a few attempts).

## Step 2 · Nobody noticed

<!-- test: retry=10; contains="users"; output -->
```bash
curl -s http://bookshop.localhost:8080/api/stats; echo
kubectl get pods -l app=python-api
```

```text
{"users":4,"books":5,"reviews":3,"latest_report":{"id":2,"created_at":"2026-10-04T18:20:01.436166+00:00","users":3,"books":5,"reviews":3,"services_up":6,"services_total":6}}
NAME                          READY   STATUS    RESTARTS     AGE
python-api-54c69f569b-dwlkk   1/1     Running   0            4m36s
python-api-54c69f569b-fkbk2   1/1     Running   0            4m36s
python-api-798f8bf4fb-82h5h   0/1     Running   1 (2s ago)   3s
```

The statistics still work. `set resources` started a **rolling update**: the new Pod could never become Ready, so
Kubernetes never removed the old ones. A bad change stopped at the first new Pod. That is the safety net of rolling
updates: [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md).

<!-- test: contains=Waiting for deployment; output -->
```bash
kubectl rollout status deployment/python-api --timeout=5s 2>&1 || true
```

```text
Waiting for deployment "python-api" rollout to finish: 1 out of 2 new replicas have been updated...
error: timed out waiting for the condition
```

## Step 3 · Roll back

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout undo deployment/python-api
kubectl rollout status deployment/python-api --timeout=240s
```

<!-- test: contains=256Mi; output -->
```bash
kubectl get deployment python-api -o jsonpath='{.spec.template.spec.containers[0].resources}'; echo
```

```text
{"limits":{"cpu":"500m","memory":"256Mi"},"requests":{"cpu":"50m","memory":"96Mi"}}
```

The previous version of the Pod template, with the 256Mi limit, is back. Next: deliberate updates and scaling,
[14 · Scaling, rolling updates, rollbacks](14-scaling-rolling-updates.md).
