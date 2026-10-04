# Labs · practical challenges

> After the [Kubernetes lessons](../kubernetes/README.md). Time: about 2 hours for all six.

In the lessons, the files were already written. Here you write them yourself, for a service the repository does
**not** deploy: [quotes-api](quotes-api/app.py), a tiny Python service (standard library only, no dependencies) that
returns a random quote. You take it the whole way, exactly like the seven applications of the platform.

Each lab has: **Task**, **Requirements**, **Hints**, **Expected result**, a hidden **Solution** (tested: every
command in it runs in CI), and an **Explanation**. Try first, then open the solution.

| # | Lab | Skill |
|---|---|---|
| 01 | [Dockerize it yourself](01-dockerize-yourself.md) | Dockerfile, image tags, run, health endpoint |
| 02 | [Add it to Compose, add an environment variable](02-add-to-compose.md) | Compose service, networks, configuration through the environment |
| 03 | [Convert it to Kubernetes](03-convert-to-kubernetes.md) | Deployment, Service, probes, resources, an Ingress path |
| 04 | [Scale it](04-scale.md) | replicas, load balancing across Pods |
| 05 | [Break the Service selector, and fix it](05-break-the-selector.md) | labels, selectors, endpoints |
| 06 | [Upgrade to v2, then roll back](06-upgrade-and-rollback.md) | rolling update, rollout history, undo |

Labs 03–06 need the platform from the [Kubernetes lessons](../kubernetes/README.md) running. Your files go to
`labs/work/` (ignored by Git).
