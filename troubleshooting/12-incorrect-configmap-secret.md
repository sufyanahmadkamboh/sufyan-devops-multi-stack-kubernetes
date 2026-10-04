# 12 · An incorrect Secret

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end. It never prints the real password.

## Break it

Someone "rotates" the database password by replacing the Secret, but does not change the password in PostgreSQL.
Later node-api restarts and reads the new value:

<!-- test: contains=restarted -->
```bash
kubectl create secret generic db-credentials --from-literal=DB_PASSWORD=wrong-password \
  --dry-run=client -o yaml | kubectl apply -f - > /dev/null
kubectl rollout restart deployment/node-api
```

<!-- test-run: sleep 20 -->

## Problem

The node-api rollout is stuck; its new Pods are never Ready. Everything else seems fine, for now.

## Symptoms

<!-- test: retry=30; contains=0/1; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                       READY   STATUS    RESTARTS   AGE
node-api-5748b5f77-fj8dq   0/1     Running   0          20s
node-api-c7ddcd5f8-4zmm8   1/1     Running   0          107s
node-api-c7ddcd5f8-zx2d4   1/1     Running   0          101s
```

## Investigation

Not Ready → ask `/ready` for the reason, and read the logs. Then compare what the application received with what the
database expects, without printing either.

## Commands

<!-- test: retry=10; contains=password authentication failed; output -->
```bash
NEW=$(kubectl get pods -l app=node-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl exec $NEW -- node -e "fetch('http://127.0.0.1:3000/ready').then(async r => console.log(r.status, await r.text()))"
```

```text
503 {"status":"not ready","service":"node-api","reason":"password authentication failed for user \"bookshop\""}
```

Compare the password in the Secret with the one PostgreSQL started with (only their checksums, never the values):

<!-- test: contains=differ; output -->
```bash
A=$(kubectl get secret db-credentials -o jsonpath='{.data.DB_PASSWORD}' | base64 -d | sha256sum | cut -c1-12)
B=$(kubectl exec postgres-0 -- printenv POSTGRES_PASSWORD | tr -d '\n' | sha256sum | cut -c1-12)
echo "Secret: $A   database: $B"; [ "$A" = "$B" ] && echo "same" || echo "they differ"
```

```text
Secret: 6786324d7148   database: 11479d24a601
they differ
```

## Root cause

The Secret `db-credentials` holds a password the database does not accept. PostgreSQL rejects node-api's login
("password authentication failed for user"). Only Pods started after the change are affected, so the error spreads
slowly, one restart at a time: the most dangerous kind of configuration error.

## Fix

Restore the real password. Here we take it from the running PostgreSQL container's environment (the value it was
initialised with), straight into the Secret, without showing it:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl create secret generic db-credentials \
  --from-literal=DB_PASSWORD="$(kubectl exec postgres-0 -- printenv POSTGRES_PASSWORD)" \
  --dry-run=client -o yaml | kubectl apply -f - > /dev/null
kubectl rollout restart deployment/node-api
kubectl rollout status deployment/node-api --timeout=240s
```

## Verification

<!-- test: retry=30; contains=Running; absent=0/1; absent=Terminating; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                      READY   STATUS    RESTARTS   AGE
node-api-7f464fcf-frsrq   1/1     Running   0          3s
node-api-7f464fcf-m6f78   1/1     Running   0          5s
```

<!-- test: retry=15; contains=Ada Lovelace -->
```bash
curl -s http://bookshop.localhost:8080/api/users
```

## Lesson learned

- `password authentication failed` → the credentials in the Secret and in the database disagree.
- Rotating a password is a sequence: change it in the database (or allow both for a while), update the Secret, restart
  the clients, verify. Changing only the Secret breaks every client at its next restart.
- Compare secrets by checksum, never by printing them.
