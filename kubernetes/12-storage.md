# 12 · Storage: data that outlives its Pod

> Level 17 of the [roadmap](../README.md). Time: 10 minutes. The concepts: [docs/10](../docs/10-storage-and-databases.md).

A container's own filesystem disappears with the container. PostgreSQL's data lives in a **PersistentVolumeClaim**
(`data-postgres-0`) created by the StatefulSet. In Compose this was the named volume `pgdata`.

## Step 1 · Write something

<!-- test: contains=Margaret Hamilton; output -->
```bash
curl -s -X POST http://bookshop.localhost:8080/api/users -H 'Content-Type: application/json' \
  -d '{"name":"Margaret Hamilton","email":"margaret@example.com"}'; echo
```

```text
{"id":7,"name":"Margaret Hamilton","email":"margaret@example.com","created_at":"2026-10-04T18:23:10.555Z"}
```

## Step 2 · Delete the database Pod

```text
⚠️ DESTRUCTIVE COMMAND · deletes the PostgreSQL Pod (the StatefulSet creates it again; the data volume is kept).
```

<!-- test: timeout=300; contains=deleted -->
```bash
kubectl delete pod postgres-0
```

<!-- test: timeout=300; contains=roll out complete; output -->
```bash
kubectl rollout status statefulset/postgres --timeout=240s
kubectl get pod postgres-0
```

```text
Waiting for 1 pods to be ready...
partitioned roll out complete: 1 new pods have been updated...
NAME         READY   STATUS    RESTARTS   AGE
postgres-0   1/1     Running   0          1s
```

A new Pod, with the same name `postgres-0`: a StatefulSet gives its Pods stable identities, and binds `postgres-0`
to the same claim again.

## Step 3 · The data is still there

<!-- test: retry=30; contains=Margaret Hamilton; output -->
```bash
curl -s http://bookshop.localhost:8080/api/users | python3 -c "import sys,json; [print(u['id'], u['name']) for u in json.load(sys.stdin)]"
```

```text
1 Ada Lovelace
2 Grace Hopper
3 Linus Torvalds
7 Margaret Hamilton
```

<!-- test: contains=Bound; output -->
```bash
kubectl get pvc
kubectl get pv -o custom-columns='VOLUME:.metadata.name,CLAIM:.spec.claimRef.name,CAPACITY:.spec.capacity.storage,STORAGECLASS:.spec.storageClassName,STATUS:.status.phase'
```

```text
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-postgres-0   Bound    pvc-75001b56-51db-4231-9bcf-e1b7b24d6547   1Gi        RWO            standard       <unset>                 7m34s
VOLUME                                     CLAIM             CAPACITY   STORAGECLASS   STATUS
pvc-75001b56-51db-4231-9bcf-e1b7b24d6547   data-postgres-0   1Gi        standard       Bound
```

What survives what:

| Event | Data |
|---|---|
| Pod deleted or restarted, node restarted | kept (the claim and its volume stay) |
| StatefulSet deleted | kept: claims of a StatefulSet are **not** deleted with it, on purpose |
| PersistentVolumeClaim deleted | lost (with the default reclaim policy `Delete`) |
| kind cluster deleted | lost: the volume is a folder inside the node container |

This is enough for a lab. A production database also needs backups, tested restores, replication, upgrades and
monitoring: usually a managed database (for example Amazon RDS) or a database operator ([docs/10](../docs/10-storage-and-databases.md)).

Next: [13 · Resources: requests, limits, OOMKilled](13-resources.md).
