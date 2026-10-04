# 07 · Database connection failure

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

A typo in the shared configuration: `DB_HOST` becomes `postgress`. Then node-api is restarted (for example by a
deployment), so its new Pods read the new value.

<!-- test: contains=restarted -->
```bash
kubectl patch configmap bookshop-config --type merge -p '{"data":{"DB_HOST":"postgress"}}'
kubectl rollout restart deployment/node-api
```

<!-- test-run: sleep 20 -->

## Problem

The node-api rollout never finishes. Other services, not restarted, still work: they read the old value at their
start.

## Symptoms

<!-- test: retry=30; contains=0/1; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                        READY   STATUS    RESTARTS   AGE
node-api-575dd44f44-79brb   0/1     Running   0          20s
node-api-67dfd9488b-hpbpg   1/1     Running   0          3m4s
node-api-67dfd9488b-jqd2m   1/1     Running   0          3m3s
```

`Running`, not Ready, no restarts: the liveness probe (`/health`) passes, the readiness probe (`/ready`) fails.

## Investigation

What does the application report about its database? node-api's `/ready` answers with the reason. Ask it from inside
the new Pod (Node.js has `fetch` built in, so no extra tool is needed), then check the configuration it started with.

## Commands

<!-- test: retry=10; contains=postgress; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl exec $NEW -- node -e "fetch('http://127.0.0.1:3000/ready').then(async r => console.log(r.status, await r.text()))"
kubectl exec $NEW -- node -e "fetch('http://127.0.0.1:3000/health').then(async r => console.log(r.status, await r.text()))"
kubectl exec $NEW -- printenv DB_HOST
```

```text
503 {"status":"not ready","service":"node-api","reason":"Connection terminated due to connection timeout"}
200 {"status":"ok","service":"node-api","version":"1.0.0"}
postgress
```

<!-- test: contains=postgress; output -->
```bash
kubectl get configmap bookshop-config -o jsonpath='DB_HOST={.data.DB_HOST}{"\n"}'
kubectl get service postgres
```

```text
DB_HOST=postgress
NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
postgres   ClusterIP   None         <none>        5432/TCP   37m
```

## Root cause

`DB_HOST` names a host that does not exist (`postgress`); the Service is called `postgres`. The DNS lookup fails, so
the application cannot reach its database and correctly reports itself as not ready. Because `/health` does not check
the database, Kubernetes does not restart the container: a restart would not help.

## Fix

Correct the ConfigMap (from Git), then restart node-api so its Pods read the corrected value:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/config/bookshop-config.yaml
kubectl rollout restart deployment/node-api
kubectl rollout status deployment/node-api --timeout=240s
```

## Verification

<!-- test: retry=30; contains=Running; absent=0/1; absent=Terminating; output -->
```bash
kubectl get pods -l app=node-api
kubectl get configmap bookshop-config -o jsonpath='DB_HOST={.data.DB_HOST}{"\n"}'
```

```text
NAME                       READY   STATUS    RESTARTS   AGE
node-api-c7ddcd5f8-4zmm8   1/1     Running   0          10s
node-api-c7ddcd5f8-zx2d4   1/1     Running   0          4s
DB_HOST=postgres
```

<!-- test: retry=15; contains=Ada Lovelace -->
```bash
curl -s http://bookshop.localhost:8080/api/users
```

## Lesson learned

- Running but not Ready → ask the application why: a readiness endpoint that reports the reason saves a lot of time.
- Environment variables from a ConfigMap are read when the container starts. A bad value hits only Pods started after
  the change, which makes these errors appear "randomly", at the next deployment or restart.
- Keep `/health` (liveness) independent of the database, so a database problem does not turn into a restart storm.
