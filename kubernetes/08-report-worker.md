# 08 · Run report-worker (JavaScript) as a CronJob

> Time: 10 minutes. The application: [applications/report-worker](../applications/report-worker/README.md).
> The concepts: [docs/14 · Jobs and CronJobs](../docs/14-jobs-and-cronjobs.md).

report-worker is JavaScript too, like node-api, but it is a different kind of program: it does one task and exits.
A Deployment would restart it forever ("it stopped, bring it back"). Kubernetes has a workload type for programs that
should run **to completion**: the Job, and the CronJob, which creates Jobs on a schedule.

| Compose | Kubernetes |
|---|---|
| `profiles: [jobs]` + `docker compose run --rm report-worker` | CronJob `report-worker`, schedule `*/10 * * * *` |
| run it once by hand | `kubectl create job --from=cronjob/report-worker` |

<!-- test: timeout=300; contains=report-worker:1.0.0 -->
```bash
kind load docker-image report-worker:1.0.0 --name bookshop
```

<!-- test: contains=cronjob.batch/report-worker created; output -->
```bash
kubectl apply -f kubernetes/report-worker/
kubectl get cronjob report-worker
```

```text
cronjob.batch/report-worker created
NAME            SCHEDULE       TIMEZONE   SUSPEND   ACTIVE   LAST SCHEDULE   AGE
report-worker   */10 * * * *   <none>     False     0        <none>          0s
```

Don't wait ten minutes: create a Job from the CronJob's template right now.

<!-- test: timeout=300; contains=condition met -->
```bash
kubectl create job report-now --from=cronjob/report-worker
kubectl wait --for=condition=complete job/report-now --timeout=240s
```

<!-- test: contains=saved; output -->
```bash
kubectl get pods -l job-name=report-now
kubectl logs job/report-now
```

```text
NAME               READY   STATUS      RESTARTS   AGE
report-now-6pqk4   0/1     Completed   0          5s
2026-10-04T18:19:41.705Z report-worker version 1.0.0 starting: stats from http://python-api:8000/api/stats, status from http://go-status:8080/api/status
2026-10-04T18:19:42.177Z report-worker report #1 saved: users=3 books=5 reviews=3 services up=6/6
```

`Completed`, exit code 0, and the report is in the database:

<!-- test: contains=latest_report; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/api/stats; echo
```

```text
{"users":3,"books":5,"reviews":3,"latest_report":{"id":1,"created_at":"2026-10-04T18:19:42.174963+00:00","users":3,"books":5,"reviews":3,"services_up":6,"services_total":6}}
```

All applications are running. Next: one entry point for all of them, [09 · Ingress](09-ingress.md).
