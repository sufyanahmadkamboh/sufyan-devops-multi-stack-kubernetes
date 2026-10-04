# 06 · Deploy java-api (Java, Spring Boot)

> Level 12 of the [roadmap](../README.md). Time: 15 minutes. The application: [applications/java-api](../applications/java-api/README.md).

The JVM needs a few seconds to start, more when its CPU is limited (measured in the
[java-api lesson](../applications/java-api/README.md)). If the liveness probe started checking immediately, it could
kill the container before it ever finished starting, again and again. A **startupProbe** solves that: until it
succeeds, the other probes wait.

```text
 startupProbe:  GET /health every 2 s, up to 30 failures = up to 60 s to start
 livenessProbe: GET /health every 10 s, starts only after the startup probe succeeded
 readinessProbe: GET /ready every 5 s (also checks the database)
 resources: requests 250m CPU / 256Mi, limits 1 CPU / 512Mi; the JVM uses -XX:MaxRAMPercentage=75 of the limit
```

<!-- test: timeout=300; contains=java-api:1.0.0 -->
```bash
kind load docker-image java-api:1.0.0 --name bookshop
```

<!-- test: contains=deployment.apps/java-api created -->
```bash
kubectl apply -f kubernetes/java-api/
```

Watch it become Ready (it takes longer than the others):

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/java-api --timeout=240s
kubectl get pods -l app=java-api
```

```text
Waiting for deployment "java-api" rollout to finish: 0 of 1 updated replicas are available...
deployment "java-api" successfully rolled out
NAME                        READY   STATUS    RESTARTS   AGE
java-api-64578ccddb-srwvq   1/1     Running   0          6s
```

How long did the start take, from Spring Boot's own log line?

<!-- test: contains=Started; output -->
```bash
kubectl logs deploy/java-api | grep -m1 -o 'Started .*'
```

```text
Started BookshopApplication in 4.452 seconds (process running for 5.296)
```

<!-- test: contains=Startup; output -->
```bash
kubectl describe pod -l app=java-api | grep -E 'Startup|Liveness|Readiness'
```

```text
    Liveness:   http-get http://:http/health delay=0s timeout=1s period=10s successThreshold=1 failureThreshold=3
    Readiness:  http-get http://:http/ready delay=0s timeout=1s period=5s successThreshold=1 failureThreshold=2
    Startup:    http-get http://:http/health delay=0s timeout=1s period=2s successThreshold=1 failureThreshold=30
  Warning  Unhealthy  3s (x2 over 5s)  kubelet            spec.containers{java-api}: Startup probe failed: Get "http://10.244.1.12:8080/health": dial tcp 10.244.1.12:8080: connect: connection refused
```

<!-- test: retry=10; contains=Moby-Dick; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://java-api:8080/api/books | head -c 200
echo
```

```text
[{"id":1,"title":"Pride and Prejudice","author":"Jane Austen","year":1813},{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":1851},{"id":3,"title":"Crime and Punishment","author":"Fyodor D
```

java-api created and filled the `books` table at startup. Next: [07 · laravel-admin](07-laravel-admin.md).
