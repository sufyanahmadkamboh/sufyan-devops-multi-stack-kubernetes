# 12 · Capstone

> Goal: the complete platform, deployed from nothing with one script, verified by 22 checks, and repaired after
> three weekend changes. Level 20 of the [roadmap](../README.md#4-the-roadmap). Time: about 90 minutes.

## Before you start

Optional but recommended: run [kubernetes/cleanup.md](../kubernetes/cleanup.md) first, so Part A really starts from
nothing. The images stay in Docker, so it is faster than the first time.

## The walk

### 1. Part A: read deploy.sh, then run it

Open [capstone/deploy.sh](../capstone/deploy.sh) and read it before you run it. Every step is one you did by hand in
chapters 04–08, in the same order: images, cluster and ingress controller, images into the cluster, namespace and
configuration and generated Secrets, database, migration Job, applications, Ingress, first report. Then run Part A of
[capstone/README.md](../capstone/README.md).

Notice that the script is **idempotent**: on an existing cluster it reports `unchanged` and moves on. A deployment
script you are afraid to run twice is a script you will not run in an emergency.

### 2. Part B: verify

Run Part B. Read [capstone/verify.sh](../capstone/verify.sh) while it runs: each check is a sentence from this course
turned into a command (requests and limits everywhere, probes everywhere, no `latest`, non-root, the password not in
the ConfigMap, every route through the Ingress, data surviving the database Pod's deletion).

### 3. Part C: Monday morning

Run `break.sh` **without reading it**. Then verify. In the test run, the result was:

```text
  PASS  6 Deployments, all Available
  FAIL  no Deployment is stuck in the middle of a rollout
        ['go-status', 'java-api']
  ...
  FAIL  Python: /api/stats (with a report)
  FAIL  Go: /api/status, every service up
        5 6

19 passed, 3 failed
```

Look at the first line again: **all six Deployments are Available**, and the platform is still broken. Rolling
updates kept old Pods serving, so "Available" alone says nothing about whether your last change worked. That is why
the second check exists.

Fix the three problems using only `get`, `describe`, `logs`, endpoints, events and `rollout history`. For each one,
write symptom → command that showed the cause → root cause → fix. Only then open the solution in the capstone README
and compare.

## Expert commentary

- **The incident note matters as much as the fix.** In a real team, the next engineer learns from your four lines
  (symptom, evidence, cause, fix), not from the fact that it works again.
- **One of the three faults was a ConfigMap change that only bit after a restart.** That is how configuration
  incidents look in real life: the change and the outage are hours apart. Look at what changed recently, not only at
  what restarted recently.
- **Interview angle:** "Tell me about a time you debugged a production problem." This capstone is a complete,
  honest story: three symptoms, how you found each cause, the fixes, and what you would change (an alert on stuck
  rollouts, restarting deliberately after config changes).

## Checkpoint

- [ ] `deploy.sh` built the platform from nothing and `verify.sh` printed `22 passed, 0 failed`.
- [ ] You found all three weekend changes yourself before reading the solution.
- [ ] You wrote an incident note: what broke, the impact, how you found it, the fix, how to prevent it.

Next: [13 · Knowledge check](13-knowledge-check.md)
