# 11 · Services, networking and Ingress

> Time: 30 minutes

## Pods come and go, and so do their IP addresses

Every Pod gets its own IP address. But Pods are replaced all the time (new versions, crashes, scaling), and each
new Pod gets a **new** IP. Nobody can hard-code Pod IPs. A **Service** solves that.

```text
                         Service node-api   (ClusterIP 10.96.x.y, port 3000)
                         selector: app=node-api
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
     Pod node-api-...-kxsnl   Pod node-api-...-z4m5c   Pod (not Ready: gets no traffic)
     10.244.1.5:3000          10.244.1.6:3000
```

A Service gives a group of Pods:

1. **a stable name**: `node-api`, resolvable by DNS inside the cluster,
2. **a stable virtual IP** (the ClusterIP) that never changes while the Service exists,
3. **load balancing** across its **endpoints**: the IPs of the Pods that match its selector **and are Ready**.

## Labels and selectors: the only link

A Service finds its Pods through labels. From [kubernetes/node-api/](../kubernetes/node-api/):

```text
# deployment.yaml (Pod template)             # service.yaml
  template:                                    spec:
    metadata:                                    selector: { app: node-api }
      labels: { app: node-api, ... }             ports:
                                                   - name: http
                                                     port: 3000
                                                     targetPort: http
```

If the selector and the labels differ by one character, the Service has **no endpoints**: no error anywhere, just
"connection refused" or a timeout. `kubectl get endpoints node-api` (or `kubectl get endpointslices`) shows which Pod
IPs a Service really sends traffic to. That check is in the troubleshooting labs.

`port` is the Service's port; `targetPort` is the container port, here referenced by its **name** `http`, so the
number lives only in the Deployment.

## DNS names

Inside the cluster, CoreDNS resolves Service names:

| Name | Works from |
|---|---|
| `node-api` | Pods in the same namespace (`bookshop`) |
| `node-api.bookshop` | any namespace |
| `node-api.bookshop.svc.cluster.local` | anywhere in the cluster (the fully qualified name) |

That is why the Compose file and the Kubernetes manifests use the **same names**: `DB_HOST=postgres`,
`http://python-api:8000/...` work unchanged in both. In Compose, Docker's DNS resolves service names; in Kubernetes,
CoreDNS resolves Service names.

## Service types

| Type | Reachable from | In this lab |
|---|---|---|
| **ClusterIP** (default) | inside the cluster only | every application Service |
| **NodePort** | every node's IP on a port 30000–32767 | the Traefik controller, on 30080 |
| **LoadBalancer** | an external load balancer created by the cloud provider | not used (kind has no cloud) |
| headless (`clusterIP: None`) | DNS returns the Pod IPs directly | `postgres` |

## Ingress: one entry point for HTTP

Exposing every service with its own NodePort would be messy. An **Ingress** is a set of HTTP routing rules: host
name and path → Service. From [kubernetes/ingress/ingress.yaml](../kubernetes/ingress/ingress.yaml):

```text
 http://bookshop.localhost:8080/api/users   → node-api:3000
 http://bookshop.localhost:8080/api/books   → java-api:8080
 http://bookshop.localhost:8080/api/stats   → python-api:8000
 http://bookshop.localhost:8080/api/status  → go-status:8080
 http://bookshop.localhost:8080/            → frontend:8080            (path-based rules, one host)
 http://admin.bookshop.localhost:8080/      → laravel-admin:8080      (host-based rule)
```

The most specific path wins: `/api/users` goes to `node-api`, everything else under `/` to the frontend.

An Ingress object alone does nothing. An **ingress controller** reads the Ingress objects and does the routing. This
lab uses **Traefik**, a maintained controller, installed with Helm
([kubernetes/cluster/traefik-values.yaml](../kubernetes/cluster/traefik-values.yaml)); `ingressClassName: traefik`
selects it. Other controllers (cloud load balancer controllers, HAProxy, Kong, ...) read the same Ingress objects.

## How a request from your browser arrives

```text
 browser: http://bookshop.localhost:8080/api/books
   │   (*.localhost always resolves to 127.0.0.1)
   ▼
 your computer, port 8080
   │   kind extraPortMappings: hostPort 8080 → node port 30080   (kubernetes/cluster/kind-config.yaml)
   ▼
 kind node (a Docker container), port 30080
   │   Service traefik, type NodePort 30080
   ▼
 Traefik Pod: matches host bookshop.localhost + path /api/books
   │
   ▼
 Service java-api:8080  →  a Ready java-api Pod
```

In Compose, the frontend's nginx did this routing (it proxies `/api/...` to the services). In Kubernetes the Ingress
does it, so each API is reached directly.

## Gateway API, the successor

The Ingress API is stable but limited (HTTP routing only; anything more needs controller-specific annotations). The
**Gateway API** is its successor in Kubernetes: `GatewayClass`, `Gateway` and `HTTPRoute` objects split the work
between the platform team (who runs the gateway) and application teams (who own their routes), and it supports more
protocols and features in a portable way. Traefik supports it too. The concepts of this lesson (host, path, backend
Service) carry over directly.

## Check yourself

<details><summary>Why can't `frontend` call `node-api` by its Pod IP?</summary>

Pod IPs change whenever a Pod is replaced. The Service gives a stable name and virtual IP that always point at the
current Ready Pods.
</details>

<details><summary>A Service exists, the Pods run, but `kubectl get endpoints` shows `<none>`. What is wrong?</summary>

The Service's selector doesn't match the Pods' labels, or the Pods are not Ready (failing readiness probe).
</details>

<details><summary>Which DNS name works from another namespace: `node-api` or `node-api.bookshop`?</summary>

`node-api.bookshop` (or the full `node-api.bookshop.svc.cluster.local`). The short name only works in the same
namespace.
</details>

<details><summary>What does the Traefik controller do with the Ingress object?</summary>

It watches Ingress objects and configures itself to route each host and path to the right Service. Without a
controller, the Ingress object has no effect.
</details>

<details><summary>Trace `http://admin.bookshop.localhost:8080/` from the browser to a container.</summary>

Port 8080 on your computer → kind port mapping → node port 30080 → Traefik Service (NodePort) → Traefik matches the
host `admin.bookshop.localhost` → Service `laravel-admin:8080` → the `laravel-web` container (nginx) → PHP-FPM in the
same Pod.
</details>

Next: [12 · Scaling, rolling updates and rollbacks](12-scaling-rolling-updates-rollbacks.md)
