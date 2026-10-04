# 02 · Deploy node-api (Node.js)

> Level 8 of the [roadmap](../README.md). Time: 20 minutes. The application: [applications/node-api](../applications/node-api/README.md).

The first application, step by step. Every later application follows the same pattern; this lesson explains it in
detail once.

## From the Compose service to Kubernetes resources

```text
 compose/docker-compose.yml                kubernetes/node-api/
 ─────────────────────────────             ──────────────────────────────────────────────────
 node-api:                                 Deployment node-api      ← "run 2 copies of this Pod, keep them running"
   image: node-api:1.0.0                     └─ Pod template: container node-api, image node-api:1.0.0
   environment: *db-env                         env from ConfigMap bookshop-config + Secret db-credentials
   healthcheck: wget /ready                     livenessProbe /health · readinessProbe /ready
   depends_on: postgres (healthy)               (no equivalent: readiness + the app's own retries)
   networks: [frontend, backend]           Service node-api        ← stable name + address, load-balances to the Pods
```

The full mapping is in [docs/06](../docs/06-compose-to-kubernetes.md). The two files:
[node-api/deployment.yaml](node-api/deployment.yaml) and [node-api/service.yaml](node-api/service.yaml).

## Step 1 · Make the image available to the cluster

Kubernetes nodes pull images from a registry. Our image exists only in Docker on this computer, and kind's nodes are
separate containers with their own image store. `kind load docker-image` copies it into every node (in a cloud you
would push to a registry instead: [docs/04](../docs/04-images-tags-and-registries.md)).

<!-- test: timeout=300; contains=node-api:1.0.0; output -->
```bash
kind load docker-image node-api:1.0.0 --name bookshop
```

```text
Image: "node-api:1.0.0" with ID "sha256:d26f646c1a28efe315aa7c9bae985c898b4a72449beed15c306746c4667034d7" not yet present on node "bookshop-control-plane", loading...
Image: "node-api:1.0.0" with ID "sha256:d26f646c1a28efe315aa7c9bae985c898b4a72449beed15c306746c4667034d7" not yet present on node "bookshop-worker", loading...
```

The Deployment says `imagePullPolicy: IfNotPresent`: use the image if the node has it, pull only otherwise. With the
version tag `1.0.0` that is safe: that tag always means the same image.

## Step 2 · The Deployment, the important lines

| Line | Meaning |
|---|---|
| `replicas: 2` | keep two Pods running at all times |
| `selector.matchLabels: {app: node-api}` | which Pods belong to this Deployment (must match the template's labels) |
| `image: node-api:1.0.0` | the same image Docker and Compose ran |
| `env: ... configMapKeyRef / secretKeyRef` | the Compose `environment`, split into non-secret (ConfigMap) and secret (Secret) |
| `livenessProbe: /health` | if it fails 3 times, Kubernetes **restarts** the container |
| `readinessProbe: /ready` | while it fails, the Pod gets **no traffic** from the Service |
| `resources.requests` / `limits` | what the scheduler reserves / the ceiling ([docs/09](../docs/09-resources-requests-and-limits.md)) |
| `securityContext` | not root, no privilege escalation, no Linux capabilities |

## Step 3 · Apply

<!-- test: contains=deployment.apps/node-api created; contains=service/node-api created -->
```bash
kubectl apply -f kubernetes/node-api/
```

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/node-api --timeout=240s
```

```text
Waiting for deployment "node-api" rollout to finish: 0 of 2 updated replicas are available...
Waiting for deployment "node-api" rollout to finish: 1 of 2 updated replicas are available...
deployment "node-api" successfully rolled out
```

<!-- test: contains=node-api; output -->
```bash
kubectl get deployment node-api
kubectl get pods -l app=node-api -o wide
```

```text
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
node-api   2/2     2            2           1s
NAME                       READY   STATUS    RESTARTS   AGE   IP           NODE              NOMINATED NODE   READINESS GATES
node-api-6f678b5b5-lffs6   1/1     Running   0          1s    10.244.1.6   bookshop-worker   <none>           <none>
node-api-6f678b5b5-xjpjv   1/1     Running   0          1s    10.244.1.5   bookshop-worker   <none>           <none>
```

Two Pods, each with its own IP address. Pods are replaceable: when one dies, the Deployment creates a new one with a
new IP. That is why nobody talks to Pod IPs directly.

## Step 4 · The Service: one stable name

<!-- test: contains=node-api; contains=3000; output -->
```bash
kubectl get service node-api
kubectl get endpoints node-api
```

```text
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
node-api   ClusterIP   10.96.169.17   <none>        3000/TCP   1s
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME       ENDPOINTS                         AGE
node-api   10.244.1.5:3000,10.244.1.6:3000   2s
```

The Service has a fixed virtual IP and the DNS name `node-api`; its **endpoints** are the IPs of the Pods that match
its selector **and are Ready**. Call the API through the Service from inside the cluster (we use one of the node-api
Pods as the place to run `wget`):

<!-- test: retry=10; contains=Ada Lovelace; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://node-api:3000/api/users
echo
```

```text
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T18:18:13.035Z"},{"id":2,"name":"Grace Hopper","email":"grace@example.com","created_at":"2026-10-04T18:18:13.038Z"},{"id":3,"name":"Linus Torvalds","email":"linus@example.com","created_at":"2026-10-04T18:18:13.039Z"}]
```

The data came from PostgreSQL: node-api created its `users` table and three users when it started, exactly as in
Compose.

## Step 5 · From your computer: port-forward

Services of type ClusterIP are reachable only inside the cluster. For a quick look from your computer,
`kubectl port-forward` tunnels a local port to the Service (in normal use it runs in the foreground until Ctrl+C;
here it runs in the background for a few seconds):

<!-- test: contains="service":"node-api"; output -->
```bash
kubectl port-forward service/node-api 13000:3000 > /dev/null 2>&1 &
PF=$!
sleep 3
curl -s http://localhost:13000/
echo
kill $PF
```

```text
{"service":"node-api","version":"1.0.0","language":"JavaScript","runtime":"Node.js 24.21.0","description":"Users API of the Bookshop (Express)"}
```

Real users will come through the Ingress ([09](09-ingress.md)), not through port-forward.

## Step 6 · Logs

Each Pod writes its logs to stdout; Kubernetes keeps them per container. `-l` reads all Pods of the Deployment:

<!-- test: contains=node-api; output=tail:6 -->
```bash
kubectl logs -l app=node-api --tail=3 --prefix
```

```text
[pod/node-api-6f678b5b5-xjpjv/node-api] 2026-10-04T18:18:13.041Z node-api table users ready
[pod/node-api-6f678b5b5-xjpjv/node-api] 2026-10-04T18:18:13.549Z node-api GET /ready 200
[pod/node-api-6f678b5b5-xjpjv/node-api] 2026-10-04T18:18:15.219Z node-api GET /api/users 200
[pod/node-api-6f678b5b5-lffs6/node-api] 2026-10-04T18:18:13.560Z node-api table users ready
[pod/node-api-6f678b5b5-lffs6/node-api] 2026-10-04T18:18:13.565Z node-api GET /ready 200
[pod/node-api-6f678b5b5-lffs6/node-api] 2026-10-04T18:18:18.374Z node-api GET / 200
```

node-api runs on Kubernetes. Next: the user interface, [03 · frontend](03-frontend.md).
