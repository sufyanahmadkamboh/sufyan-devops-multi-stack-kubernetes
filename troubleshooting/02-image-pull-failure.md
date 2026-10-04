# 02 · Image pull failure: "but the image is right there!"

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

Version 1.2.0 of python-api is ready: you build the image on your computer and deploy it. You forget one step.

<!-- test: timeout=900; contains=image updated -->
```bash
docker build --build-arg APP_VERSION=1.2.0 -t python-api:1.2.0 applications/python-api > /dev/null
kubectl set image deployment/python-api python-api=python-api:1.2.0
```

## Problem

"The image exists, I just built it. Why does Kubernetes say it cannot pull it?"

## Symptoms

<!-- test: retry=30; contains=ImagePullBackOff; output -->
```bash
kubectl get pods -l app=python-api
```

```text
NAME                          READY   STATUS             RESTARTS   AGE
python-api-54c69f569b-mgqzv   1/1     Running            0          4m33s
python-api-54c69f569b-tsr2b   1/1     Running            0          4m27s
python-api-8f7888c94-hvxs5    0/1     ImagePullBackOff   0          15s
```

Same status as in [lab 01](01-wrong-image-name.md), but this time the name is spelled correctly.

## Investigation

Where is the image, exactly? There are two separate image stores: Docker's on your computer (where `docker build` and
`docker tag` put images), and the container runtime's **inside each Kubernetes node**. A node only knows images
that were pulled from a registry or loaded into it.

## Commands

On your computer:

<!-- test: contains=1.2.0; output -->
```bash
docker images python-api --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}'
```

```text
REPOSITORY   TAG       IMAGE ID
python-api   1.2.0     da8670f544dc
python-api   1.0.0     ba729f27214a
```

Inside the node that runs the Pods (a kind node is a container, so `docker exec` reaches its runtime, and `crictl`
lists its images):

<!-- test: contains=python-api; absent=1.2.0; output -->
```bash
docker exec bookshop-worker crictl images | grep -E 'IMAGE|python-api'
```

```text
IMAGE                                           TAG                  IMAGE ID            SIZE
docker.io/library/python-api                    1.0.0                09ef536e2e767       62MB
```

<!-- test: retry=15; contains=python-api:1.2.0; output -->
```bash
kubectl get events --field-selector reason=Failed --sort-by=.lastTimestamp | grep 'python-api:1.2.0' | tail -1
```

```text
2s          Warning   Failed   pod/python-api-8f7888c94-hvxs5    Failed to pull image "python-api:1.2.0": failed to pull and unpack image "docker.io/library/python-api:1.2.0": failed to resolve reference "docker.io/library/python-api:1.2.0": pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed
```

The node did not have `python-api:1.2.0`, so it tried the default registry, `docker.io/library/python-api`, where no
such image exists.

## Root cause

The image was never made available to the cluster. In this lab the step is `kind load docker-image`; on a real
cluster it is `docker push` to a registry the nodes can pull from (GHCR, ECR, Docker Hub), with the full registry
name in the manifest ([docs/04](../docs/04-images-tags-and-registries.md)).

## Fix

Load the image into the nodes. The kubelet retries pulls with a growing delay (up to minutes); deleting the stuck Pods
makes the Deployment create new ones immediately:

<!-- test: timeout=300; contains=python-api:1.2.0 -->
```bash
kind load docker-image python-api:1.2.0 --name bookshop 2>&1
```

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl delete pod -l app=python-api --field-selector=status.phase=Pending
kubectl rollout status deployment/python-api --timeout=240s
```

## Verification

<!-- test: retry=20; contains=python-api:1.2.0; absent=BackOff; absent=Terminating; output -->
```bash
kubectl get pods -l app=python-api
kubectl get deployment python-api -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

```text
NAME                         READY   STATUS    RESTARTS   AGE
python-api-8f7888c94-72rjk   1/1     Running   0          15s
python-api-8f7888c94-mzd8f   1/1     Running   0          8s
python-api:1.2.0
```

<!-- test: retry=15; contains="version":"1.2.0"; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/; echo
```

```text
{"service":"python-api","version":"1.2.0","language":"Python","runtime":"CPython 3.14.8","description":"Statistics for the Bookshop: counts of users, books, reviews and the latest report"}
```

Version 1.2.0 was only a rebuild of the same code for this lab. Put the manifest's version back and remove the lab image from
your computer and from the nodes (so the lab can be repeated):

```text
⚠️ DESTRUCTIVE COMMAND · removes the image tag python-api:1.2.0 from Docker and from both kind nodes.
```

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/python-api/deployment.yaml
kubectl rollout status deployment/python-api --timeout=240s
docker image rm python-api:1.2.0 > /dev/null
for n in bookshop-control-plane bookshop-worker; do docker exec $n crictl rmi docker.io/library/python-api:1.2.0 > /dev/null; done
```

## Lesson learned

- Your computer's Docker and the cluster's nodes have **separate** image stores.
- `ImagePullBackOff` with a correct name → is the image in a registry the nodes can reach (or loaded into kind)?
- `docker exec <kind-node> crictl images` shows what a kind node really has.
