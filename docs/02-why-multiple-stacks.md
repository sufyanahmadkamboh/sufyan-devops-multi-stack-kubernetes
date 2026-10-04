# 02 · Why multiple technology stacks?

> Time: 15 minutes

## Real companies are never "one language"

Open the repositories of almost any company older than a few years and you will find several languages side by side:

| Why | Example |
|---|---|
| **Teams choose what fits the job** | a data team writes Python, a web team writes JavaScript/TypeScript |
| **History** | the billing system from 2014 is Java, the new services are Go |
| **Libraries and ecosystems** | machine learning in Python, enterprise integrations in Java, a CMS in PHP |
| **Performance or footprint** | a small, fast network service in Go; a heavy business application on the JVM |
| **Acquisitions and vendors** | a bought product arrives with its own stack |

A DevOps or platform engineer rarely gets to choose. The job is to **run all of them the same way**: build, ship,
configure, observe and update them with one set of tools. Containers and Kubernetes are how that is done today.

## What Kubernetes sees, and what it does not

Kubernetes never looks inside your code. It manages **containers**, and it only sees what a container shows on the
outside:

```text
            ┌─────────────────────────────── what Kubernetes sees ───────────────────────────────┐
            │  an image name + tag   a process that starts   a port it listens on   /health, /ready │
            │  environment variables in   stdout/stderr out   an exit code   a reaction to SIGTERM  │
            └───────────────────────────────────────────────────────────────────────────────────────┘
                                                     ▲
                                             the container boundary
                                                     ▼
            ┌──────────────────── what Kubernetes does NOT care about ────────────────────┐
            │  Node.js or Java?  Express or Spring?  npm or Maven?  interpreted or compiled? │
            └───────────────────────────────────────────────────────────────────────────────┘
```

| Kubernetes needs | Why |
|---|---|
| an **image** it can pull | to start the container on any node |
| a **port** | for the Service to send traffic to |
| **health endpoints** | to know when to restart (liveness) and when to send traffic (readiness) |
| **configuration from environment variables** | so one image runs in every environment (ConfigMaps and Secrets fill them) |
| **logs on stdout/stderr** | `kubectl logs` reads exactly that, nothing else |
| a **meaningful exit code** | a Job succeeds with 0 and fails with anything else; a crashing server is restarted |
| **graceful shutdown on SIGTERM** | rolling updates and scale-downs send SIGTERM before they stop a container |

## The contract is the interface

Because Kubernetes only sees the outside, this lab defines that outside once, in [CONTRACT.md](CONTRACT.md), and
every application follows it, whatever its language:

| Rule | Node.js | Python | Go | Java | PHP | JavaScript job |
|---|---|---|---|---|---|---|
| port from `PORT` | ✓ | ✓ | ✓ | ✓ | (nginx: 8080, FPM: 9000) | – (no server) |
| `/health` (process alive) | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| `/ready` (database answers) | ✓ | ✓ | – (no database) | ✓ | ✓ | – |
| config only from environment | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| missing `DB_PASSWORD` → clear message, exit 1 | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| logs to stdout | ✓ | ✓ | ✓ | ✓ | ✓ (stderr) | ✓ |
| graceful SIGTERM | ✓ | ✓ | ✓ | ✓ | ✓ (FPM) | – (exits on its own) |
| non-root user in the image | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

The result: the Kubernetes manifests of `node-api`, `python-api` and `java-api` are almost identical. Only the image,
the port, the memory numbers and (for Java) a startup probe differ. Compare
[node-api/deployment.yaml](../kubernetes/node-api/deployment.yaml) with
[java-api/deployment.yaml](../kubernetes/java-api/deployment.yaml).

## JavaScript is a language, Node.js is a runtime

Three parts of this lab are written in JavaScript, and they run in three different places:

```text
  JavaScript (the language)
      │
      ├── in the BROWSER ........ frontend (React)     the code is built into files; your browser runs it
      │
      └── on NODE.JS (a runtime that runs JavaScript outside the browser)
              ├── a SERVER ...... node-api (Express)   starts, listens on port 3000, runs until stopped
              └── a BATCH JOB ... report-worker        starts, does one job, exits (no framework at all)
```

- **JavaScript** is the programming language.
- **Node.js** is a runtime: the V8 engine plus file, network and process access, so JavaScript can run outside a
  browser. It is to JavaScript roughly what the JVM is to Java bytecode.
- **Express** is a framework on top of Node.js for HTTP servers. `report-worker` uses no framework: it is plain
  JavaScript with one library (the PostgreSQL client).

For Kubernetes the difference that matters is not the language but the **shape of the workload**: `node-api` is a
long-running server (a Deployment), `report-worker` runs to completion (a Job, created on a schedule by a CronJob),
and the React code never runs in the cluster at all, only the nginx that serves it.

## Why not more stacks?

It would be easy to add .NET, Ruby or Rust. They were left out on purpose, because each would repeat a lesson that an
existing service already teaches:

| Candidate | What it would show | Already shown by |
|---|---|---|
| .NET | compiled to an intermediate language, needs a runtime, multi-stage SDK → runtime image | `java-api` (JDK → JRE) |
| Rust | one static binary in a tiny final image | `go-status` |
| Ruby / Django | interpreted, dependencies from a lock file, a web server process | `python-api`, `node-api`, `laravel-admin` |
| Next.js / Vue | a JavaScript frontend built into static files | `frontend` |

Seven applications that each teach something different are more useful than ten that repeat each other. Once you
have done these, adding any other stack is the same four steps: a Dockerfile, an image, a Compose service, and a
Deployment plus Service.

## Check yourself

<details><summary>Name four things Kubernetes needs from a container, regardless of its language.</summary>

An image to pull, a port to send traffic to, health endpoints for its probes, and configuration through environment
variables (also: logs on stdout, meaningful exit codes, graceful SIGTERM handling).
</details>

<details><summary>Why are the Deployments of node-api and python-api almost the same file?</summary>

Both follow the same contract: port from `PORT`, `/health` and `/ready`, database settings from the same environment
variables. Kubernetes only sees that outside behaviour, so only the image, the port and the resource numbers differ.
</details>

<details><summary>Is Node.js a programming language?</summary>

No. JavaScript is the language; Node.js is a runtime that executes JavaScript outside the browser.
</details>

<details><summary>Which Kubernetes resource fits report-worker, and why not a Deployment?</summary>

A Job (scheduled by a CronJob). It runs to completion and exits with 0. A Deployment expects a process that keeps
running and would restart it forever after every successful exit.
</details>

<details><summary>Does the React code of the frontend run inside the Kubernetes cluster?</summary>

No. It is built into static files at image build time; the cluster only runs nginx, which serves those files. The
browser runs the React code.
</details>

Next: [03 · Dockerfiles across stacks](03-dockerfiles-across-stacks.md)
