"""Chapters 19-24: deploy every application to Kubernetes (Node.js, React, Python, Go, Java, Laravel)."""

from __future__ import annotations

from components import arrow, box, code, label, notes, svg, terminal
from recordings import rec
from scenes_common import K, S, excerpt, scene

JAVA_PROBES = excerpt("kubernetes/java-api/deployment.yaml", "startupProbe:", "failureThreshold: 2")

# ---------------------------------------------------------------- 19. Node.js
scene("Deploy Node.js", "Recorded · kubernetes/00 + 01", "A cluster, a namespace, configuration, a database", terminal(
    rec(K["00-cluster"], "kubectl config current-context", tones={" Ready": "ok"})
    + rec(K["01-foundation"], "kubectl describe secret db-credentials", step=1)
    + rec(K["01-foundation"], "kubectl get pods,pvc -l app=postgres", step=2, width=150, tones={"Bound": "ok", "Running": "ok"}),
    "bash (recorded)"), [
    S("First the ground work. kind creates a real Kubernetes one point thirty-seven cluster with two nodes, each a "
      "Docker container on this computer. Traefik is installed as the ingress controller."),
    S("A namespace for the platform, a ConfigMap with the settings, and the Secrets, created from random values directly "
      "in the cluster. The repository contains no password at all: describe shows only the size.", zoom=1.3),
    S("And PostgreSQL as a StatefulSet, with a persistent volume claim that is bound to a real volume."),
])

scene(None, "Recorded · kubernetes/02-node-api.md", "Image in, Deployment up, Service in front", terminal(
    rec(K["02-node-api"], "kind load docker-image node-api:1.0.0", tail=2)
    + rec(K["02-node-api"], "kubectl get deployment node-api", step=1, width=150, tones={"Running": "ok"})
    + rec(K["02-node-api"], "kubectl get service node-api", step=2, width=150)
    + rec(K["02-node-api"], "kubectl exec deploy/node-api -- wget -qO- http://node-api:3000/api/users", step=3, width=150, tones={"Ada": "ok"}),
    "bash (recorded)"), [
    S("Our image exists only in Docker on this computer. kind load copies it into the cluster's nodes. In a cloud you "
      "would push it to a registry instead."),
    S("Apply the Deployment and the Service. Two Pods, each with its own I P address, both running.", zoom=1.15),
    S("The Service gives them one stable name and virtual I P. Its endpoints are the two Pod addresses.", zoom=1.2),
    S("And through the Service, by name, the users come back from PostgreSQL. node-api runs on Kubernetes.", zoom=1.2),
])

# ---------------------------------------------------------------- 20. React
scene("Deploy React", "Recorded · kubernetes/03-frontend.md", "One image, configured at start", terminal(
    rec(K["03-frontend"], "kubectl rollout status deployment/frontend", tail=3, tones={"successfully": "ok"})
    + rec(K["03-frontend"], "curl -s http://localhost:18080/ | grep -o", step=1, tones={"kubernetes": "ok"})
    + rec(K["03-frontend"], "curl -s http://localhost:18080/api/users | head -c 120", step=2, width=150, tones={"upstream unreachable": "bad"}),
    "bash (recorded)"), [
    S("The frontend: two replicas of the same image that ran in Compose."),
    S("Through a port forward: the page, its health check, and the configuration file, which now says environment "
      "Kubernetes, because it came from the ConfigMap when the container started.", zoom=1.25),
    S("The users come back through the frontend's proxy. The books do not, yet: java-api is not deployed, and the "
      "frontend says so with a clean error.", zoom=1.2),
])

# ---------------------------------------------------------------- 21. Python
scene("Deploy Python", "Recorded · kubernetes/04-python-api.md", "Same YAML shape, another language", terminal(
    rec(K["04-python-api"], "kubectl apply -f kubernetes/python-api/", tail=3, tones={"successfully": "ok"})
    + rec(K["04-python-api"], "kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/api/stats", step=1, tones={"users": "ok"}),
    "bash (recorded)"), [
    S("The Python Deployment differs from the Node.js one in a handful of lines: the name, the image, the port, the "
      "user I D and the resource numbers. Same shape, different language."),
    S("It counts three users. Books and reviews are still zero: their owners are not deployed yet, and the A P I "
      "treats a missing table as zero instead of failing.", zoom=1.3),
])

# ---------------------------------------------------------------- 22. Go
scene("Deploy Go", "Recorded · kubernetes/05-go-status.md", "Service discovery, seen from the status board", terminal(
    rec(K["05-go-status"], "kubectl get configmap bookshop-config -o jsonpath='{.data.TARGETS}'")
    + rec(K["05-go-status"], "kubectl exec deploy/node-api -- wget -qO- http://go-status:8080/api/status", step=1,
          tones={" up ": "ok", "down": "bad"})
    + rec(K["05-go-status"], "kubectl exec deploy/go-status -- sh -c 'echo hello'", step=2, wrap=118, tones={"not found": "bad"}),
    "bash (recorded)"), [
    S("The status board's targets come from the ConfigMap: the same service names as in Compose, resolved by the "
      "cluster's D N S."),
    S("What is deployed is up, what is not shows as down: its name does not exist yet.", zoom=1.2),
    S("And the distroless container has no shell, in Kubernetes as in Docker.", zoom=1.2),
])

# ---------------------------------------------------------------- 23. Java
scene("Deploy Java", "kubernetes/java-api/deployment.yaml", "A startup probe for a slow starter", code(
    "kubernetes/java-api/deployment.yaml (probes)", JAVA_PROBES, "yaml", 22) + notes([
    (0, "startupProbe", "up to 30 × 2 s = 60 s to start; the other probes wait"),
    (1, "livenessProbe", "after startup: restart if /health fails 3 times"),
    (2, "readinessProbe", "traffic only while /ready (with the database) answers"),
]), [
    S("Java needs a few seconds to start, more with a CPU limit. If the liveness probe started checking at once, it "
      "could kill the JVM before it ever finished starting, in an endless loop. The startup probe gives it up to sixty "
      "seconds, and holds the other probes back until it succeeds."),
    S("After that, liveness takes over: restart only if slash health fails three times in a row."),
    S("And readiness decides about traffic, every five seconds."),
], layout="code")

scene(None, "Recorded · kubernetes/06-java-api.md", "Watch the startup probe work", terminal(
    rec(K["06-java-api"], "kubectl logs deploy/java-api | grep -m1", tones={"Started": "ok"})
    + rec(K["06-java-api"], "kubectl describe pod -l app=java-api | grep -E 'Startup|Liveness|Readiness'", step=1, wrap=118,
          tones={"Startup probe failed": "warn"})
    + rec(K["06-java-api"], "kubectl exec deploy/node-api -- wget -qO- http://java-api:8080/api/books", step=2, width=150, tones={"Moby": "ok"}),
    "bash (recorded)"), [
    S("Spring Boot reports its own start time.", zoom=1.3),
    S("And the Pod's events show the startup probe failing at first, connection refused, while the JVM was still "
      "starting. That is exactly what it is for: those failures did not restart anything.", zoom=1.1),
    S("Then the books arrive, from the table Java created at startup.", zoom=1.2),
])

# ---------------------------------------------------------------- 24. Laravel
scene("Deploy Laravel", "kubernetes/laravel-admin/", "A Job for migrations, one Pod with two containers", svg(
    box(0, 0, 40, 520, 200, "🧰", "Job laravel-migrate", ["php artisan migrate --seed", "runs once, to completion"], "amber", "#2b2410")
    + arrow(0, 530, 140, 640, 140)
    + label(0, 590, 120, "then", 22, "amber", "middle")
    + '<rect class="st" data-s="1" x="650" y="0" width="1070" height="330" rx="24" fill="#221a3a" stroke="#b48cff" stroke-width="3"/>'
    + label(1, 680, 50, "Pod laravel-admin (one network namespace)", 26, "violet")
    + box(1, 680, 80, 470, 220, "🌐", "laravel-web (nginx)", ["port 8080", "exposed by the Service"], "blue")
    + arrow(1, 1155, 190, 1220, 190, label="127.0.0.1:9000")
    + box(1, 1225, 80, 470, 220, "🐘", "laravel-fpm (PHP-FPM)", ["port 9000", "only inside the Pod"], "violet", "#221a3a")
    + label(2, 860, 450, "Compose: two services over the network  →  Kubernetes: two containers in one Pod", 28, "sky", "middle", 700)
), [
    S("Laravel brings two new Kubernetes ideas. Migrations run once per release, not in every replica at startup, so "
      "they are a Job: it runs to completion and stops."),
    S("And nginx and PHP F P M always run and scale together, and nginx must reach exactly its own F P M. So they are "
      "two containers in one Pod. Containers in a Pod share a network, so nginx talks to F P M on one two seven dot zero "
      "dot zero dot one."),
    S("In Compose they were two services. In Kubernetes they are a sidecar pair."),
])

scene(None, "Recorded · kubernetes/07 + 08", "Migration Job, a 2/2 Pod, and a CronJob", terminal(
    rec(K["07-laravel-admin"], "kubectl wait --for=condition=complete job/laravel-migrate", tones={"Complete": "ok"})
    + rec(K["07-laravel-admin"], "kubectl apply -f kubernetes/laravel-admin/deployment.yaml", step=1, tail=2, tones={"2/2": "ok"})
    + rec(K["08-report-worker"], "kubectl get pods -l job-name=report-now", step=2, width=150, tones={"saved": "ok", "Completed": "ok"}),
    "bash (recorded)"), [
    S("The migration Job: complete, one of one, in a few seconds.", zoom=1.3),
    S("The Laravel Pod: ready two of two, two containers.", zoom=1.3),
    S("And the JavaScript worker as a CronJob. We create one Job from it right away: completed, exit code zero, report "
      "saved with six of six services up. Every application is running.", zoom=1.2),
])
