# Cleanup

> Time: 2 minutes.

Two levels, depending on whether you want to keep the cluster.

## Level 1 · Remove the platform, keep the cluster

```text
⚠️ DESTRUCTIVE COMMAND · deletes the namespace bookshop and everything in it, including the database volume.
```

<!-- test: timeout=600; contains=namespace "bookshop" deleted -->
```bash
kubectl delete namespace bookshop
```

<!-- test: absent=bookshop -->
```bash
kubectl get namespaces
kubectl config set-context --current --namespace=default > /dev/null
```

Deleting a namespace deletes every object in it: Deployments, Services, the StatefulSet, the claims and their volumes,
Jobs, Secrets. That is the advantage of one namespace per application.

## Level 2 · Delete the cluster

```text
⚠️ DESTRUCTIVE COMMAND · deletes the kind cluster (both node containers and everything inside them).
```

<!-- test: timeout=300; contains=Deleted -->
```bash
kind delete cluster --name bookshop 2>&1
```

<!-- test: absent=bookshop -->
```bash
kind get clusters 2>&1
docker ps --filter name=bookshop -q
```

The images built in the lessons stay in Docker (`docker images`); `docker image rm <name>:<tag>` removes them.
