# 10 · Resources, scaling, rolling updates, rollbacks

> Goal: you can size containers, scale them, ship a new version and take it back, and you understand why bad
> changes stop by themselves. Level 18 of the [roadmap](../README.md#4-the-roadmap). Time: about 60 minutes.

## The walk

### 1. Resources: kubernetes/13

Read [docs/09](../docs/09-resources-requests-and-limits.md), then run [kubernetes/13-resources.md](../kubernetes/13-resources.md).
Watch for the moment python-api gets 24 MiB:

```text
python-api-798f8bf4fb-82h5h  OOMKilled exit 137
```

Exit code 137 = 128 + signal 9: the kernel killed the process at its memory limit. And then the more important
moment: nobody noticed. The two old Pods kept serving, because the rolling update waited for the new Pod to be Ready,
which it never was:

```text
Waiting for deployment "python-api" rollout to finish: 1 out of 2 new replicas have been updated...
error: timed out waiting for the condition
```

A rollout that does not finish is a signal. `rollout undo` brings back the previous Pod template.

### 2. Scaling and versions: kubernetes/14

Read [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md), then run [kubernetes/14-scaling-rolling-updates.md](../kubernetes/14-scaling-rolling-updates.md).
Watch for:

- **Two ReplicaSets** after the update to 1.1.0: the new one with all Pods, the old one kept at 0:

  ```text
  NAME                  DESIRED   CURRENT   READY   AGE
  node-api-698cbcbcdd   3         3         3       81s
  node-api-6f678b5b5    0         0         0       6m40s
  ```

  The old ReplicaSet is the rollback: undo just scales it up again.
- **The history**, with the change cause you recorded:

  ```text
  REVISION  CHANGE-CAUSE
  3         <none>
  4         node-api 1.1.0
  ```

  (Your revision numbers depend on how often you changed the Deployment before; lessons 11 and 13 also created
  revisions.)

## Expert commentary

- **Requests are promises to the scheduler, limits are walls.** Set memory requests close to real use and the limit
  with headroom; for the JVM, set `-XX:MaxRAMPercentage` so the heap fits inside the limit (java-api does).
- **CPU limits throttle, memory limits kill.** Slow requests with no errors can be CPU throttling; restarts with
  exit 137 are memory.
- **Rollbacks need immutable tags.** `node-api:1.0.0` still exists after you shipped 1.1.0. With `latest`, "the
  previous version" is gone the moment you push.
- **`kubectl scale` and `rollout undo` change the live object, not your files.** After an emergency, fix the YAML in
  Git and apply it, or the next deploy undoes your fix.
- **Interview angle:** "A deployment is half-rolled-out and stuck. What happened and what do you do?" New Pods never
  became Ready (crash, OOM, probe, image). Investigate the new Pods' events and logs, then fix forward or undo.

## Checkpoint

- [ ] You caused an OOMKilled container and read exit code 137 from the Pod status.
- [ ] You can explain why the bad resource change did not cause an outage.
- [ ] You shipped 1.1.0 and rolled back to 1.0.0, and can explain what a revision and a ReplicaSet are.

Next: [11 · Troubleshooting](11-troubleshooting.md)
