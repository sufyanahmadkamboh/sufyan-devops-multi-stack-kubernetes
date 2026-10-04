# 03 · Deploy the frontend (React)

> Level 9 of the [roadmap](../README.md). Time: 15 minutes. The application: [applications/frontend](../applications/frontend/README.md).

The React application is not a server program: the browser runs the JavaScript. The container only serves the built
files (nginx). For Kubernetes that makes no difference: it is an image that listens on a port and answers `/health`.

```text
 Compose: frontend                         Kubernetes: kubernetes/frontend/
   image: frontend:1.0.0                     Deployment frontend (2 replicas), Service frontend:8080
   environment: ADMIN_URL                    env ADMIN_URL from the ConfigMap, APP_ENV=kubernetes
   ports: 127.0.0.1:8081:8080                (no host port: the Ingress will be the entry point)
   depends_on: the APIs (healthy)            nothing: the page shows each API's state on its own
```

## Step 1 · Load and apply

<!-- test: timeout=300; contains=frontend:1.0.0 -->
```bash
kind load docker-image frontend:1.0.0 --name bookshop
```

<!-- test: contains=deployment.apps/frontend created -->
```bash
kubectl apply -f kubernetes/frontend/
```

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/frontend --timeout=240s
kubectl get pods -l app=frontend
```

```text
Waiting for deployment "frontend" rollout to finish: 0 of 2 updated replicas are available...
Waiting for deployment "frontend" rollout to finish: 1 of 2 updated replicas are available...
deployment "frontend" successfully rolled out
NAME                       READY   STATUS    RESTARTS   AGE
frontend-fd495cfc7-dl2ct   1/1     Running   0          1s
frontend-fd495cfc7-wd454   1/1     Running   0          1s
```

## Step 2 · Check it through a port-forward

<!-- test: contains=<title>Bookshop</title>; contains="service":"frontend"; contains=kubernetes; output -->
```bash
kubectl port-forward service/frontend 18080:8080 > /dev/null 2>&1 &
PF=$!
sleep 3
curl -s http://localhost:18080/ | grep -o '<title>[^<]*</title>'
curl -s http://localhost:18080/health; echo
curl -s http://localhost:18080/config.js
kill $PF
```

```text
<title>Bookshop</title>
{"status":"ok","service":"frontend","version":"1.0.0"}
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080", APP_ENV: "kubernetes" };
```

`/config.js` is written when the container starts, from its environment (here from the ConfigMap): the same image
runs in Compose and in Kubernetes with different settings. A React build bakes values in at **build** time; reading
them at **start** time is what makes one image work everywhere ([applications/frontend](../applications/frontend/README.md)).

## Step 3 · Its API calls

The page fetches `/api/users`, `/api/books`, ... from the same address. Through the port-forward they go to the
frontend's nginx, which forwards them to the Services by their full DNS names (see the env in
[frontend/deployment.yaml](frontend/deployment.yaml)). node-api is deployed, the others not yet:

<!-- test: contains=Ada Lovelace; contains=upstream unreachable; output -->
```bash
kubectl port-forward service/frontend 18080:8080 > /dev/null 2>&1 &
PF=$!
sleep 3
curl -s http://localhost:18080/api/users | head -c 120; echo
curl -s http://localhost:18080/api/books; echo
kill $PF
```

```text
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T18:18:13.035Z"},{"id":2,"name":"Grace 
{"error":"upstream unreachable","path":"/api/books"}
```

`/api/books` fails cleanly with a 502 JSON message, because java-api does not exist yet. The UI shows the same error in
its Books panel. Once the Ingress exists ([09](09-ingress.md)), it sends `/api/*` straight to each API.

Next: [04 · python-api](04-python-api.md).
