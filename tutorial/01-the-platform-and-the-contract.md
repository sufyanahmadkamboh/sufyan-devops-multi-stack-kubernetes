# 01 · The platform and the contract

> Goal: you can explain the architecture, why it uses seven stacks, and the one rule set that makes them all
> deployable the same way. Levels 1–2 of the [roadmap](../README.md#4-the-roadmap). Time: about 45 minutes.

## The walk

### 1. Read docs/01 · Architecture

Open [docs/01](../docs/01-architecture.md). Follow the request it traces from the browser to PostgreSQL and back.
Pay attention to one detail that runs through the whole course: **the service names never change**. `node-api` is the
Compose service name, the Kubernetes Service name and the DNS name other services use. In Compose the frontend's nginx
forwards `/api/*`; in Kubernetes the Ingress does that routing. The applications do not notice the difference.

### 2. Read docs/02 · Why multiple stacks

Open [docs/02](../docs/02-why-multiple-stacks.md). The important part is the list of what Kubernetes **sees**:

```text
 an image · a port · environment variables · /health and /ready · signals (SIGTERM) · exit codes · stdout
```

and what it does **not** care about: the language, the framework, the build tool. Read the section on JavaScript and
Node.js carefully: JavaScript is the language; Node.js is a runtime that runs JavaScript outside the browser. In this
course JavaScript appears three times in three roles: in the **browser** (the React UI), in a **server** (node-api) and
in a **batch job** (report-worker). Three roles mean three different Kubernetes resources later.

### 3. Read the contract

Open [docs/CONTRACT.md](../docs/CONTRACT.md). This is the most important page of the course, and it is short. Every
service:

| Rule | Why Kubernetes cares |
|---|---|
| listens on `PORT` | the Deployment's `containerPort` and the Service's `targetPort` must match it |
| `GET /health` (no database check) | liveness: restart only when the process itself is broken |
| `GET /ready` (checks the database) | readiness: take the Pod out of the Service while it cannot work |
| configuration only from environment variables | the same image runs everywhere, configured by ConfigMaps and Secrets |
| logs to stdout | `kubectl logs` and every log collector read stdout |
| graceful SIGTERM | rolling updates stop old Pods with SIGTERM |
| non-root user, versioned tag | security, and rollbacks to an image that still exists |

### 4. Look at the applications

Open [applications/README.md](../applications/README.md), then skim the source of two services in different
languages, for example `applications/node-api/src/server.js` and `applications/python-api/src/main.py`. Find the
`/health` and `/ready` handlers in both. They look different and do the same thing. That is the point.

## Expert commentary

- **Why one contract?** In real companies, the platform team cannot learn every language the product teams use.
  What they can do is publish a contract like this one ("listen on PORT, expose /health and /ready, log to stdout").
  Every team that follows it gets deployment, monitoring and scaling for free.
- **The /health vs /ready split** is the most common design mistake in real services: a liveness probe that checks
  the database makes Kubernetes restart every API when the database has a hiccup, which turns a small outage into a
  large one. Chapter 09 shows the correct behaviour live.
- **Interview angle:** "How would you deploy an application written in a language you don't know?" Answer with the
  contract: build an image, find out its port, health endpoint, configuration and how it stops; the rest is the same
  YAML as for any other service.

## Checkpoint

- [ ] You can draw the platform from memory: seven applications, who calls whom, one database.
- [ ] You can explain JavaScript vs Node.js, and name the three roles JavaScript plays here.
- [ ] You can say why `/health` must not check the database.
- [ ] You found `/health` and `/ready` in two applications written in different languages.

Next: [02 · Dockerize every stack](02-dockerize-every-stack.md)
