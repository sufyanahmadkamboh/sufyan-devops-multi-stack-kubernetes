# 11 · The frontend cannot reach a backend

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

The java-api Service is edited: its `port` becomes 8081 ("to avoid confusion with go-status"). Nobody updates the
places that call it.

<!-- test: contains=service/java-api patched -->
```bash
kubectl patch service java-api --type json -p '[{"op":"replace","path":"/spec/ports/0/port","value":8081}]'
```

## Problem

In the browser, the Books panel of the Bookshop UI shows an error. Users, statistics and status still work.

## Symptoms

The browser calls `/api/books`. Do the same, and look at the whole response, headers included:

<!-- test: retry=15; contains=502; output -->
```bash
curl -s -i http://bookshop.localhost:8080/api/books
```

```text
HTTP/1.1 502 Bad Gateway
Content-Length: 52
Content-Type: application/json
Date: Sun, 04 Oct 2026 18:54:38 GMT
Server: nginx/1.30.5

{"error":"upstream unreachable","path":"/api/books"}
```

## Investigation

Look closely at that answer: `Server: nginx` and a JSON body `{"error":"upstream unreachable",...}`. That is not
java-api answering, and not Traefik: it is the **frontend's** nginx. So the request did not go where the Ingress
should have sent it. Two questions: what does the Ingress say about `/api/books`, and why did the frontend's own
proxy fail too?

## Commands

<!-- test: contains=java-api:8080; output -->
```bash
kubectl describe ingress bookshop | grep -E 'Path|/api/books|/ '
```

```text
  Host                      Path  Backends
                            /api/books    java-api:8080 ()
                            /             frontend:8080 (10.244.1.19:8080,10.244.1.20:8080)
                            /   laravel-admin:8080 (10.244.1.14:8080)
```

<!-- test: contains=8081; output -->
```bash
kubectl get service java-api
kubectl get endpointslices -l kubernetes.io/service-name=java-api -o custom-columns='SERVICE:.metadata.labels.kubernetes\.io/service-name,PORT:.ports[0].port,ADDRESS:.endpoints[0].addresses[0]'
```

```text
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
java-api   ClusterIP   10.96.195.75   <none>        8081/TCP   35m
SERVICE    PORT   ADDRESS
java-api   8080   10.244.1.12
```

<!-- test: contains=8080; output -->
```bash
kubectl get deployment frontend -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="JAVA_API_URL")].value}{"\n"}'
```

```text
http://java-api.bookshop.svc.cluster.local:8080
```

## Root cause

Two clients use java-api on port **8080**: the Ingress rule for `/api/books`, and the frontend's nginx (`JAVA_API_URL`).
The Service now exposes port **8081**. Traefik cannot build a route to a Service port that does not exist, so it drops
that rule; the request then matches the next rule, `/` → frontend. The frontend's nginx forwards `/api/books` to
`java-api...:8080`, gets no answer, and returns its 502 JSON. java-api itself is healthy; its address changed.

## Fix

Put the Service back to the port its clients use (changing a Service port means changing every client first). The
usual way, `kubectl apply`, fails here:

<!-- test: fail; contains=Duplicate value; output -->
```bash
kubectl apply -f kubernetes/java-api/service.yaml
```

```text
Warning: resource services/java-api is missing the kubectl.kubernetes.io/last-applied-configuration annotation which is required by kubectl apply. kubectl apply should only be used on resources created declaratively by either kubectl create --save-config or kubectl apply. The missing annotation will be patched automatically.
The Service "java-api" is invalid: spec.ports[1].name: Duplicate value: "http"
```

`apply` merges the list of ports **by port number**. Port 8080 is not in the live object (it has 8081), so `apply`
tries to *add* an 8080 entry next to 8081, and both would be named `http`. `kubectl replace` sends the whole object
from the file instead of merging:

<!-- test: contains=service/java-api replaced -->
```bash
kubectl replace -f kubernetes/java-api/service.yaml
```

## Verification

<!-- test: retry=20; contains=Moby-Dick; absent=Server: nginx; output -->
```bash
curl -s -i http://bookshop.localhost:8080/api/books | head -c 400; echo
```

```text
HTTP/1.1 200 OK
Content-Length: 390
Content-Type: application/json
Date: Sun, 04 Oct 2026 18:54:39 GMT

[{"id":1,"title":"Pride and Prejudice","author":"Jane Austen","year":1813},{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851},{"id":3,"title":"Crime and Punishment","author":"Fyodor Dostoevsky","year":1866},{"id":4,"title":"The Adventures of Sherlock Holmes","author":"Arthu
```

No `Server: nginx` header anymore: the answer comes from java-api (Spring Boot) directly, through the Ingress.

## Lesson learned

- Read response **headers** and the **shape** of the body: they tell you which component really answered.
- A route that cannot be built is often skipped silently, and the request falls through to a broader rule.
- A Service's port is an interface: before changing it, find every client (Ingress rules, other services' config).
- `kubectl apply` merges lists by a key (ports by port number, containers and env by name); when the key itself
  changed, `kubectl replace -f` restores the object from the file.
