# 08 · Networking and Ingress

> Goal: one entry point for the whole platform, and you can follow a request from the browser to a Pod. Level 14 of
> the [roadmap](../README.md#4-the-roadmap). Time: about 45 minutes.

## Before you start

All six applications are deployed (chapters 05–07). Read [docs/11](../docs/11-services-networking-and-ingress.md).

## The walk

### 1. Run kubernetes/09

Run [kubernetes/09-ingress.md](../kubernetes/09-ingress.md). Watch for:

- **Every Service, one table.** `postgres` has no cluster IP:

  ```text
  postgres        ClusterIP   None            <none>        5432/TCP   5m55s
  ```

  It is the headless Service of the StatefulSet: its name resolves straight to the database Pod.
- **The rules as Traefik sees them**, with the Pod IPs behind each backend:

  ```text
  bookshop.localhost
                            /api/users    node-api:3000 (10.244.1.5:3000,10.244.1.6:3000)
                            /api/books    java-api:8080 (10.244.1.12:8080)
                            /api/stats    python-api:8000 (10.244.1.9:8000,10.244.1.10:8000)
                            /api/status   go-status:8080 (10.244.1.11:8080)
  ```

  If a backend shows no addresses in brackets, the Service has no Ready Pods: chapter 11 uses exactly that clue.
- **The finished product**, through the front door:

  ```text
  6 of 6 services up
  <title>Bookshop · Reviews</title>
  ```

  Open <http://bookshop.localhost:8080> in your browser now. This is the moment the whole course has been building to.
- **Load balancing**, counted from the Pods' own logs:

  ```text
  pod/node-api-6f678b5b5-lffs6: 6 requests
  pod/node-api-6f678b5b5-xjpjv: 6 requests
  ```

  (The counts include the requests of earlier steps; the split is what matters.)

### 2. Follow one request

Write this in your notebook in your own words, then check it against [docs/11](../docs/11-services-networking-and-ingress.md):

```text
 browser: GET http://bookshop.localhost:8080/api/books
   → localhost:8080 (kind's port mapping) → node port 30080 → Traefik Pod
   → Ingress rule: host bookshop.localhost, longest path match /api/books → Service java-api:8080
   → one Ready Pod of java-api, port 8080 → Spring Boot → PostgreSQL (Service postgres → postgres-0)
```

## Expert commentary

- **Longest path wins.** `/` matches everything, but `/api/books` is more specific, so it wins for book requests.
  Order in the file does not matter; specificity does.
- **One Ingress per platform, or one per team?** Several Ingress objects can add paths to the same host (lab 03
  does exactly that). Teams can own their own routes without editing a shared file.
- **Gateway API** is the successor of Ingress, with richer routing and clearer ownership. The ideas you learn here
  (rule → controller → Service → Pods) carry over unchanged.
- **Interview angle:** "What is the difference between a Service and an Ingress?" A Service gives a stable name and
  load balancing to Pods, mostly inside the cluster. An Ingress is an HTTP routing rule from outside to Services,
  carried out by an ingress controller.

## Checkpoint

- [ ] The UI works in your browser, and the status board shows 6 of 6.
- [ ] You can trace a request from the browser to a Pod without notes.
- [ ] You can say where to look first when one path of the Ingress fails (its backend's addresses).

Next: [09 · Config, probes, storage](09-config-probes-storage.md)
