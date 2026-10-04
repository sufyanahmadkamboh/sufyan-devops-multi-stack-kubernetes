# 08 · Readiness probe failure

> Time: 10 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

An update of python-api's manifest changes the readiness path to `/readyz` (another project's convention). The
application only has `/ready`.

<!-- test: contains=deployment.apps/python-api patched -->
```bash
kubectl patch deployment python-api --type json -p '[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/readyz"}]'
```

<!-- test-run: sleep 20 -->

## Problem

The rollout of python-api hangs. Nothing is down, but nothing moves either.

## Symptoms

<!-- test: retry=30; contains=0/1; output -->
```bash
kubectl get pods -l app=python-api
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
python-api-54c69f569b-2wcr5   1/1     Running   0          2m14s
python-api-54c69f569b-tht6x   1/1     Running   0          2m20s
python-api-8684996bd6-slfnn   0/1     Running   0          21s
```

<!-- test: contains=Waiting for deployment; output -->
```bash
kubectl rollout status deployment/python-api --timeout=5s 2>&1 || true
```

```text
Waiting for deployment "python-api" rollout to finish: 1 out of 2 new replicas have been updated...
error: timed out waiting for the condition
```

## Investigation

A Pod that runs but never becomes Ready: what does its readiness probe call, and what does it get back?

## Commands

<!-- test: retry=15; contains=statuscode: 404; output -->
```bash
NEW=$(kubectl get pods -l app=python-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl get events --field-selector involvedObject.name=${NEW#pod/},reason=Unhealthy | tail -2
kubectl describe $NEW | grep Readiness
```

```text
25s         Warning   Unhealthy   pod/python-api-8684996bd6-slfnn   Readiness probe failed: Get "http://10.244.1.106:8000/readyz": dial tcp 10.244.1.106:8000: connect: connection refused
5s          Warning   Unhealthy   pod/python-api-8684996bd6-slfnn   Readiness probe failed: HTTP probe failed with statuscode: 404
    Readiness:  http-get http://:http/readyz delay=0s timeout=1s period=5s successThreshold=1 failureThreshold=2
  Warning  Unhealthy  25s (x2 over 25s)  kubelet            spec.containers{python-api}: Readiness probe failed: Get "http://10.244.1.106:8000/readyz": dial tcp 10.244.1.106:8000: connect: connection refused
  Warning  Unhealthy  5s (x4 over 20s)   kubelet            spec.containers{python-api}: Readiness probe failed: HTTP probe failed with statuscode: 404
```

The same request by hand, from another Pod, through the Service:

<!-- test: contains=404; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/readyz 2>&1 || true
kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/ready; echo
```

```text
wget: server returned error: HTTP/1.1 404 Not Found
command terminated with exit code 1
{"status":"ready","service":"python-api","version":"1.0.0"}
```

## Root cause

The probe asks for `/readyz`, which returns 404; the application's readiness endpoint is `/ready`. A probe counts
every status from 200 to 399 as success and everything else as failure, so the new Pods never become Ready and the
rolling update waits forever. The old Pods keep serving: users notice nothing, which is exactly why a stuck rollout can
stay unnoticed for days.

## Fix

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout undo deployment/python-api
kubectl rollout status deployment/python-api --timeout=240s
```

## Verification

<!-- test: retry=30; contains=/ready; absent=0/1; absent=Terminating; output -->
```bash
kubectl get pods -l app=python-api
kubectl describe deployment python-api | grep Readiness
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
python-api-54c69f569b-2wcr5   1/1     Running   0          2m22s
python-api-54c69f569b-tht6x   1/1     Running   0          2m28s
    Readiness:  http-get http://:http/ready delay=0s timeout=1s period=5s successThreshold=1 failureThreshold=2
```

## Lesson learned

- A stuck rollout (`rollout status` keeps waiting) with Pods at `0/1` → the readiness probe.
- Probe paths and ports are part of the contract between the application and the manifest; test them like code.
- In CI/CD, `kubectl rollout status --timeout=...` makes a stuck rollout fail the pipeline instead of hanging silently.
