# Lab 03 · Convert quotes-api to Kubernetes

## Task

Deploy quotes-api to the running Bookshop cluster and publish it at
`http://bookshop.localhost:8080/api/quotes`, with the same quality as the platform's own services.

## Requirements

1. `labs/work/k8s/quotes-api.yaml` with a Deployment (2 replicas) and a ClusterIP Service `quotes-api:8000`, in the
   namespace `bookshop`.
2. Image `quotes-api:1.0.0`, loaded into kind; `imagePullPolicy: IfNotPresent`.
3. Liveness and readiness probes on `/health`; requests and limits for CPU and memory; `runAsNonRoot`.
4. A separate Ingress `quotes` in the namespace that routes the path `/api/quotes` on host `bookshop.localhost`.
5. Do not edit the platform's own manifests.

## Hints

- Start from [kubernetes/go-status/deployment.yaml](../kubernetes/go-status/deployment.yaml): no database, no Secret.
- Several Ingress objects can define paths for the same host; the controller merges them.
- `kubectl apply --dry-run=server -f ...` validates your file against the cluster without creating anything.

## Expected result

`curl -s http://bookshop.localhost:8080/api/quotes` returns a quote; `kubectl get pods -l app=quotes-api` shows
`2/2` Pods `1/1` Ready.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: contains=created (server dry run); output -->
```bash
mkdir -p labs/work/k8s
cat > labs/work/k8s/quotes-api.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quotes-api
  namespace: bookshop
  labels: { app: quotes-api }
spec:
  replicas: 2
  selector:
    matchLabels: { app: quotes-api }
  template:
    metadata:
      labels: { app: quotes-api }
    spec:
      securityContext: { runAsNonRoot: true, runAsUser: 10001, seccompProfile: { type: RuntimeDefault } }
      containers:
        - name: quotes-api
          image: quotes-api:1.0.0
          imagePullPolicy: IfNotPresent
          ports: [{ name: http, containerPort: 8000 }]
          livenessProbe: { httpGet: { path: /health, port: http }, periodSeconds: 10 }
          readinessProbe: { httpGet: { path: /health, port: http }, periodSeconds: 5 }
          resources:
            requests: { cpu: 10m, memory: 24Mi }
            limits: { cpu: 200m, memory: 64Mi }
          securityContext: { allowPrivilegeEscalation: false, capabilities: { drop: ["ALL"] } }
---
apiVersion: v1
kind: Service
metadata:
  name: quotes-api
  namespace: bookshop
spec:
  selector: { app: quotes-api }
  ports: [{ name: http, port: 8000, targetPort: http }]
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: quotes
  namespace: bookshop
spec:
  ingressClassName: traefik
  rules:
    - host: bookshop.localhost
      http:
        paths:
          - path: /api/quotes
            pathType: Prefix
            backend: { service: { name: quotes-api, port: { number: 8000 } } }
EOF
kubectl apply --dry-run=server -f labs/work/k8s/quotes-api.yaml
```

```text
deployment.apps/quotes-api created (server dry run)
service/quotes-api created (server dry run)
ingress.networking.k8s.io/quotes created (server dry run)
```

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kind load docker-image quotes-api:1.0.0 --name bookshop > /dev/null
kubectl apply -f labs/work/k8s/quotes-api.yaml
kubectl rollout status deployment/quotes-api --timeout=240s
```

<!-- test: retry=15; contains=author; output -->
```bash
kubectl get pods -l app=quotes-api
curl -s http://bookshop.localhost:8080/api/quotes; echo
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
quotes-api-5cc5b7c6c5-f625h   1/1     Running   0          6s
quotes-api-5cc5b7c6c5-v99n5   1/1     Running   0          6s
{"quote": "Make it work, make it right, make it fast.", "author": "Kent Beck", "version": "1.0.0"}
```

</details>

## Explanation

Compose needed one service block; Kubernetes needs three objects, because it separates concerns that Compose mixes:
**what runs** (Deployment: image, replicas, probes, resources, security), **how to reach it inside the cluster**
(Service: a stable name and the selection of Ready Pods) and **how to reach it from outside** (Ingress: a path on the
shared entry point). The `--dry-run=server` step catches typos and schema errors before anything changes.

Next: [Lab 04 · Scale it](04-scale.md).
