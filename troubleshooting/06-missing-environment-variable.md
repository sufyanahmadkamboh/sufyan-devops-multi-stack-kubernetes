# 06 · A missing environment variable

> Time: 10 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

While "simplifying" the python-api manifest, someone removes the `DB_PASSWORD` variable:

<!-- test: contains=env updated -->
```bash
kubectl set env deployment/python-api DB_PASSWORD-
```

## Problem

The new python-api Pod crashes immediately; the statistics still work, but only thanks to the old Pods.

## Symptoms

<!-- test: retry=60; contains=CrashLoopBackOff; output -->
```bash
kubectl get pods -l app=python-api
```

```text
NAME                          READY   STATUS             RESTARTS     AGE
python-api-54c69f569b-2wcr5   1/1     Running            0            75s
python-api-54c69f569b-tht6x   1/1     Running            0            81s
python-api-6c4855688b-pvsbp   0/1     CrashLoopBackOff   1 (6s ago)   11s
```

## Investigation

Crashing → read the previous container's logs. Then compare the container's environment with what the application
needs ([docs/CONTRACT.md](../docs/CONTRACT.md): `DB_PASSWORD` is required, with no default).

## Commands

<!-- test: contains=DB_PASSWORD; output -->
```bash
NEW=$(kubectl get pods -l app=python-api --sort-by=.metadata.creationTimestamp -o name | tail -1)
kubectl logs $NEW --previous
```

```text
python-api: FATAL: the environment variable DB_PASSWORD is not set (the database password is required)
```

<!-- test: absent=DB_PASSWORD; contains=DB_HOST; output -->
```bash
kubectl get deployment python-api -o jsonpath='{.spec.template.spec.containers[0].env[*].name}'; echo
```

```text
DB_HOST DB_PORT DB_NAME DB_USER
```

## Root cause

The Pod template no longer defines `DB_PASSWORD`. The application refuses to start without it, with a clear message
and exit code 1, instead of starting and failing on every request later. That clear message is a design choice of
this lab's applications; many programs fail far less clearly.

## Fix

Re-apply the manifest: it defines the variable (from the Secret `db-credentials`).

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/python-api/deployment.yaml
kubectl rollout status deployment/python-api --timeout=240s
```

## Verification

<!-- test: retry=30; contains=DB_PASSWORD; absent=CrashLoopBackOff; absent=Error; absent=Terminating; output -->
```bash
kubectl get pods -l app=python-api
kubectl get deployment python-api -o jsonpath='{.spec.template.spec.containers[0].env[*].name}'; echo
```

```text
NAME                          READY   STATUS    RESTARTS   AGE
python-api-54c69f569b-2wcr5   1/1     Running   0          78s
python-api-54c69f569b-tht6x   1/1     Running   0          84s
DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
```

<!-- test: retry=15; contains="users" -->
```bash
curl -s http://bookshop.localhost:8080/api/stats
```

## Lesson learned

- Configuration errors usually appear at startup: `kubectl logs --previous`.
- Applications should fail fast with a message that names the missing setting.
- If the variable referred to a Secret key that does not exist, the container would not even start: the Pod shows
  `CreateContainerConfigError`, and `kubectl describe pod` names the missing key.
