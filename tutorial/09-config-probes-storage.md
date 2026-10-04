# 09 · Configuration, health probes, storage

> Goal: you have seen configuration changes, probe decisions and persistent storage happen on a live platform.
> Levels 15–17 of the [roadmap](../README.md#4-the-roadmap). Time: about 75 minutes.

## The walk

### 1. Configuration: kubernetes/10 (level 15)

Read [docs/07](../docs/07-configmaps-and-secrets.md), then run [kubernetes/10-config-and-secrets.md](../kubernetes/10-config-and-secrets.md).
The key moment is the value that does **not** change:

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080", APP_ENV: "kubernetes" };
```

You patched the ConfigMap, and the running frontend still shows the old value. Environment variables are copied
when a container starts. After `rollout restart`:

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080/?from=kubernetes", APP_ENV: "kubernetes" };
```

Then the Secret demo: `c3VwZXItc2VjcmV0` decodes to `super-secret` with one command. Base64 is an encoding, not
encryption.

### 2. Health probes: kubernetes/11 (level 16)

Read [docs/08](../docs/08-health-probes.md), then run [kubernetes/11-health-probes.md](../kubernetes/11-health-probes.md).
**Don't skip this one.** The database disappears, and every API reacts correctly:

```text
NAME                          READY   STATUS    RESTARTS   AGE
java-api-64578ccddb-srwvq     0/1     Running   0          5m19s
node-api-6f678b5b5-kjn8h      0/1     Running   0          49s
node-api-6f678b5b5-l2dnl      0/1     Running   0          50s
python-api-54c69f569b-dwlkk   0/1     Running   0          5m46s
python-api-54c69f569b-fkbk2   0/1     Running   0          5m46s
```

`0/1` (not ready, so no traffic) and `RESTARTS 0` (alive, so no restart). From outside:

```text
no available server

HTTP 503
```

When the database returns, nothing is restarted: the readiness probes pass again and the Pods rejoin their Services.
Then the opposite case, a broken liveness probe: `Liveness probe failed: HTTP probe failed with statuscode: 404`, and
the kubelet kills the container.

### 3. Storage: kubernetes/12 (level 17)

Read [docs/10](../docs/10-storage-and-databases.md), then run [kubernetes/12-storage.md](../kubernetes/12-storage.md).
You delete the database Pod; the StatefulSet recreates `postgres-0` with the same claim, and the user you added is
still there:

```text
1 Ada Lovelace
2 Grace Hopper
3 Linus Torvalds
7 Margaret Hamilton
```

(Why 7 and not 4? Two node-api replicas seeded the table at the same time; `ON CONFLICT DO NOTHING` still consumes
sequence numbers. Real data, real gaps: IDs are identifiers, not counters.)

## Expert commentary

- **A ConfigMap change is a time bomb** until the next restart: the change is invisible, and one day an unrelated
  restart picks it up. Restart deliberately after a change, or use tools that roll Deployments when their ConfigMap
  changes. The capstone's scenario is built on this.
- **Readiness is a traffic decision, liveness is a life-or-death decision.** Make liveness boring (is the process
  alive?) and put dependency checks only in readiness.
- **Data lifetime ≠ Pod lifetime ≠ cluster lifetime.** The table at the end of lesson 12 is worth memorising, and so
  is its last sentence: a database in Kubernetes needs backups, tested restores and upgrades before it is production
  data.
- **Interview angle:** "The database is down. What should your APIs' probes do?" Readiness fails (stop traffic),
  liveness keeps passing (no restart storm).

## Checkpoint

- [ ] You can explain why the patched ConfigMap did not change the running frontend.
- [ ] You watched all five API Pods go `0/1` with 0 restarts, and come back without restarts.
- [ ] You can explain what survives deleting a Pod, a StatefulSet, a PVC, the cluster.

Next: [10 · Resources, scaling, rollouts](10-resources-scaling-rollouts.md)
