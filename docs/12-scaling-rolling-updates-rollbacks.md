# 12 · Scaling, rolling updates and rollbacks

> Time: 25 minutes

## Replicas

A Deployment keeps a number of identical Pods running: `replicas: 2` in
[kubernetes/node-api/deployment.yaml](../kubernetes/node-api/deployment.yaml). More replicas give you:

- **availability**: one Pod crashes or its node fails, the others keep serving;
- **capacity**: the Service spreads requests over all Ready Pods;
- **zero-downtime updates**: there is always an old Pod serving while a new one starts.

Change the number on the fly:

```text
kubectl -n bookshop scale deployment node-api --replicas=3
kubectl -n bookshop get pods -l app=node-api
```

The Service picks up the new Pod as soon as it is **Ready**. Note: `kubectl scale` changes the live object only. The
next `kubectl apply` of the YAML sets the replicas back to the file's value, so permanent changes belong in the file.

## How a Deployment changes versions: ReplicaSets

A Deployment does not manage Pods directly. It manages **ReplicaSets**, one per version of the Pod template:

```text
 Deployment node-api
 ├── ReplicaSet node-api-6f678b5b5   (image node-api:1.0.0)  revision 1
 └── ReplicaSet node-api-7c9d8f4b6   (image node-api:1.1.0)  revision 2   ← current
```

Every change to the Pod template (image, env, probes, resources) creates a new ReplicaSet: a new **revision**. Old
ReplicaSets are kept (scaled to 0), which is what makes a rollback instant.

## Rolling update

The default strategy is `RollingUpdate`: replace Pods a few at a time.

```text
 strategy:
   type: RollingUpdate
   rollingUpdate:
     maxSurge: 25%          ← how many extra Pods above "replicas" may exist during the update (rounded up)
     maxUnavailable: 25%    ← how many Pods below "replicas" may be unavailable (rounded down)
```

With `replicas: 2`: maxSurge 25 % of 2 → rounded **up** to 1, maxUnavailable 25 % of 2 → rounded **down** to 0. So
Kubernetes starts **one** new Pod, waits until it is **Ready**, removes one old Pod, and repeats. At no moment are
fewer than 2 Pods serving.

```text
 v1 v1          start
 v1 v1 v2       new Pod starting (surge)
 v1 v1 v2✓      new Pod Ready
 v1 v2✓         one old Pod removed
 v1 v2✓ v2      next new Pod
 v2✓ v2✓        done
```

**Readiness gates the rollout.** A new Pod that never becomes Ready stops the rollout: the old Pods keep serving and
`kubectl rollout status` waits (and eventually reports `exceeded its progress deadline`). A bad version with a good
readiness probe never takes all traffic.

## The commands

| Command | What it does |
|---|---|
| `kubectl -n bookshop set image deployment/node-api node-api=node-api:1.1.0` | changes the image (container name = image reference): starts a rolling update |
| `kubectl -n bookshop rollout status deployment/node-api` | waits until the rollout has finished (or failed) |
| `kubectl -n bookshop rollout history deployment/node-api` | lists the revisions |
| `kubectl -n bookshop rollout undo deployment/node-api` | goes back to the previous revision |
| `kubectl -n bookshop rollout undo deployment/node-api --to-revision=1` | goes back to a specific revision |
| `kubectl -n bookshop annotate deployment/node-api kubernetes.io/change-cause="1.1.0: ..."` | records **why**: shown in the CHANGE-CAUSE column of `rollout history` |

A rollback is itself a rollout: the old ReplicaSet scales up, the new one down, with the same surge rules.

## Versioned tags make rollbacks meaningful

Revisions record the **image reference**. If you deploy `node-api:latest`, then build a new `latest` and roll back,
the "old" revision still says `node-api:latest`, which now means the new, broken image (or whatever the node has
cached). With `node-api:1.0.0` and `node-api:1.1.0`, a rollback goes back to exactly the image that worked. That is
why this lab never uses `latest` ([docs/04](04-images-tags-and-registries.md)).

## The next step: autoscaling

`kubectl scale` is manual. A **HorizontalPodAutoscaler** (HPA) changes `replicas` automatically, for example to keep
average CPU usage around 70 % of the requests, between a minimum and a maximum number of Pods. It needs the
metrics-server (for CPU and memory) and sensible CPU requests, because it calculates utilisation relative to them.
This lab scales by hand so you can see each step.

## Check yourself

<details><summary>You scaled `node-api` to 3 with `kubectl scale`, then ran `kubectl apply -f kubernetes/node-api/`. How many replicas now?</summary>

2, the value in the file. `kubectl scale` only changed the live object.
</details>

<details><summary>With `replicas: 2` and the default strategy, how many Pods run at most during a rolling update, and how few are Ready at least?</summary>

At most 3 (maxSurge rounds up to 1); at least 2 Ready (maxUnavailable rounds down to 0).
</details>

<details><summary>A new version's readiness probe always fails. What happens to the traffic?</summary>

Nothing changes for users: the new Pod never becomes Ready, so it gets no traffic, and the old Pods are not removed.
The rollout stalls until you fix it or roll back.
</details>

<details><summary>Why does `kubectl rollout undo` work instantly?</summary>

The previous ReplicaSet still exists (scaled to 0). Undo scales it up again; no new template has to be built.
</details>

<details><summary>Why is rolling back between two `latest` images unreliable?</summary>

Both revisions record the same reference, `latest`, so the "previous" revision doesn't identify the image that
worked.
</details>

Next: [13 · Logging and debugging](13-logging-and-debugging.md)
