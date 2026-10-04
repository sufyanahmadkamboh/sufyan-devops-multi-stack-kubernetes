# 07 · ConfigMaps and Secrets

> Time: 20 minutes

Every application in this lab reads its configuration from environment variables (rule 5 of the
[contract](CONTRACT.md)). That is what lets **one image** run on a laptop, in Compose and in Kubernetes. Kubernetes
fills those variables from two kinds of objects.

| | ConfigMap | Secret |
|---|---|---|
| For | non-sensitive settings | passwords, keys, tokens |
| In this lab | `bookshop-config` | `db-credentials`, `laravel-app-key` |
| Stored in Git? | yes ([bookshop-config.yaml](../kubernetes/config/bookshop-config.yaml)) | **never**: created with `kubectl`, only an [example](../kubernetes/secrets/db-credentials.example.yaml) is committed |
| Values in the object | plain text | base64-encoded |
| Access control | normal | can be restricted separately (RBAC), not shown in `kubectl describe` |

## The ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bookshop-config
  namespace: bookshop
data:
  DB_HOST: postgres
  DB_PORT: "5432"              # values are always strings: quote numbers
  DB_NAME: bookshop
  DB_USER: bookshop
  STATS_URL: http://python-api:8000/api/stats
  STATUS_URL: http://go-status:8080/api/status
  ADMIN_URL: http://admin.bookshop.localhost:8080
  TARGETS: >-
    frontend=http://frontend:8080/health,node-api=http://node-api:3000/health,...
```

One object holds the settings several services share. Change the database name here, and every service that reads
`DB_NAME` picks it up (after a restart, see below).

## The Secrets

They are created from **generated** values, so no password ever exists in a file:

```text
kubectl -n bookshop create secret generic db-credentials --from-literal=DB_PASSWORD="$(openssl rand -hex 16)"
kubectl -n bookshop create secret generic laravel-app-key --from-literal=APP_KEY="base64:$(openssl rand -base64 32)"
```

The same password is used by PostgreSQL (`POSTGRES_PASSWORD`) and by every client (`DB_PASSWORD`): both read the key
`DB_PASSWORD` of the same Secret, so they can never get out of sync.

## Getting values into the container

### One variable at a time: `valueFrom`

What every Deployment in this lab does:

```yaml
          env:
            - name: DB_HOST
              valueFrom: { configMapKeyRef: { name: bookshop-config, key: DB_HOST } }
            - name: DB_PASSWORD                     # the only secret value, from a Secret, never from the ConfigMap
              valueFrom: { secretKeyRef: { name: db-credentials, key: DB_PASSWORD } }
```

Explicit: you see exactly which variables a container gets, and a typo in a key name stops the Pod with a clear
error (`CreateContainerConfigError: couldn't find key ...`).

### Everything at once: `envFrom`

```yaml
          envFrom:
            - configMapRef: { name: bookshop-config }
```

Shorter, but every key becomes a variable, including ones the application does not need (`TARGETS` in `node-api`),
and you no longer see in the Deployment what the container depends on. The lab uses `valueFrom` for clarity.

Both can also be **mounted as files** (a volume of type `configMap` or `secret`): useful for whole configuration files
such as an nginx config.

## base64 is not encryption

```text
kubectl -n bookshop get secret db-credentials -o jsonpath='{.data.DB_PASSWORD}'              → <the value in base64>
kubectl -n bookshop get secret db-credentials -o jsonpath='{.data.DB_PASSWORD}' | base64 -d  → <the password itself>
```

base64 is an **encoding** (so binary values fit into YAML), not a protection. Anyone who can read the Secret object
can read the value. What Secrets do give you:

| Protection | How |
|---|---|
| **Not in the image** | the value is injected at run time; `docker history` shows nothing |
| **Not in Git** | the lab creates Secrets with `kubectl create secret`; only an example with a fake value is committed |
| **Separate permissions** | RBAC can allow a team to read ConfigMaps but not Secrets |
| **Not printed by default** | `kubectl describe secret` shows sizes, not values |
| **Encryption at rest** | when the cluster is configured for it (managed clusters usually offer it), etcd stores Secrets encrypted |

For production, teams often keep the real values in an external secret manager (AWS Secrets Manager, HashiCorp
Vault, ...) and sync them into Kubernetes, or encrypt them for Git (Sealed Secrets, SOPS). The rule never changes:
**never commit a real secret, not even base64-encoded.**

## Changing configuration

Environment variables are read **once, when the container starts**. Editing the ConfigMap or Secret does not change
running containers:

```text
kubectl -n bookshop edit configmap bookshop-config          # change a value
kubectl -n bookshop rollout restart deployment node-api     # new Pods start with the new value
```

`rollout restart` replaces the Pods one by one (a rolling update), so the service stays available. Values mounted as
**files** are updated in the running container after a short delay, but the application must re-read the file to
notice.

## Check yourself

<details><summary>Why is <code>DB_PASSWORD</code> not in the ConfigMap, although it is "just another setting"?</summary>

It is sensitive. Secrets can be protected separately (RBAC, encryption at rest) and are never committed to Git;
ConfigMaps are plain configuration meant to be versioned.
</details>

<details><summary>Someone says "our password is safe, it is base64-encoded in the Secret". Is it?</summary>

No. `base64 -d` reverses it instantly. Protection comes from who may read the Secret (RBAC), from encryption at rest,
and from keeping the value out of Git and images.
</details>

<details><summary>You change <code>DB_NAME</code> in the ConfigMap. Why do the running node-api Pods still use the old one?</summary>

Environment variables are set when the container starts. Run `kubectl rollout restart deployment node-api` to start
new Pods with the new value.
</details>

<details><summary>What happens when a Deployment references a Secret key that does not exist?</summary>

The container cannot be created: the Pod shows `CreateContainerConfigError`, and `kubectl describe pod` names the
missing key.
</details>

<details><summary><code>env</code> + <code>valueFrom</code> or <code>envFrom</code>: what is the trade-off?</summary>

`valueFrom` is explicit (you see each variable and its source) but longer; `envFrom` imports every key of the object
in one line but hides what the container really depends on.
</details>

Next: [08 · Health probes](08-health-probes.md)
