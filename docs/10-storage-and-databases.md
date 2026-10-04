# 10 · Storage and databases

> Time: 25 minutes

## A container's files do not survive

Everything a container writes to its own filesystem disappears when the container is replaced. In Kubernetes that
happens all the time: a new image version, a node restart, a crash, a rescheduled Pod. For stateless services
(`node-api`, `go-status`, `frontend`, ...) that is fine: their state lives in PostgreSQL. For **PostgreSQL itself** it
would be a disaster.

In Compose, the database keeps its files in a named volume:

```text
services:
  postgres:
    volumes:
      - pgdata:/var/lib/postgresql
volumes:
  pgdata: {}
```

Kubernetes has the same idea, split into three objects.

## PV, PVC and StorageClass

```text
 Pod ──mounts──► PersistentVolumeClaim (PVC)  "I need 1Gi, ReadWriteOnce"      ← you write this
                         │ bound to
                         ▼
                 PersistentVolume (PV)        the real piece of storage          ← created for you
                         ▲
                         │ created by
                 StorageClass "standard"      how to create volumes on demand   ← the cluster provides this
```

| Object | Who creates it | What it is |
|---|---|---|
| **PersistentVolumeClaim** | you (or a StatefulSet for you) | a request for storage: size and access mode |
| **PersistentVolume** | usually the StorageClass's provisioner | the actual storage: a cloud disk, an NFS share, a local directory |
| **StorageClass** | the cluster administrator | the recipe for creating PVs on demand |

In this lab, kind ships a StorageClass called `standard` that uses the *local-path* provisioner: each volume is a
directory on the kind node (a Docker container on your computer). Real clusters use cloud disks (for example EBS on
AWS) through their CSI drivers. The manifests don't change: only the StorageClass behind them.

Access modes: `ReadWriteOnce` (one node mounts it read-write; normal for databases), `ReadOnlyMany`, `ReadWriteMany`
(many nodes at once; needs shared storage such as NFS or EFS).

## The lab's PostgreSQL: a StatefulSet

From [kubernetes/database/postgres.yaml](../kubernetes/database/postgres.yaml):

```text
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  ...
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

Why a **StatefulSet** and not a Deployment?

| | Deployment | StatefulSet |
|---|---|---|
| Pod names | random (`node-api-6f678b5b5-kxsnl`) | stable and ordered (`postgres-0`, `postgres-1`, ...) |
| Storage | all replicas share whatever you mount | `volumeClaimTemplates`: **each** Pod gets its own PVC (`data-postgres-0`) |
| After a restart | a new Pod with a new name | the same name, re-attached to the same PVC |
| Use for | stateless services | databases, queues, anything with an identity and its own data |

The Service in front of it is **headless** (`clusterIP: None`): the name `postgres` resolves straight to the Pod's
IP. With several replicas, each one would also get its own DNS name (`postgres-0.postgres`), which database
replication needs.

The `fsGroup: 70` in the Pod's security context makes the volume writable for the `postgres` user of the alpine image.

## How long does the data live?

| You delete ... | The data |
|---|---|
| the Pod `postgres-0` | survives: the StatefulSet recreates the Pod and re-attaches `data-postgres-0` |
| the StatefulSet | survives: the PVC is **not** deleted with it |
| the PVC `data-postgres-0` | **gone** (with the default reclaim policy `Delete` of local-path and most cloud StorageClasses) |
| the namespace `bookshop` | **gone**: the PVC is deleted with the namespace |
| the kind cluster | **gone**: the node containers, and the directories in them, are deleted |

## Databases need special care

Running PostgreSQL in Kubernetes is possible, and this lab does it so everything runs on one laptop. But be clear
about what this lab's database **is not**:

- **No backups.** Nothing copies the data anywhere. One deleted PVC and it is lost.
- **No high availability.** One replica. If its node fails, the database is down until the Pod runs again.
- **No upgrade procedure.** A major version upgrade of PostgreSQL needs a data migration, not just a new image tag.
- **No tuning, monitoring or connection pooling.**

**This single-replica PostgreSQL is fine for learning and not production-ready.** In production, teams either use
a **managed database** (Amazon RDS, Azure Database for PostgreSQL, Cloud SQL), which handles backups, failover and
patching, or run PostgreSQL in Kubernetes with a database **operator** (such as CloudNativePG), which automates
replication, backups and failover.

## Check yourself

<details><summary>Why doesn't `node-api` need a PersistentVolumeClaim?</summary>

It stores nothing on its own filesystem: its data is in PostgreSQL. Any replica can be replaced at any time without
losing anything.
</details>

<details><summary>What do `volumeClaimTemplates` give a StatefulSet that a Deployment doesn't have?</summary>

Each Pod gets its own PVC (`data-postgres-0`, `data-postgres-1`, ...), and a recreated Pod re-attaches to the same
PVC.
</details>

<details><summary>You run `kubectl delete pod postgres-0`. Is the data lost?</summary>

No. The StatefulSet creates `postgres-0` again and mounts the same PVC, `data-postgres-0`.
</details>

<details><summary>What does the StorageClass `standard` do in kind, and what would replace it on AWS?</summary>

It creates volumes on demand as directories on the kind node (local-path provisioner). On AWS, a StorageClass using
the EBS CSI driver creates EBS disks instead; the PVC stays the same.
</details>

<details><summary>Name three things this lab's database lacks for production.</summary>

Backups, high availability (replication and failover), and an upgrade procedure. Also monitoring, tuning and
connection pooling.
</details>

Next: [11 · Services, networking and Ingress](11-services-networking-and-ingress.md)
