"""Chapters 16-18: everything with Docker Compose, Compose networking, from Compose to Kubernetes."""

from __future__ import annotations

from components import arrow, box, checklist, code, label, notes, svg, terminal
from recordings import rec
from scenes_common import COMPOSE, S, excerpt, scene

COMPOSE_NODE = excerpt("compose/docker-compose.yml", "  node-api:", "    networks:")
K8S_NODE = excerpt("kubernetes/node-api/deployment.yaml", "      containers:", "            failureThreshold: 2")

# ---------------------------------------------------------------- 16. Docker Compose
scene("Run everything with Docker Compose", "compose/docker-compose.yml", "One file for the whole platform", code(
    "compose/docker-compose.yml (excerpt)", COMPOSE_NODE, "yaml", 22) + notes([
    (0, "build + image", "where the Dockerfile is, and the versioned name of the result"),
    (1, "environment", "the shared database settings (x-db-env), the password from .env"),
    (2, "healthcheck + depends_on", "start after PostgreSQL is healthy; report healthy when /ready answers"),
    (3, "networks", "which other services it can reach by name"),
]), [
    S("Seven containers that must find each other, share a database and start in a sensible order. Docker Compose "
      "describes all of that in one file. Here is one service: where to build it, and the image name with its version."),
    S("The environment: the same database settings for every service, defined once. The password comes from a dot "
      "env file that never goes into Git."),
    S("Then the order: start after PostgreSQL is healthy, and count as healthy only when slash ready answers. Without "
      "health conditions, depends on only waits until the other container has started, not until it is ready."),
    S("And the networks this service joins, which decide who can reach it by name."),
], layout="code")

scene(None, "Recorded · compose/README.md", "docker compose up", terminal(
    rec(COMPOSE, "docker compose up -d --wait", tail=7, tones={"Healthy": "ok"})
    + rec(COMPOSE, "docker compose ps --format", step=1, width=150, tones={"healthy": "ok"}),
    "bash (recorded)"), [
    S("One command builds what is missing and starts everything in order. With wait, it returns only when every "
      "service is running and healthy.", zoom=1.15),
    S("Nine containers from seven stacks, all healthy. Only two of them publish a port on this computer, and only on "
      "localhost: the user interface and the reviews admin. Everything else is reachable only from inside.", zoom=1.1),
])

scene(None, "Recorded · compose/README.md", "The platform, working", terminal(
    rec(COMPOSE, "curl -s http://localhost:8081/api/books | head -c 160", tones={"Pride": "ok"})
    + rec(COMPOSE, "services up", step=1, tones={"6 of 6": "ok", " up": "ok"})
    + rec(COMPOSE, "docker compose run --rm report-worker", step=2, tones={"saved": "ok"}),
    "bash (recorded)"), [
    S("Through the frontend: books from Java and statistics from Python."),
    S("The Go status board: six of six services up.", zoom=1.2),
    S("And the JavaScript worker is not a server, so it does not start with the rest. Docker compose run starts it "
      "once; it writes its report and exits.", zoom=1.3),
])

# ---------------------------------------------------------------- 17. Compose networking
scene("Understand Compose networking", "docs/05", "Two networks, one DNS server, deliberate isolation", svg(
    '<rect class="st" data-s="0" x="0" y="20" width="1720" height="250" rx="24" fill="#101d31" stroke="#3b82d6" stroke-width="3"/>'
    + label(0, 30, 70, "network: frontend", 26, "sky")
    + box(0, 40, 100, 300, 140, "⚛️", "frontend", ["UI only here"], "blue")
    + box(1, 440, 100, 1240, 140, "🔀", "node-api · python-api · java-api · go-status · laravel-web", ["on BOTH networks"], "ok", "#0f2a22")
    + '<rect class="st" data-s="2" x="0" y="320" width="1720" height="250" rx="24" fill="#2b2410" stroke="#ffc94d" stroke-width="3"/>'
    + label(2, 30, 370, "network: backend", 26, "amber")
    + box(2, 440, 400, 600, 140, "🗄️", "postgres", ["only here"], "amber", "#2b2410")
    + box(2, 1080, 400, 600, 140, "🐘", "laravel-fpm · workers", ["only here"], "amber", "#2b2410")
    + label(3, 860, 650, "Containers find each other by service name: Compose runs a DNS server for each network.", 28, "sky", "middle", 700)
), [
    S("The frontend container is only on the frontend network. It needs to reach the A P Is, nothing else."),
    S("The A P Is are on both networks: they talk to the frontend side and to the database."),
    S("The database, PHP F P M and the workers are only on the backend network."),
    S("And within a network, a service name is a host name. That is service discovery, and Kubernetes will do the same "
      "with Services."),
])

scene(None, "Recorded · compose/README.md", "Prove it from inside the containers", terminal(
    rec(COMPOSE, "docker compose exec node-api wget -qO- http://java-api:8080/api/books/2", tones={"Moby": "ok"})
    + rec(COMPOSE, "docker compose exec frontend wget -qO- -T 3 http://postgres:5432", step=1, tones={"bad address": "bad"})
    + rec(COMPOSE, "docker compose exec postgres psql", step=2),
    "bash (recorded)"), [
    S("From inside node-api, the Java A P I is simply java-api, port eighty eighty.", zoom=1.3),
    S("From inside the frontend, the name postgres does not even exist: bad address. The isolation works.", zoom=1.3),
    S("And in the database, the tables created by three different applications in three languages."),
])

# ---------------------------------------------------------------- 18. Compose → Kubernetes
scene("From Compose to Kubernetes", "docs/06", "Every Compose line has a Kubernetes home", checklist([
    (0, "service", "→ Deployment (a server) · StatefulSet (the database) · Job / CronJob (run to completion)"),
    (1, "ports", "→ Service (inside the cluster) + Ingress (from outside)"),
    (2, "environment / .env", "→ ConfigMap (settings) + Secret (passwords, keys)"),
    (3, "volumes", "→ PersistentVolumeClaim"),
    (4, "healthcheck · depends_on", "→ startup, liveness and readiness probes · readiness and retries in the app"),
    (5, "replicas · restart", "→ Deployment replicas · Kubernetes keeps the desired state"),
]), [
    S("This is the heart of the course. Kubernetes is not docker compose up on a bigger machine. Every line of the "
      "Compose file maps to a Kubernetes resource, chosen by what the service does. A server becomes a Deployment, "
      "the database a StatefulSet, the worker a CronJob, the migration a Job."),
    S("Ports become Services inside the cluster, and an Ingress for traffic from outside."),
    S("The environment splits into a ConfigMap for settings and Secrets for passwords."),
    S("Volumes become persistent volume claims."),
    S("Health checks and depends on become probes. There is no start order in Kubernetes: everything starts, and "
      "readiness decides when a Pod gets traffic."),
    S("And instead of restart policies, Kubernetes keeps the declared number of replicas running, on any node."),
])

scene(None, "compose/ vs kubernetes/node-api/", "The same service, side by side", '<div style="display:grid;grid-template-columns:1fr 1.25fr;gap:28px;width:100%">'
      + code("compose/docker-compose.yml", COMPOSE_NODE, "yaml", 17)
      + code("kubernetes/node-api/deployment.yaml (excerpt)", K8S_NODE, "yaml", 15) + "</div>", [
    S("Here is node-api in both worlds. The same image, the same port, the same environment, but in Kubernetes split "
      "into references to the ConfigMap and the Secret, plus a liveness and a readiness probe, resources and a security "
      "context. Longer, yes, but every line answers a question Compose never had to ask: what happens on a cluster "
      "of machines, when things fail."),
])
