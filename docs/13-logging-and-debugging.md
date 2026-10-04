# 13 · Logging and debugging

> Time: 30 minutes

## Logs go to stdout and stderr

Every application in this lab writes its logs to **standard output** (stdout) or **standard error** (stderr), never
to files ([docs/CONTRACT.md](CONTRACT.md), rule 6). The container runtime captures those two streams; `docker logs`
reads them in Docker and Compose, `kubectl logs` reads them in Kubernetes. Log files inside a container would be
invisible to both, and lost when the container is replaced.

## kubectl logs

| Command | Shows |
|---|---|
| `kubectl -n bookshop logs deploy/node-api` | the logs of one Pod of the Deployment |
| `kubectl -n bookshop logs <pod>` | the logs of one specific Pod |
| `kubectl -n bookshop logs -f <pod>` | follow: new lines as they arrive (Ctrl+C to stop) |
| `kubectl -n bookshop logs <pod> --previous` | the logs of the **previous**, crashed container: the most important flag for `CrashLoopBackOff` |
| `kubectl -n bookshop logs <pod> -c laravel-fpm` | one container of a multi-container Pod (`laravel-admin` has `laravel-web` and `laravel-fpm`) |
| `kubectl -n bookshop logs -l app=python-api --prefix` | all Pods with that label, each line prefixed with its Pod |
| `kubectl -n bookshop logs job/report-now` | the logs of a Job's Pod |
| `kubectl -n bookshop logs <pod> --since=10m --tail=50` | only recent lines |

Logs disappear with the Pod. Production clusters ship them to a central system (Loki, Elasticsearch, CloudWatch,
...) so they survive and can be searched.

## The debugging commands and the question each one answers

| Command | Answers |
|---|---|
| `kubectl get pods` | does it run? What is the STATUS (Pending, ContainerCreating, ImagePullBackOff, CrashLoopBackOff, Running) and READY (`1/1`)? How many RESTARTS? |
| `kubectl get pods -o wide` | on which node, with which Pod IP? |
| `kubectl describe pod <pod>` | **why**: container state and last state (exit code, `OOMKilled`), probe results, and the **Events** at the bottom (scheduling, image pulls, probe failures) |
| `kubectl logs <pod>` | what did the application itself say? |
| `kubectl exec -it <pod> -- sh` | look from inside: does the app answer on localhost? Is the env variable set? (not possible with distroless images like `go-status`, which have no shell) |
| `kubectl get svc` | which Services exist, their type, ClusterIP and ports |
| `kubectl describe svc <svc>` | the selector, ports, targetPort and the current endpoints |
| `kubectl get endpoints <svc>` / `kubectl get endpointslices` | which Pod IPs the Service really sends traffic to (`<none>` = selector mismatch or no Ready Pod) |
| `kubectl get events --sort-by=.lastTimestamp` | everything that happened in the namespace, newest last |
| `kubectl get deployments` | READY / UP-TO-DATE / AVAILABLE replicas |
| `kubectl rollout status deployment/<d>` | is the rollout progressing, finished or stuck? |
| `kubectl rollout history deployment/<d>` | which revisions exist, for `rollout undo` |

## A decision flow

Start with `kubectl get pods` and follow the status:

```text
 kubectl get pods
 │
 ├── Pending ─────────────► kubectl describe pod → Events
 │                          "Insufficient cpu/memory" (requests), "unbound PersistentVolumeClaim" (storage),
 │                          "untolerated taint", node selector ...
 │
 ├── ErrImagePull / ImagePullBackOff
 │                     ───► kubectl describe pod → Events: wrong image name or tag? image not in the registry
 │                          (or not loaded into kind)? private registry without credentials?
 │
 ├── CrashLoopBackOff ────► kubectl logs <pod> --previous   (the crash reason)
 │                          kubectl describe pod → Last State: exit code, OOMKilled?
 │                          typical: missing env variable or Secret, wrong config, out of memory
 │
 ├── CreateContainerConfigError
 │                     ───► kubectl describe pod → a referenced ConfigMap/Secret or key does not exist
 │
 ├── Running but READY 0/1 ► kubectl describe pod → "Readiness probe failed: ..."
 │                          wrong probe path/port? does the dependency (database) answer?
 │
 └── Running and Ready, but requests fail
        │
        ├── inside the cluster ► kubectl get endpoints <svc>: <none>? → selector/labels mismatch
        │                        kubectl describe svc <svc>: port / targetPort match the container port?
        │                        test from another Pod: kubectl run tmp --rm -it --image=busybox:1.37 -- wget -qO- http://<svc>:<port>/health
        │
        └── only from outside ► the Ingress: kubectl describe ingress bookshop (host, path, backend
                                 Service and port), the ingress controller's logs (kubectl -n traefik logs deploy/traefik)
```

The [troubleshooting labs](../troubleshooting/README.md) walk through each branch with a real failure.

## Check yourself

<details><summary>A Pod is in CrashLoopBackOff and `kubectl logs` shows nothing useful. What next?</summary>

`kubectl logs <pod> --previous`: the current container may just have started; the previous one holds the crash
message. Then `kubectl describe pod` for the exit code and reason (for example OOMKilled).
</details>

<details><summary>How do you read the logs of PHP-FPM in the `laravel-admin` Pod?</summary>

`kubectl -n bookshop logs <laravel-admin-pod> -c laravel-fpm`: name the container, because the Pod has two.
</details>

<details><summary>Everything is Running and Ready, but `curl http://node-api:3000/health` from another Pod fails. Which command first?</summary>

`kubectl get endpoints node-api`. If it shows `<none>`, the Service's selector doesn't match the Pods' labels.
</details>

<details><summary>Why can't you `kubectl exec ... -- sh` into the `go-status` Pod?</summary>

Its image is distroless: it contains only the Go binary, no shell. Debug it with its logs, from another Pod, or with
`kubectl debug` and an ephemeral container.
</details>

<details><summary>Why should applications log to stdout instead of files?</summary>

The container runtime captures stdout/stderr, so `kubectl logs` and log collectors can read them. Files inside the
container are invisible to them and vanish with the container.
</details>

Next: [14 · Jobs and CronJobs](14-jobs-and-cronjobs.md)
