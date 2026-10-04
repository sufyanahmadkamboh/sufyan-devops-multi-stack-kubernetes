# 06 · Deploy the frontend

> Goal: the React UI runs on Kubernetes, configured at start time, with one image for every environment. Level 9 of
> the [roadmap](../README.md#4-the-roadmap). Time: about 30 minutes.

## The walk

### 1. Run kubernetes/03

Run [kubernetes/03-frontend.md](../kubernetes/03-frontend.md). Watch for the configuration file the container wrote
when it started:

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080", APP_ENV: "kubernetes" };
```

The same image printed different values in Compose. That is runtime configuration: the built JavaScript reads
`/config.js`, and the container generates that file from its environment variables at start.

### 2. The proxy that is not needed, and why it is there

The frontend's nginx can forward `/api/*` to the APIs (that is how it worked in Compose). Through a port-forward, before
the Ingress exists, you see both outcomes:

```text
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com", ...
{"error":"upstream unreachable","path":"/api/books"}
```

node-api answers; java-api does not exist yet (if you deployed it already, both answer), and nginx returns a clean
502 JSON instead of hanging. Notice also the full DNS names in [frontend/deployment.yaml](../kubernetes/frontend/deployment.yaml)
(`node-api.bookshop.svc.cluster.local`): nginx's own resolver does not use the cluster's search domains. Short names
work for almost everything in Kubernetes, but not for nginx's resolver.

## Expert commentary

- **Build-time vs runtime configuration** is the classic single-page-app trap: Vite and React bake environment
  variables into the bundle at **build** time. Then you need one image per environment, which defeats "build once,
  deploy everywhere". The `/config.js` trick (or a small config endpoint) keeps one image.
- **The frontend is just a web server.** In Kubernetes it is an nginx Deployment like any other; the browser does the
  React work. Scaling the frontend means scaling a file server.
- **Interview angle:** "How do you configure a React app per environment without rebuilding it?" Runtime config
  generated at container start, read by the app before it renders.

## Checkpoint

- [ ] The frontend Deployment is `Available` with 2 replicas.
- [ ] You can explain where `APP_ENV: "kubernetes"` came from, step by step (ConfigMap or env → container start →
      `/config.js` → browser).
- [ ] You can explain why the proxy uses full DNS names.

Next: [07 · Laravel and the worker](07-laravel-and-the-worker.md)
