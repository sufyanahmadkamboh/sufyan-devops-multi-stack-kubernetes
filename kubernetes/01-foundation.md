# 01 · Foundation: namespace, configuration, secrets, database

> Levels 7 and 15–17 of the [roadmap](../README.md) start here. Time: 15 minutes.
> The concepts: [docs/06](../docs/06-compose-to-kubernetes.md), [docs/07](../docs/07-configmaps-and-secrets.md),
> [docs/10](../docs/10-storage-and-databases.md).

Before any application, the things every application needs: a namespace to live in, shared configuration, the
secrets, and the database. In Compose these were the top of the file (`x-db-env`), `.env`, and the `postgres` service
with its volume.

| Compose | Kubernetes, in this lesson |
|---|---|
| the project name `bookshop` | Namespace `bookshop` |
| `x-db-env` (DB_HOST, DB_PORT, ...) | ConfigMap `bookshop-config` |
| `.env` (DB_PASSWORD, APP_KEY) | Secrets `db-credentials` and `laravel-app-key` |
| service `postgres` + volume `pgdata` | StatefulSet `postgres` + PersistentVolumeClaim + headless Service |

## Step 1 · The namespace

<!-- test: contains=namespace/bookshop -->
```bash
kubectl apply -f kubernetes/namespace.yaml
```

Every following command would need `-n bookshop`. Make it the default for the current context instead:

<!-- test: contains=bookshop; output -->
```bash
kubectl config set-context --current --namespace=bookshop
kubectl config view --minify -o jsonpath='{..namespace}'; echo
```

```text
Context "kind-bookshop" modified.
bookshop
```

## Step 2 · Configuration: a ConfigMap

[config/bookshop-config.yaml](config/bookshop-config.yaml) holds everything that is not secret: where the database
is, the URLs the worker and the status board use, the admin link of the UI.

<!-- test: contains=configmap/bookshop-config -->
```bash
kubectl apply -f kubernetes/config/bookshop-config.yaml
```

<!-- test: contains=DB_HOST; output -->
```bash
kubectl get configmap bookshop-config -o jsonpath='{.data}' | python3 -m json.tool | head -8
```

```text
{
    "ADMIN_URL": "http://admin.bookshop.localhost:8080",
    "DB_HOST": "postgres",
    "DB_NAME": "bookshop",
    "DB_PORT": "5432",
    "DB_USER": "bookshop",
    "STATS_URL": "http://python-api:8000/api/stats",
    "STATUS_URL": "http://go-status:8080/api/status",
```

## Step 3 · Secrets, generated, never committed

The repository contains no secret values. Create them from random values, directly in the cluster:

<!-- test: contains=secret/db-credentials created; contains=secret/laravel-app-key created -->
```bash
kubectl create secret generic db-credentials --from-literal=DB_PASSWORD="$(openssl rand -hex 16)"
kubectl create secret generic laravel-app-key --from-literal=APP_KEY="base64:$(openssl rand -base64 32)"
```

<!-- test: contains=DB_PASSWORD; output -->
```bash
kubectl describe secret db-credentials | tail -3
```

```text
Data
====
DB_PASSWORD:  32 bytes
```

`describe` shows the key and the size, never the value. The value is stored **base64-encoded**, which is not
encryption: anyone allowed to read Secrets in this namespace can decode it. What protects it is access control (RBAC),
keeping it out of images and Git, and, on real clusters, encryption at rest ([docs/07](../docs/07-configmaps-and-secrets.md)).

## Step 4 · The database: a StatefulSet with its own volume

[database/postgres.yaml](database/postgres.yaml): a headless Service `postgres` (the name the applications use), and
a StatefulSet that gives its Pod a stable name (`postgres-0`) and a PersistentVolumeClaim of 1 GiB. The password comes
from the Secret, the database name and user from the ConfigMap.

<!-- test: contains=statefulset.apps/postgres created -->
```bash
kubectl apply -f kubernetes/database/postgres.yaml
```

<!-- test: timeout=300; contains=roll out complete; output -->
```bash
kubectl rollout status statefulset/postgres --timeout=240s
```

```text
Waiting for 1 pods to be ready...
partitioned roll out complete: 1 new pods have been updated...
```

<!-- test: contains=Bound; contains=postgres-0; output -->
```bash
kubectl get pods,pvc -l app=postgres
kubectl get pvc
```

```text
NAME             READY   STATUS    RESTARTS   AGE
pod/postgres-0   1/1     Running   0          20s

NAME                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-postgres-0   Bound    pvc-75001b56-51db-4231-9bcf-e1b7b24d6547   1Gi        RWO            standard       <unset>                 20s
NAME              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-postgres-0   Bound    pvc-75001b56-51db-4231-9bcf-e1b7b24d6547   1Gi        RWO            standard       <unset>                 20s
```

The PersistentVolumeClaim `data-postgres-0` is `Bound`: kind's default StorageClass (`standard`, a local-path
provisioner) created a volume for it on the node. Ask PostgreSQL itself:

<!-- test: contains=PostgreSQL 18; output -->
```bash
kubectl exec postgres-0 -- psql -U bookshop -d bookshop -tAc 'select version();'
```

```text
PostgreSQL 18.6 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
```

The foundation is in place. Next: the first application, [02 · node-api](02-node-api.md).
