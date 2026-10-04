# The applications

> Levels 2–4 of the [roadmap](../README.md): build each application, Dockerize it, run it as a container.

Seven small applications in six languages and frameworks, all following one [contract](../docs/CONTRACT.md): a port
from the environment, `/health` and `/ready`, configuration from environment variables, logs to stdout, a non-root
user. They are deliberately simple: the subject of this lab is **deployment**, not application development.

| Application | Stack | Purpose | Lesson |
|---|---|---|---|
| frontend | React 19 + Vite 8, served by nginx | the web UI | [frontend/README.md](frontend/README.md) |
| node-api | Node.js 24 + Express 5 | users API | [node-api/README.md](node-api/README.md) |
| python-api | Python 3.14 + FastAPI | statistics API | [python-api/README.md](python-api/README.md) |
| go-status | Go 1.27, standard library | status board for all services | [go-status/README.md](go-status/README.md) |
| java-api | Java 25 + Spring Boot 4.1 | books API | [java-api/README.md](java-api/README.md) |
| laravel-admin | PHP 8.5 + Laravel 13 (PHP-FPM + nginx) | reviews admin | [laravel-admin/README.md](laravel-admin/README.md) |
| report-worker | JavaScript on Node.js 24, no framework | a batch job | [report-worker/README.md](report-worker/README.md) |

Each lesson has the same sections: what it is, what it does, how to run it locally, how to build the image, how to
run the container, how Compose and Kubernetes run it, which Kubernetes resources it needs, how to verify,
troubleshoot and clean up, and a practical challenge.

Suggested order: node-api first (the most detailed), then any order. Then all of them together:
[Docker Compose](../compose/README.md).
