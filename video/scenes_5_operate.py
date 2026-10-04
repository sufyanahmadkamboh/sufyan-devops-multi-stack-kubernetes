"""Chapters 25-32: services and networking, ConfigMaps and Secrets, probes, storage, Ingress, scaling, rolling
updates, rollbacks."""

from __future__ import annotations

from components import arrow, box, card, code, grid, label, notes, svg, terminal
from recordings import rec
from scenes_common import K, S, bare, scene

SCREEN = "../../docs/images/bookshop-ui-kubernetes.png"

# ---------------------------------------------------------------- 25. Services and networking
scene("Services and networking", "docs/11", "Pods come and go. Services stay.", svg(
    box(0, 0, 60, 480, 230, "🧑‍💻", "a client Pod", ["calls http://node-api:3000"], "blue")
    + arrow(0, 490, 175, 600, 175)
    + box(1, 610, 60, 480, 230, "🔀", "Service node-api", ["stable name + virtual IP", "selector: app=node-api"], "amber", "#2b2410")
    + arrow(2, 1100, 120, 1240, 80) + arrow(2, 1100, 230, 1240, 280)
    + box(2, 1250, 0, 470, 150, "📦", "Pod 10.244.1.6", ["Ready ✓ → endpoint"], "ok", "#0f2a22")
    + box(2, 1250, 200, 470, 150, "📦", "Pod 10.244.1.5", ["Ready ✓ → endpoint"], "ok", "#0f2a22")
    + label(3, 860, 470, "Endpoints = the Ready Pods whose labels match the selector, updated automatically.", 28, "sky", "middle", 700)
    + label(4, 860, 540, "Same names as in Compose: the cluster DNS resolves node-api to the Service.", 28, "amber", "middle", 700)
), [
    S("Pods are replaceable: when one dies, a new one comes with a new I P address. So nobody talks to Pods directly. "
      "Clients call a Service by name."),
    S("The Service has a stable name and virtual I P, and a selector: which Pods belong to it."),
    S("Its endpoints are the Pods that match the selector and are Ready. Kubernetes keeps that list up to date all "
      "the time."),
    S("Remember this sentence: endpoints are the ready Pods whose labels match the selector. Half of all networking "
      "problems are explained by it."),
    S("And the names are the same as in Compose, so not a single line of application configuration had to change."),
])

scene(None, "Recorded · kubernetes/09-ingress.md", "Every Service, its endpoints, and the load balancing", terminal(
    rec(K["09-ingress"], "kubectl get services", width=150)
    + rec(K["09-ingress"], "for i in $(seq 1 10)", step=1, tones={"requests": "ok"}),
    "bash (recorded)"), [
    S("All the Services of the platform. Each has a cluster I P, except postgres: a headless Service, whose name points "
      "straight at the database Pod."),
    S("Ten requests to the users A P I through one Service name land on both node-api Pods. The Service balances the "
      "load; nobody configured anything for that.", zoom=1.3),
])

# ---------------------------------------------------------------- 26. ConfigMaps and Secrets
scene("ConfigMaps and Secrets", "Recorded · kubernetes/10-config-and-secrets.md", "Change a setting: when does it apply?", terminal(
    rec(K["10-config-and-secrets"], "kubectl patch configmap bookshop-config --type merge")
    + rec(K["10-config-and-secrets"], "curl -s http://bookshop.localhost:8080/config.js", step=1, nth=0, width=150)
    + rec(K["10-config-and-secrets"], "kubectl rollout restart deployment/frontend", step=2, nth=0, tail=2, tones={"successfully": "ok"})
    + rec(K["10-config-and-secrets"], "curl -s http://bookshop.localhost:8080/config.js", step=2, nth=1, width=150, tones={"from=kubernetes": "ok"}),
    "bash (recorded)"), [
    S("Change the admin link in the ConfigMap."),
    S("The page still shows the old value. Environment variables are copied into a container when it starts. Changing "
      "the ConfigMap does not change processes that are already running.", zoom=1.25),
    S("A rollout restart replaces the Pods one by one, with no downtime, and the new Pods read the new value.", zoom=1.25),
])

scene(None, "Recorded · kubernetes/10-config-and-secrets.md", "What is inside a Secret?", terminal(
    rec(K["10-config-and-secrets"], "kubectl create secret generic demo-secret", tones={"super-secret": "warn"})
    + rec(K["10-config-and-secrets"], "grep -B1 -A1 'secretKeyRef'", step=1),
    "bash (recorded)"), [
    S("With a throw-away example, never a real secret: a Secret stores its value base64 encoded, and anyone who may "
      "read it can decode it in one command. Base64 is an encoding, not encryption. What protects a Secret is access "
      "control, keeping it out of images and Git, and encryption at rest in real clusters.", zoom=1.2),
    S("Our manifests only reference the Secret by name. The password itself never appears in any file."),
])

# ---------------------------------------------------------------- 27. Health probes
scene("Health probes", "Recorded · kubernetes/11-health-probes.md", "Take the database away", terminal(
    rec(K["11-health-probes"], "kubectl get pods -l 'app in (node-api,python-api,java-api)'", nth=0, width=150, tones={"0/1": "bad"})
    + rec(K["11-health-probes"], "curl -s -w '\\nHTTP %{http_code}\\n' http://bookshop.localhost:8080/api/users", step=1, tones={"503": "bad"})
    + rec(K["11-health-probes"], "kubectl get pods -l 'app in (node-api,python-api,java-api)'", step=2, nth=1, width=150, tones={"1/1": "ok"}),
    "bash (recorded)"), [
    S("Now the difference between liveness and readiness, live. Scale the database to zero. Within seconds, every A P I "
      "that needs it is running, but zero of one ready, and the restart count stays at zero. The processes are fine, so "
      "nothing is restarted: restarting would not bring the database back.", zoom=1.15),
    S("But they are taken out of their Services, so the Ingress has nobody to send traffic to: five oh three, no "
      "available server.", zoom=1.3),
    S("Scale the database back up. Nobody restarts anything: the readiness probes simply pass again, and the A P Is "
      "rejoin their Services.", zoom=1.15),
])

scene(None, "Recorded · kubernetes/11-health-probes.md", "A broken liveness probe restarts a healthy app", terminal(
    rec(K["11-health-probes"], "grep go-status | tail -2", wrap=118, tones={"Liveness probe failed": "bad"})
    + rec(K["11-health-probes"], "kubectl get events --field-selector reason=Killing", step=1, width=150, tones={"Killing": "bad"}),
    "bash (recorded)"), [
    S("And the other side: point go-status's liveness probe at a path that does not exist, the most common typo there "
      "is. Four oh four, liveness probe failed.", zoom=1.2),
    S("After three failures the kubelet kills the container and starts it again, and again. A perfectly healthy "
      "application, restarted forever by one wrong line of YAML.", zoom=1.2),
])

# ---------------------------------------------------------------- 28. Storage
scene("Storage", "Recorded · kubernetes/12-storage.md", "Delete the database Pod. Keep the data.", terminal(
    rec(K["12-storage"], "curl -s -X POST http://bookshop.localhost:8080/api/users", tones={"Margaret": "ok"})
    + rec(K["12-storage"], "kubectl rollout status statefulset/postgres", step=1, tones={"Running": "ok"})
    + rec(K["12-storage"], "for u in json.load", step=2, tones={"Margaret": "ok"}),
    "bash (recorded)"), [
    S("Add a user. Then delete the PostgreSQL Pod.", zoom=1.3),
    S("The StatefulSet creates it again, with the same name, postgres zero, and binds it to the same volume claim.", zoom=1.2),
    S("And the user is still there. The data lives in the persistent volume, not in the container. A lab database "
      "like this is not production ready, though: real ones need backups, replication and upgrades.", zoom=1.25),
])

# ---------------------------------------------------------------- 29. Ingress
scene("Ingress", "kubernetes/ingress/ingress.yaml", "One entry point: paths and host names", code(
    "kubernetes/ingress/ingress.yaml", bare("kubernetes/ingress/ingress.yaml"), "yaml", 16) + notes([
    (0, "ingressClassName: traefik", "the controller that carries out these rules"),
    (1, "host bookshop.localhost", "longest matching path wins: /api/users → node-api, ..., / → frontend"),
    (2, "host admin.bookshop.localhost", "a second host, a different application"),
]), [
    S("The Ingress is a set of routing rules, and the ingress controller, Traefik, carries them out."),
    S("For the bookshop host, each A P I path goes to its Service, and everything else to the frontend. The longest "
      "matching path wins."),
    S("And a second host name routes to the Laravel admin. Seven applications behind one port."),
], layout="code")

scene(None, "Recorded · kubernetes/09-ingress.md", "Through the front door", terminal(
    rec(K["09-ingress"], "B=http://bookshop.localhost:8080", width=150, tones={"Bookshop": "ok"})
    + rec(K["09-ingress"], "services up", step=1, tones={"6 of 6": "ok", "Reviews": "ok"}),
    "bash (recorded)"), [
    S("The same U R Ls a browser uses: the page, users from Node.js, books from Java, statistics from Python."),
    S("The status board says six of six services up, and the admin host serves the Laravel page.", zoom=1.3),
])

scene(None, "Recorded · the browser", "The platform on Kubernetes", f'<img class="shot st" data-s="0" src="{SCREEN}" alt="The Bookshop UI on Kubernetes" style="height:700px;width:auto">', [
    S("And in the browser: books, users, statistics with the latest report, and the status of every service. Seven "
      "stacks, one platform, running on Kubernetes."),
])

# ---------------------------------------------------------------- 30. Scaling
scene("Scaling", "Recorded · kubernetes/14 + labs/04", "One number", terminal(
    rec(K["14-scaling-rolling-updates"], "kubectl rollout status deployment/node-api --timeout=240s", nth=0, width=150, tones={"Running": "ok"})
    + rec("labs/04-scale.md", "for i in $(seq 1 20)", step=1, tones={"requests": "ok"}),
    "bash (recorded)"), [
    S("Scaling is one number. Three replicas of node-api: three identical Pods behind one Service. More capacity, and "
      "one Pod or one node can fail without an outage."),
    S("In the labs you scale your own service to four, and the logs show how twenty requests spread across all four.", zoom=1.3),
])

scene(None, "Recorded · kubernetes/13-resources.md", "A memory limit that is too small", terminal(
    rec(K["13-resources"], "kubectl get pods -l app=python-api -o jsonpath", width=150, tones={"OOMKilled": "bad"})
    + rec(K["13-resources"], "curl -s http://bookshop.localhost:8080/api/stats; echo", step=1, width=150, tones={"users": "ok"})
    + rec(K["13-resources"], "kubectl rollout status deployment/python-api --timeout=5s", step=2),
    "bash (recorded)"), [
    S("Requests are what the scheduler reserves, limits are the ceiling. Give python-api a twenty-four megabyte memory "
      "limit, and the new Pod is O O M killed, exit code one three seven, again and again.", zoom=1.15),
    S("But the statistics still work. The change started a rolling update, the new Pod never became ready, so "
      "Kubernetes never removed the old ones.", zoom=1.15),
    S("The rollout simply stopped at the first bad Pod. That is the safety net of rolling updates.", zoom=1.3),
])

# ---------------------------------------------------------------- 31. Rolling updates
scene("Rolling updates", "Recorded · kubernetes/14-scaling-rolling-updates.md", "From 1.0.0 to 1.1.0, one Pod at a time", terminal(
    rec(K["14-scaling-rolling-updates"], "kubectl rollout status deployment/node-api --timeout=240s", nth=1, tail=4, tones={"successfully": "ok"})
    + rec(K["14-scaling-rolling-updates"], "kubectl get replicasets -l app=node-api", step=1, width=150, tones={"1.1.0": "ok"})
    + rec(K["14-scaling-rolling-updates"], "kubectl rollout history deployment/node-api", step=2),
    "bash (recorded)"), [
    S("A new version is a new image with a new tag. Kubectl set image starts a rolling update: new Pods come up and must "
      "pass their readiness probe before old ones are removed.", zoom=1.2),
    S("Behind the scenes, a new ReplicaSet for the new Pod template, and the old one kept, scaled to zero. The new Pods "
      "answer version one point one.", zoom=1.15),
    S("And the rollout history: revision two, with the change cause we recorded.", zoom=1.3),
])

# ---------------------------------------------------------------- 32. Rollbacks
scene("Rollbacks", "Recorded · kubernetes/14-scaling-rolling-updates.md", "kubectl rollout undo", terminal(
    rec(K["14-scaling-rolling-updates"], "kubectl rollout undo deployment/node-api", tail=2, tones={"successfully": "ok"})
    + rec(K["14-scaling-rolling-updates"], "kubectl get deployment node-api -o jsonpath", step=1, tones={"1.0.0": "ok"}),
    "bash (recorded)"), [
    S("Version one point one turns out to be bad. Rollout undo scales the previous ReplicaSet back up, with the same "
      "rolling, zero downtime process.", zoom=1.3),
    S("Back on node-api one point zero point zero. This only works because every version has its own tag: one point zero "
      "point zero still means exactly the image that ran before. With latest, the previous version would not exist "
      "anymore.", zoom=1.3),
])
