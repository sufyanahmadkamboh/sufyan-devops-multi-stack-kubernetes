# 00 · A local Kubernetes cluster with an ingress controller

> Level 7 of the [roadmap](../README.md). Time: 10 minutes. You need Docker, [kind](https://kind.sigs.k8s.io/)
> v0.33, kubectl v1.37 and [Helm](https://helm.sh/) v4 (installation: [README](../README.md#3-prerequisites)).

**kind** ("Kubernetes in Docker") runs each Kubernetes node as a Docker container on your computer. It is a real,
conformant Kubernetes 1.37: the same API, the same objects, the same kubectl. What is different from a cloud
cluster is only where the nodes run.

```text
 your computer
 ├── Docker
 │    ├── container bookshop-control-plane   (Kubernetes control plane + node)
 │    └── container bookshop-worker          (a worker node: our Pods run here)
 └── localhost:8080 ──► node port 30080 ──► Traefik (ingress controller) ──► the right Service
```

## Step 1 · Create the cluster

The cluster is described in [cluster/kind-config.yaml](cluster/kind-config.yaml): two nodes, Kubernetes 1.37.0
(the node image pinned by digest), and port 30080 of the nodes published as `localhost:8080`.

<!-- test-run: kind delete cluster --name bookshop > /dev/null 2>&1 || true -->

<!-- test: timeout=600; contains=kind-bookshop; output=tail:3 -->
```bash
kind create cluster --config kubernetes/cluster/kind-config.yaml 2>&1
```

```text
...
kubectl cluster-info --context kind-bookshop

Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 🙂
```

kind also switched kubectl to the new cluster (context `kind-bookshop`):

<!-- test: retry=30; contains=bookshop-worker; absent=NotReady; output -->
```bash
kubectl config current-context
kubectl get nodes
```

```text
kind-bookshop
NAME                     STATUS   ROLES           AGE   VERSION
bookshop-control-plane   Ready    control-plane   29s   v1.37.0
bookshop-worker          Ready    <none>          14s   v1.37.0
```

## Step 2 · Install the ingress controller (Traefik)

An **Ingress** is a routing rule ("requests for `bookshop.localhost/api/users` go to the Service `node-api`"). A rule
does nothing on its own: an **ingress controller** reads the rules and routes the traffic. We install Traefik with Helm,
the package manager for Kubernetes, using the settings in [cluster/traefik-values.yaml](cluster/traefik-values.yaml)
(listen on node port 30080, register the IngressClass `traefik`):

<!-- test: timeout=600; contains=deployed; output=tail:3 -->
```bash
helm repo add traefik https://traefik.github.io/charts > /dev/null 2>&1 || true
helm repo update traefik > /dev/null
helm install traefik traefik/traefik --version 41.6.1 --namespace traefik --create-namespace \
  --values kubernetes/cluster/traefik-values.yaml --wait --timeout 5m
```

```text
...
TEST SUITE: None
NOTES:
traefik with docker.io/traefik:v3.7.13 has been deployed successfully on traefik namespace!
```

<!-- test: contains=30080; contains=traefik; output -->
```bash
kubectl get pods,svc -n traefik
kubectl get ingressclass
```

```text
NAME                           READY   STATUS    RESTARTS   AGE
pod/traefik-6d88bc478f-xsbx9   1/1     Running   0          18s

NAME              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/traefik   NodePort   10.96.165.105   <none>        80:30080/TCP   18s
NAME                CONTROLLER                      PARAMETERS   AGE
traefik (default)   traefik.io/ingress-controller   <none>       18s
```

## Step 3 · Is the entry point alive?

Nothing is deployed yet, so Traefik answers every request with `404 page not found`: proof that requests reach it.
(`*.localhost` names point to your own computer; curl and browsers resolve them without any setup.)

<!-- test: retry=15; contains=404 page not found; output -->
```bash
curl -s http://bookshop.localhost:8080/
```

```text
404 page not found
```

The cluster is ready. Next: the namespace, configuration, secrets and the database: [01 · Foundation](01-foundation.md).
