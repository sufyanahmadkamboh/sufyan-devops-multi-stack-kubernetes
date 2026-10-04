# 11 · Health probes in action

> Level 16 of the [roadmap](../README.md). Time: 20 minutes. The concepts: [docs/08](../docs/08-health-probes.md).

> **Liveness** answers "should Kubernetes restart this container?"
> **Readiness** answers "should this Pod receive traffic right now?"

Every API has `/health` (liveness: the process works) and `/ready` (readiness: it can also reach the database). Here
is why the difference matters.

## Step 1 · Take the database away

Scale the PostgreSQL StatefulSet to zero: the database stops.

<!-- test: timeout=180; contains=scaled -->
```bash
kubectl scale statefulset postgres --replicas=0
kubectl wait --for=delete pod/postgres-0 --timeout=120s
```

Within a few seconds the readiness probes of the database-backed APIs fail:

<!-- test: retry=60; contains=0/1; absent=1/1; output -->
```bash
kubectl get pods -l 'app in (node-api,python-api,java-api)'
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
java-api-64578ccddb-srwvq     0/1     Running   0          5m19s
node-api-6f678b5b5-kjn8h      0/1     Running   0          49s
node-api-6f678b5b5-l2dnl      0/1     Running   0          50s
python-api-54c69f569b-dwlkk   0/1     Running   0          5m46s
python-api-54c69f569b-fkbk2   0/1     Running   0          5m46s
```

`Running`, but `0/1` ready, and `RESTARTS 0`. The processes are fine (`/health` answers), so the liveness probe
does not restart them: restarting would not bring the database back, and a restart storm of every API would only
make things worse. But they cannot do their job, so the readiness probe takes them out of their Services:

<!-- test: retry=20; contains=node-api; output -->
```bash
kubectl get endpointslices -l kubernetes.io/service-name=node-api -o custom-columns='SERVICE:.metadata.labels.kubernetes\.io/service-name,READY:.endpoints[*].conditions.ready'
kubectl get events --field-selector reason=Unhealthy --sort-by=.lastTimestamp | grep node-api | tail -1
```

```text
SERVICE    READY
node-api   false,false
1s          Warning   Unhealthy   pod/node-api-6f678b5b5-kjn8h       Readiness probe failed: Get "http://10.244.1.31:3000/ready": context deadline exceeded (Client.Timeout exceeded while awaiting headers)
```

From outside, the Ingress has no Ready Pod to send `/api/users` to:

<!-- test: retry=10; contains=503; output -->
```bash
curl -s -w '\nHTTP %{http_code}\n' http://bookshop.localhost:8080/api/users
```

```text
no available server

HTTP 503
```

The status board (Go, no database) is still Ready and tells you what is wrong. Its own checks call `/health`, so it
reports the APIs as up: they are alive, just not ready.

## Step 2 · Bring the database back

<!-- test: timeout=300; contains=roll out complete -->
```bash
kubectl scale statefulset postgres --replicas=1
kubectl rollout status statefulset/postgres --timeout=240s
```

Nobody restarts the APIs: their readiness probes simply pass again, and they rejoin their Services.

<!-- test: retry=90; contains=Ada Lovelace; absent=0/1; output -->
```bash
kubectl get pods -l 'app in (node-api,python-api,java-api)'
curl -s http://bookshop.localhost:8080/api/users | head -c 90; echo
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
java-api-64578ccddb-srwvq     1/1     Running   0          5m26s
node-api-6f678b5b5-kjn8h      1/1     Running   0          56s
node-api-6f678b5b5-l2dnl      1/1     Running   0          57s
python-api-54c69f569b-dwlkk   1/1     Running   0          5m53s
python-api-54c69f569b-fkbk2   1/1     Running   0          5m53s
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T18:18:13
```

## Step 3 · A broken liveness probe

What does a liveness failure look like? Point go-status's liveness probe at a path that does not exist (a typo in
a manifest is the most common cause in real life):

<!-- test: contains=deployment.apps/go-status patched -->
```bash
kubectl patch deployment go-status --type json -p '[{"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe/httpGet/path","value":"/healthz"}]'
```

<!-- test: retry=60; contains=Liveness probe failed; output -->
```bash
kubectl get events --field-selector reason=Unhealthy --sort-by=.lastTimestamp | grep go-status | tail -2
```

```text
96s         Warning   Unhealthy   pod/go-status-b5b65b96d-pjsbs      Readiness probe failed: Get "http://10.244.1.22:8080/health": dial tcp 10.244.1.22:8080: connect: connection refused
86s         Warning   Unhealthy   pod/go-status-b5b65b96d-pjsbs      Liveness probe failed: HTTP probe failed with statuscode: 404
```

<!-- test: retry=40; contains=Killing; output -->
```bash
kubectl get events --field-selector reason=Killing --sort-by=.lastTimestamp | grep go-status | tail -1
kubectl get pods -l app=go-status
```

```text
84s         Normal   Killing   pod/go-status-b5b65b96d-pjsbs    Stopping container go-status
NAME                         READY   STATUS              RESTARTS   AGE
go-status-6ddf8dbd94-4xsd8   1/1     Running             0          85s
go-status-b5b65b96d-dl5lr    0/1     ContainerCreating   0          1s
```

After three failed checks (the `failureThreshold`), the kubelet kills the container and starts it again. With a wrong
path that repeats forever, and the restart count keeps growing. Put the manifest back:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/go-status/deployment.yaml
kubectl rollout status deployment/go-status --timeout=240s
```

The startup probe of java-api was demonstrated in [06](06-java-api.md). Next: [12 · Storage](12-storage.md).
