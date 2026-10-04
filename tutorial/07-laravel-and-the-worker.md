# 07 · Laravel and the worker

> Goal: you can tell when a program is a Deployment, a Job or a CronJob, and when two containers belong in one Pod.
> Level 13 of the [roadmap](../README.md#4-the-roadmap). Time: about 45 minutes.

## The walk

### 1. Read docs/14 and docs/15

[docs/14](../docs/14-jobs-and-cronjobs.md) (Jobs and CronJobs) and [docs/15](../docs/15-multi-container-pods.md)
(multi-container Pods). Ten minutes, and the next two lessons make sense at once.

### 2. Laravel: kubernetes/07

Run [kubernetes/07-laravel-admin.md](../kubernetes/07-laravel-admin.md). Three things to watch:

- **The migration runs as a Job, once**, before the application. Its log:

  ```text
     INFO  Running migrations.

    2026_10_04_000001_create_reviews_table ......................... 4.89ms DONE
  ```

  Running migrations inside every replica at startup is a classic incident: two replicas migrating at the same time.
  A Job runs them once per release.

- **One Pod, two containers:**

  ```text
  NAME                           READY   STATUS    RESTARTS   AGE
  laravel-admin-cbd8498c-9tx8k   2/2     Running   0          1s
  ```

  `2/2` means both containers are ready. nginx reaches PHP-FPM at `127.0.0.1:9000` because containers in a Pod share
  one network namespace. In Compose these were two services talking over a network.

- **`kubectl logs -c laravel-fpm`:** with several containers you must say which one.

### 3. report-worker: kubernetes/08

Run [kubernetes/08-report-worker.md](../kubernetes/08-report-worker.md). The worker is JavaScript on Node.js, like
node-api, but it is a different **kind of program**: it does one task and exits.

```text
NAME               READY   STATUS      RESTARTS   AGE
report-now-6pqk4   0/1     Completed   0          5s
... report #1 saved: users=3 books=5 reviews=3 services up=6/6
```

`0/1 Completed` is success for a Job. In a Deployment the same exit would be a failure: Kubernetes would restart it
forever.

## Expert commentary

- **Choose the workload by the program's lifecycle, not by its language.** Runs forever and serves requests →
  Deployment. Runs once and exits → Job. Runs on a schedule → CronJob. Needs a stable identity and its own disk →
  StatefulSet. JavaScript appears in all three of the first categories in this repository.
- **Sidecar or separate Deployment?** Put two containers in one Pod only when they must run, scale and fail together
  and talk over localhost (nginx + its own PHP-FPM). If they could scale independently, make them separate.
- **`concurrencyPolicy: Forbid`** on the CronJob prevents two reports running at once when one is slow. Ask about it
  for every CronJob you review.
- **Interview angle:** "How do you run database migrations on Kubernetes?" A Job per release (or a Helm hook / an
  init step in a pipeline), not in the application's startup in every replica.

## Checkpoint

- [ ] The migration Job is `Complete`, laravel-admin shows `2/2`, a report was saved.
- [ ] You can explain why `0/1 Completed` is good for a Job and bad for a Deployment.
- [ ] You can name the workload type for: an API, a nightly cleanup, a one-time data import, a database.

Next: [08 · Networking and Ingress](08-networking-and-ingress.md)
