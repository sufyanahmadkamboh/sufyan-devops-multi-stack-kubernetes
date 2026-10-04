# 07 · Deploy laravel-admin (PHP, Laravel)

> Level 13 of the [roadmap](../README.md). Time: 20 minutes. The application: [applications/laravel-admin](../applications/laravel-admin/README.md).
> The concepts: [docs/14 · Jobs](../docs/14-jobs-and-cronjobs.md), [docs/15 · multi-container Pods](../docs/15-multi-container-pods.md).

Laravel brings two new Kubernetes ideas:

```text
 Compose                                    Kubernetes
 laravel-migrate (one-off, then exits)  →   Job laravel-migrate             runs once, to completion
 laravel-fpm  (PHP-FPM, port 9000)      ┐
 laravel-web  (nginx, port 8080)        ┘→  Deployment laravel-admin:       ONE Pod, TWO containers:
                                              laravel-web  ── 127.0.0.1:9000 ──►  laravel-fpm
                                            Service laravel-admin:8080      only nginx is exposed
```

nginx and PHP-FPM always run and scale together, and nginx must reach exactly "its" FPM: containers in one Pod share
the network namespace, so `127.0.0.1:9000` works, with no Service in between.

## Step 1 · Images

<!-- test: timeout=300; contains=laravel-web:1.0.0 -->
```bash
kind load docker-image laravel-fpm:1.0.0 laravel-web:1.0.0 --name bookshop
```

## Step 2 · The migration Job

The `reviews` table must exist before the application serves requests. Migrations run **once per release**, not in
every replica at startup (two replicas migrating at the same time is a classic production incident). That is a Job:

<!-- test: contains=job.batch/laravel-migrate created -->
```bash
kubectl apply -f kubernetes/laravel-admin/migrate-job.yaml
```

<!-- test: timeout=300; contains=condition met; output -->
```bash
kubectl wait --for=condition=complete job/laravel-migrate --timeout=240s
kubectl get job laravel-migrate
```

```text
job.batch/laravel-migrate condition met
NAME              STATUS     COMPLETIONS   DURATION   AGE
laravel-migrate   Complete   1/1           3s         4s
```

<!-- test: contains=reviews; output=tail:6 -->
```bash
kubectl logs job/laravel-migrate
```

```text
...
   INFO  Running migrations.  

  2026_10_04_000001_create_reviews_table ......................... 4.89ms DONE


   INFO  Seeding database.  
```

The Job's Pod stays in `Completed` state so you can read its log; `ttlSecondsAfterFinished: 3600` removes it after an
hour.

## Step 3 · The two-container Deployment

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl apply -f kubernetes/laravel-admin/deployment.yaml -f kubernetes/laravel-admin/service.yaml
kubectl rollout status deployment/laravel-admin --timeout=240s
kubectl get pods -l app=laravel-admin
```

```text
deployment.apps/laravel-admin created
service/laravel-admin created
Waiting for deployment "laravel-admin" rollout to finish: 0 of 1 updated replicas are available...
deployment "laravel-admin" successfully rolled out
NAME                           READY   STATUS    RESTARTS   AGE
laravel-admin-cbd8498c-9tx8k   2/2     Running   0          1s
```

`READY 2/2`: two containers in one Pod. Logs are per container, so name the one you want with `-c`:

<!-- test: contains=laravel-web; contains=laravel-fpm; output -->
```bash
kubectl get pod -l app=laravel-admin -o jsonpath='{.items[0].spec.containers[*].name}'; echo
kubectl logs deploy/laravel-admin -c laravel-fpm --tail=3
```

```text
laravel-web laravel-fpm
[04-Oct-2026 18:19:31] NOTICE: fpm is running, pid 1
[04-Oct-2026 18:19:31] NOTICE: ready to handle connections
127.0.0.1 -  04/Oct/2026:18:19:31 +0000 "GET /index.php" 200
```

## Step 4 · Verify

<!-- test: retry=10; contains=Reviews; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://laravel-admin:8080/ | grep -o '<title>[^<]*</title>'
kubectl exec deploy/node-api -- wget -qO- http://laravel-admin:8080/ready; echo
```

```text
<title>Bookshop · Reviews</title>
{"status":"ready","service":"laravel-admin","version":"1.0.0"}
```

Next: the batch job written in plain JavaScript, [08 · report-worker](08-report-worker.md).
