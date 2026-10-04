# 14 · Jobs and CronJobs

> Time: 20 minutes

## Three kinds of work

| Workload | Runs | When it ends | In this lab |
|---|---|---|---|
| **Deployment** | forever; restarted whenever it stops | never (until you delete it) | `node-api`, `python-api`, `java-api`, `go-status`, `frontend`, `laravel-admin` |
| **Job** | until it **succeeds** (exit code 0), retried on failure | when it has completed | `laravel-migrate` (database migrations) |
| **CronJob** | creates a **Job** on a schedule | each Job ends; the CronJob stays | `report-worker` |

A server that exits is a problem: a Deployment restarts it. A batch task that exits with 0 is **done**: it must not be
restarted. That is why `report-worker` (it collects statistics, stores one row, and exits) is a CronJob, not a
Deployment. In Compose, the same distinction is a service you start with `docker compose run --rm report-worker`
(and `profiles: [jobs]`, so `docker compose up` doesn't start it).

## The report-worker CronJob

From [kubernetes/report-worker/cronjob.yaml](../kubernetes/report-worker/cronjob.yaml):

```text
spec:
  schedule: "*/10 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      ttlSecondsAfterFinished: 3600
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: report-worker
              image: report-worker:1.0.0
```

| Field | Meaning |
|---|---|
| `schedule: "*/10 * * * *"` | cron syntax: minute, hour, day of month, month, day of week. `*/10` in the minute field = every 10 minutes |
| `concurrencyPolicy: Forbid` | if the previous run is still going, skip this one (`Allow` would run both; `Replace` would stop the old one) |
| `successfulJobsHistoryLimit` / `failedJobsHistoryLimit` | how many finished Jobs (and their Pods, with their logs) to keep |
| `jobTemplate` | the Job that is created at each scheduled time |
| `backoffLimit: 2` | a failing run is retried, then the Job is marked Failed |
| `ttlSecondsAfterFinished: 3600` | delete the finished Job (and its Pods) an hour later |
| `restartPolicy: OnFailure` | restart the container in the same Pod if it fails. Jobs allow only `OnFailure` or `Never`, never `Always` |

Don't wait 10 minutes to test it. Create a Job from the CronJob's template, right now:

```text
kubectl -n bookshop create job report-now --from=cronjob/report-worker
kubectl -n bookshop wait --for=condition=complete job/report-now --timeout=90s
kubectl -n bookshop logs job/report-now
```

## The laravel-migrate Job

Laravel's database migrations must run **once per release**, before the new version serves traffic. Not in every
replica at startup: two replicas starting at the same time would run the same migration twice. From
[kubernetes/laravel-admin/migrate-job.yaml](../kubernetes/laravel-admin/migrate-job.yaml):

```text
spec:
  backoffLimit: 4                      # the database may still be starting: retry a few times
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: laravel-fpm:1.0.0
          args: ["php", "artisan", "migrate", "--force", "--seed"]
```

| Field | Why |
|---|---|
| `image: laravel-fpm:1.0.0` | the **same image** as the application: the migrations are part of the code of that release |
| `args:` (not `command:`) | replaces only the CMD, so the image's entrypoint still runs and checks that `APP_KEY` and `DB_PASSWORD` are set |
| `restartPolicy: Never` + `backoffLimit: 4` | each retry is a new Pod (each failed Pod stays for inspection), up to 4 retries |
| `--force` | Laravel refuses to migrate in production without it |

A Job's spec cannot be changed after it is created. For the next release, delete the old Job (or let
`ttlSecondsAfterFinished` remove it) and apply the new one. Deployment tools such as Helm hooks or Argo CD sync waves
automate "migrate first, then roll out".

## Check yourself

<details><summary>Why is `report-worker` a CronJob and not a Deployment?</summary>

It finishes its work and exits with 0. A Deployment would restart it immediately, forever. A CronJob runs it as a Job
on a schedule, and a completed Job is not restarted.
</details>

<details><summary>What does `concurrencyPolicy: Forbid` prevent?</summary>

Two report runs at the same time: if the previous run hasn't finished when the next scheduled time arrives, the new
run is skipped.
</details>

<details><summary>How do you run the CronJob's work once, now?</summary>

`kubectl -n bookshop create job report-now --from=cronjob/report-worker`.
</details>

<details><summary>Why don't the Laravel Pods run their migrations at startup?</summary>

Every replica would run them, possibly at the same time. A Job runs them once per release, before the new version
serves traffic.
</details>

<details><summary>Which `restartPolicy` values can a Job's Pod use?</summary>

`OnFailure` or `Never`. `Always` is only for long-running workloads such as Deployments.
</details>

Next: [15 · Multi-container Pods](15-multi-container-pods.md)
