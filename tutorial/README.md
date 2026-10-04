# The Multi-Stack Applications on Kubernetes Training Course

This is the guided path through the whole repository. Think of it as a senior DevOps engineer sitting next to you
while you take seven applications from their source code to a Kubernetes cluster: we decide what to run next, look at
the output together, break things on purpose, investigate, and fix them.

**The commands live in the lessons, not here.** Every chapter tells you which lesson (or which steps of it) to run
now, what to watch for while it runs, and what an experienced engineer thinks about when they see that output. The
lessons are tested end to end ([tests/](../tests/README.md)), so the commands you type are the ones that were proven
to work. The output excerpts quoted in this course are copied from those real runs; your IDs, ages and timestamps
will differ.

| Chapter | What you do | Levels | Time |
|---|---|---|---|
| [00 · Start here](00-start-here.md) | Check your tools, clone the repo, tour it, meet the Bookshop platform, see how the tests prove the outputs | – | 30 min |
| [01 · The platform and the contract](01-the-platform-and-the-contract.md) | Understand the architecture and the one contract every service follows | 1–2 | 45 min |
| [02 · Dockerize every stack](02-dockerize-every-stack.md) | Seven applications, seven Dockerfiles, seven containers, compared side by side | 3–4 | 3 h |
| [03 · Docker Compose](03-docker-compose.md) | The whole platform on one machine: networks, volumes, health-aware start order | 5–6 | 60 min |
| [04 · From Compose to Kubernetes](04-compose-to-kubernetes.md) | The mapping, a kind cluster with an ingress controller, namespace, config, secrets, database | 7 | 60 min |
| [05 · Deploy the APIs](05-deploy-the-apis.md) | node-api, python-api, go-status, java-api: one pattern, four languages | 8, 10–12 | 75 min |
| [06 · Deploy the frontend](06-deploy-the-frontend.md) | A React build behind nginx, runtime configuration, one image everywhere | 9 | 30 min |
| [07 · Laravel and the worker](07-laravel-and-the-worker.md) | Two containers in one Pod, a migration Job, a JavaScript CronJob | 13 | 45 min |
| [08 · Networking and Ingress](08-networking-and-ingress.md) | Services, EndpointSlices, one entry point for everything | 14 | 45 min |
| [09 · Config, probes, storage](09-config-probes-storage.md) | Change configuration, take the database away, delete the database Pod | 15–17 | 75 min |
| [10 · Resources, scaling, rollouts](10-resources-scaling-rollouts.md) | OOMKilled, scale out, v1.0.0 → v1.1.0 → back | 18 | 60 min |
| [11 · Troubleshooting](11-troubleshooting.md) | Twelve failures, investigated like an on-call engineer | 19 | 3 h |
| [12 · Capstone](12-capstone.md) | Deploy everything with one script, verify 22 checks, fix three weekend changes | 20 | 90 min |
| [13 · Knowledge check](13-knowledge-check.md) | The skills checklist per level and 20 self-test questions | – | 30 min |

About 17 hours in total, spread over as many sessions as you like. Chapters 04–12 use the same kind cluster; between
sessions you can leave it running, or stop Docker and start it again later (the cluster comes back with it).

## How to use it

1. Keep two windows open: this chapter, and the lesson it sends you to.
2. Type the commands yourself. Copy and paste is fine, but read each command before you run it.
3. Before you read the explanation under an output, look at your own terminal and guess what it means.
4. When a chapter says "don't fix it yet", don't. The investigation is the lesson.
5. Keep a notebook (or a text file): one line per chapter with the thing that surprised you most. That file becomes
   your own runbook.
6. After each chapter, do its checkpoint list honestly. If you cannot tick an item, go back to that step.

Ready? Open [00 · Start here](00-start-here.md).
