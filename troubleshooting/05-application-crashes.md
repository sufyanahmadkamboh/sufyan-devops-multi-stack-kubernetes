# 05 · The application crashes

> Time: 10 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

The node-api manifest gets an explicit start command, with a typo in the file name (`servr.js`):

<!-- test: contains=deployment.apps/node-api patched -->
```bash
kubectl patch deployment node-api --type json -p '[{"op":"add","path":"/spec/template/spec/containers/0/command","value":["node","src/servr.js"]}]'
```

## Problem

The new node-api Pod starts and dies, again and again.

## Symptoms

<!-- test: retry=60; contains=CrashLoopBackOff; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                        READY   STATUS             RESTARTS     AGE
node-api-67dfd9488b-hpbpg   1/1     Running            0            2m25s
node-api-67dfd9488b-jqd2m   1/1     Running            0            2m24s
node-api-7766dc5869-prx4x   0/1     CrashLoopBackOff   1 (3s ago)   4s
```

`CrashLoopBackOff`: the container exits, Kubernetes restarts it, it exits again, and the delay between restarts grows
(10 s, 20 s, 40 s, ... up to 5 minutes). The old Pods keep serving.

## Investigation

`CrashLoopBackOff` is not the cause, only Kubernetes saying "this container keeps exiting". The cause is what the
program printed before it exited: the logs of the **previous** container.

## Commands

<!-- test: contains=MODULE_NOT_FOUND; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl logs $NEW --previous | grep -E 'Error|code'
```

```text
Error: Cannot find module '/app/src/servr.js'
  code: 'MODULE_NOT_FOUND',
```

<!-- test: contains=Exit Code; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl describe $NEW | grep -A5 'Last State'
kubectl get deployment node-api -o jsonpath='{.spec.template.spec.containers[0].command}'; echo
```

```text
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
      Started:      Sun, 04 Oct 2026 20:52:27 +0200
      Finished:     Sun, 04 Oct 2026 20:52:27 +0200
    Ready:          False
["node","src/servr.js"]
```

## Root cause

The container command points to a file that does not exist, `src/servr.js`. Node.js exits with code 1 and
`MODULE_NOT_FOUND`. The image is fine; the manifest overrides the image's own `CMD`.

## Fix

The previous revision of the Deployment was correct: roll back to it.

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout undo deployment/node-api
kubectl rollout status deployment/node-api --timeout=240s
```

## Verification

<!-- test: retry=30; absent=CrashLoopBackOff; absent=Error; absent=Terminating; contains=Running; output -->
```bash
kubectl get pods -l app=node-api
kubectl get deployment node-api -o jsonpath='command: {.spec.template.spec.containers[0].command}{"\n"}'
```

```text
NAME                        READY   STATUS    RESTARTS   AGE
node-api-67dfd9488b-hpbpg   1/1     Running   0          2m29s
node-api-67dfd9488b-jqd2m   1/1     Running   0          2m28s
command: 
```

<!-- test: retry=15; contains=Ada Lovelace -->
```bash
curl -s http://bookshop.localhost:8080/api/users
```

## Lesson learned

- `CrashLoopBackOff` → `kubectl logs <pod> --previous`. The current container may not have printed anything yet.
- `describe` → `Last State: Terminated`, `Exit Code`: 1 = the program failed, 137 = killed (often OOMKilled).
- `kubectl rollout undo` is the fastest way back when the previous revision was good.
