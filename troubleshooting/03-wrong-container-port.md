# 03 · Wrong container port

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

Someone sets `PORT=3001` for node-api ("3000 is used by something else on my laptop"). The application obeys and
listens on 3001. The manifest still says the container port is 3000, and the probes check port 3000.

<!-- test: contains=env updated -->
```bash
kubectl set env deployment/node-api PORT=3001
```

<!-- test-run: sleep 5; NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1); kubectl wait --for=jsonpath='{.status.phase}'=Running $NEW --timeout=120s > /dev/null; sleep 35 -->

## Problem

The new node-api Pods never become Ready, and after a while they start restarting.

## Symptoms

<!-- test: retry=45; contains=0/1; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                        READY   STATUS    RESTARTS      AGE
node-api-67dfd9488b-hpbpg   1/1     Running   0             2m13s
node-api-67dfd9488b-jqd2m   1/1     Running   0             2m12s
node-api-7655bbcc84-x57l2   0/1     Running   1 (11s ago)   41s
```

The old Pods keep serving (the rollout waits for a Ready new Pod), so `/api/users` still works through the Ingress.

## Investigation

Running but not Ready → the readiness probe fails. Why? Ask the events, then look from inside the new Pod: does the
application answer where the probe asks?

## Commands

<!-- test: retry=20; contains=connection refused; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl get events --field-selector involvedObject.name=${NEW#pod/},reason=Unhealthy | tail -3
```

```text
LAST SEEN   TYPE      REASON      OBJECT                          MESSAGE
5s          Warning   Unhealthy   pod/node-api-7655bbcc84-x57l2   Readiness probe failed: Get "http://10.244.1.100:3000/ready": dial tcp 10.244.1.100:3000: connect: connection refused
1s          Warning   Unhealthy   pod/node-api-7655bbcc84-x57l2   Liveness probe failed: Get "http://10.244.1.100:3000/health": dial tcp 10.244.1.100:3000: connect: connection refused
```

<!-- test: retry=10; contains=3001; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl logs $NEW | grep listening
kubectl exec $NEW -- wget -qO- http://127.0.0.1:3001/health; echo
kubectl exec $NEW -- wget -qO- -T 2 http://127.0.0.1:3000/health 2>&1 || true
```

```text
2026-10-04T18:52:08.410Z node-api version 1.0.0 listening on port 3001
{"status":"ok","service":"node-api","version":"1.0.0"}
wget: can't connect to remote host (127.0.0.1): Connection refused
command terminated with exit code 1
```

<!-- test: contains=3000; output -->
```bash
kubectl get deployment node-api -o jsonpath='containerPort: {.spec.template.spec.containers[0].ports[0].containerPort}{"\n"}PORT env: {.spec.template.spec.containers[0].env[?(@.name=="PORT")].value}{"\n"}'
```

```text
containerPort: 3000
PORT env: 3001
```

## Root cause

The application and the manifest disagree about the port. The application listens where its `PORT` says (3001); the
probes and the Service target the port named `http` in the manifest (3000), where nothing listens. `containerPort`
is only a description: it does not change where the process listens.

## Fix

Remove the override (the application's default, and the manifest, are 3000):

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl set env deployment/node-api PORT-
kubectl rollout status deployment/node-api --timeout=240s
```

## Verification

<!-- test: retry=30; contains=listening on port 3000; absent=0/1; output -->
```bash
kubectl get pods -l app=node-api
kubectl logs deploy/node-api | grep listening
```

```text
NAME                        READY   STATUS    RESTARTS   AGE
node-api-67dfd9488b-hpbpg   1/1     Running   0          2m16s
node-api-67dfd9488b-jqd2m   1/1     Running   0          2m15s
Found 2 pods, using pod/node-api-67dfd9488b-hpbpg
2026-10-04T18:50:06.148Z node-api version 1.0.0 listening on port 3000
```

<!-- test: retry=15; contains=Ada Lovelace -->
```bash
curl -s http://bookshop.localhost:8080/api/users
```

## Lesson learned

- The port the process listens on, `containerPort`, the probes' port and the Service's `targetPort` must all agree.
- `connection refused` from a probe means "nothing listens there", not "the app is unhealthy".
- `kubectl exec` + `wget 127.0.0.1:<port>` tests the application from inside its own Pod, without any Service.
