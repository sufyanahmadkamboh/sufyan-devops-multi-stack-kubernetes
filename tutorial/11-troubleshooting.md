# 11 · Troubleshooting

> Goal: find the root cause of twelve realistic failures from their symptoms, the way an on-call engineer does.
> Level 19 of the [roadmap](../README.md#4-the-roadmap). Time: about 3 hours.

## Before you start

The complete platform is running and healthy (the status board shows 6 of 6). Every lab breaks one thing, makes you
investigate, fixes it and restores the platform completely, so the labs can run in any order. Read
[docs/13](../docs/13-logging-and-debugging.md) first: its decision flow is your map.

## The method

Open [troubleshooting/README.md](../troubleshooting/README.md). Every lab follows the same headings:

```text
Break it → Problem → Symptoms → Investigation → Commands → Root cause → Fix → Verification → Lesson learned
```

How to work through each lab:

1. Run the "Break it" step.
2. **Stop reading.** Look at the symptoms yourself and write down a hypothesis.
3. Then read the investigation and compare it with what you would have done.
4. Fix, verify, and add one line to your runbook: symptom → cause → fix.

## The labs, grouped by the first thing you see

### The Pod never starts: image problems

| Lab | What you see |
|---|---|
| [01 · Wrong image name](../troubleshooting/01-wrong-image-name.md) | `ImagePullBackOff`; the event names the image it could not find |
| [02 · Image pull failure](../troubleshooting/02-image-pull-failure.md) | the image is in your Docker, but not on the cluster's nodes |

```text
go-status-798ff9f56d-fj62r   0/1     ImagePullBackOff   0          17s
Failed to pull image "go-staus:1.0.0": failed to pull and unpack image "docker.io/library/go-staus:1.0.0"
```

Read the image name in the event letter by letter. And notice the old Pod still `Running` next to it: the rolling
update protected the service again.

### The Pod starts and dies: crashes and configuration

| Lab | What you see |
|---|---|
| [05 · Application crashes](../troubleshooting/05-application-crashes.md) | `CrashLoopBackOff`; `logs --previous` shows `Cannot find module '/app/src/servr.js'` |
| [06 · Missing environment variable](../troubleshooting/06-missing-environment-variable.md) | `CrashLoopBackOff` with the application's own message |

```text
python-api: FATAL: the environment variable DB_PASSWORD is not set (the database password is required)
```

`CrashLoopBackOff` is never the cause, only the symptom. The cause is in the **previous** container's log.

### The Pod runs but is never Ready

| Lab | What you see |
|---|---|
| [03 · Wrong container port](../troubleshooting/03-wrong-container-port.md) | probes get `connection refused`: the app listens on another port |
| [07 · Database connection failure](../troubleshooting/07-database-connection-failure.md) | `/ready` answers 503, `/health` 200; the ConfigMap says `postgress` |
| [08 · Readiness probe failure](../troubleshooting/08-readiness-probe-failure.md) | `Readiness probe failed: HTTP probe failed with statuscode: 404`: a typo in the probe path |
| [12 · Incorrect Secret](../troubleshooting/12-incorrect-configmap-secret.md) | `password authentication failed for user "bookshop"` |

The question for all four: what does the **probe** call, and what does the **application** answer? `kubectl get events`
and a request to `/ready` from inside the cluster answer it.

### The Pod is fine, the traffic does not arrive

| Lab | What you see |
|---|---|
| [04 · Service selector mismatch](../troubleshooting/04-service-selector-mismatch.md) | `no available server`, HTTP 503; the Service has no endpoints |
| [10 · Works in the Pod, not through the Service](../troubleshooting/10-works-in-pod-not-through-service.md) | the Service's `TargetPort` is 8080, the app listens on 8000 |
| [11 · Frontend cannot reach a backend](../troubleshooting/11-frontend-cannot-reach-backend.md) | the UI's panel shows an error; a Service port changed |

```text
Port:                     http  8000/TCP
TargetPort:               8080/TCP
Endpoints:                10.244.1.99:8080,10.244.1.98:8080
```

Follow the chain from outside in: Ingress → Service → endpoints → Pod port. The break is always at one link.

### The Pod is never scheduled

| Lab | What you see |
|---|---|
| [09 · Volume problem](../troubleshooting/09-volume-problem.md) | `Pending`; `pod has unbound immediate PersistentVolumeClaims`; `storageclass.storage.k8s.io "fast-ssd" not found` |

`Pending` means "no node yet": the reason is in the scheduler's events, never in a log (no container has started).

## Expert commentary

- **Status column → first command.** `ImagePullBackOff` → `describe` events. `CrashLoopBackOff` → `logs --previous`.
  `Running 0/1` → probe events and `/ready`. `Running 1/1` but unreachable → endpoints and ports. `Pending` → events.
  This table is half of a Kubernetes on-call shift.
- **The rolling update hid several failures.** In labs 01, 03, 05, 06 and 08 the old Pods kept serving. That is
  safety, but also danger: a stuck rollout can stay unnoticed for days. Alert on "rollout not complete".
- **Interview angle:** "A Service returns 503. Walk me through your debugging." Endpoints first (`kubectl get
  endpoints`); empty → selector vs labels, or Pods not Ready; not empty → ports (`targetPort` vs container port).

## Checkpoint

- [ ] You ran all twelve labs and wrote one runbook line per lab.
- [ ] For each status (`ImagePullBackOff`, `CrashLoopBackOff`, `Running 0/1`, `Running 1/1` but unreachable,
      `Pending`) you can name your first command.
- [ ] You can explain why several of the failures caused no outage, and why that is not a reason to ignore them.

Next: [12 · Capstone](12-capstone.md)
