# 01 · Wrong image name

> Time: 10 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md), running in the
> namespace `bookshop` (the current namespace of your context). The lab restores everything at the end.

## Break it

A colleague updates go-status and types the image name by hand. One letter is missing: `go-staus`.

<!-- test: contains=image updated -->
```bash
kubectl set image deployment/go-status go-status=go-staus:1.0.0
```

## Problem

The status board was supposed to get a routine update. Instead, the deployment never finishes.

## Symptoms

<!-- test: retry=30; contains=ImagePullBackOff; output -->
```bash
kubectl get pods -l app=go-status
```

```text
NAME                         READY   STATUS             RESTARTS   AGE
go-status-6ddf8dbd94-4xsd8   1/1     Running            0          27m
go-status-798ff9f56d-fj62r   0/1     ImagePullBackOff   0          17s
```

A new Pod hangs in `ErrImagePull` / `ImagePullBackOff`. The old Pod is still `Running` and serving: the Deployment
does not remove it until a new Pod is Ready. Users notice nothing yet, but the update is stuck:

<!-- test: contains=Waiting for deployment; output -->
```bash
kubectl rollout status deployment/go-status --timeout=5s 2>&1 || true
```

```text
Waiting for deployment "go-status" rollout to finish: 1 old replicas are pending termination...
error: timed out waiting for the condition
```

## Investigation

`ImagePullBackOff` means "the node tried to download the image, failed, and waits longer before each new attempt".
The Pod's events say why (the newest `Failed` event of the namespace). Then compare the image the Pod wants with the image you meant.

## Commands

<!-- test: retry=15; contains=pull access denied; output -->
```bash
kubectl describe pod -l app=go-status | grep -E '^\s+Image:'
kubectl get events --field-selector reason=Failed --sort-by=.lastTimestamp | grep go-staus | tail -1
```

```text
    Image:          go-status:1.0.0
    Image:          go-staus:1.0.0
6s          Warning   Failed   pod/go-status-798ff9f56d-fj62r    Failed to pull image "go-staus:1.0.0": failed to pull and unpack image "docker.io/library/go-staus:1.0.0": failed to resolve reference "docker.io/library/go-staus:1.0.0": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

<!-- test: contains=go-staus; output -->
```bash
kubectl get deployment go-status -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

```text
go-staus:1.0.0
```

## Root cause

The Deployment refers to an image that does not exist: `go-staus:1.0.0`. The node looked for it in its own image
store, did not find it, and then asked the default registry (Docker Hub, `docker.io/library/go-staus`), which has no
such repository.

## Fix

Re-apply the manifest from Git: the single source of truth for what should run.

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/go-status/deployment.yaml
kubectl rollout status deployment/go-status --timeout=240s
```

## Verification

<!-- test: retry=20; contains=go-status:1.0.0; absent=BackOff; absent=Terminating; output -->
```bash
kubectl get pods -l app=go-status
kubectl get deployment go-status -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

```text
NAME                         READY   STATUS    RESTARTS   AGE
go-status-6ddf8dbd94-4xsd8   1/1     Running   0          27m
go-status:1.0.0
```

<!-- test: retry=15; contains=6 of 6 services up -->
```bash
curl -s http://bookshop.localhost:8080/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['up']} of {d['total']} services up\")"
```

## Lesson learned

- `ErrImagePull` / `ImagePullBackOff` → `kubectl describe pod`, read `Image:` and the `Failed to pull` event.
- A rolling update protects you: the broken Pod never replaced the working one.
- Change images through the manifest in Git (or CI), not by typing names by hand; `kubectl apply` of the manifest is
  also the fastest way back.
