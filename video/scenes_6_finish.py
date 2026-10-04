"""Chapters 33-36: troubleshooting, the final multi-stack deployment, cleanup, the final challenge."""

from __future__ import annotations

from components import card, checklist, grid, terminal, tile
from recordings import rec
from scenes_common import CAP, K, S, TS, scene

T = {n: TS.format(n, name) for n, name in [
    (1, "wrong-image-name"), (2, "image-pull-failure"), (3, "wrong-container-port"), (4, "service-selector-mismatch"),
    (5, "application-crashes"), (6, "missing-environment-variable"), (7, "database-connection-failure"),
    (8, "readiness-probe-failure"), (9, "volume-problem"), (10, "works-in-pod-not-through-service"),
    (11, "frontend-cannot-reach-backend"), (12, "incorrect-configmap-secret")]}

# ---------------------------------------------------------------- 33. Troubleshooting
scene("Troubleshooting", "troubleshooting/README", "Read the status, then ask the right question", checklist([
    (0, "Pending", "the scheduler or a volume: kubectl describe pod → Events"),
    (1, "ErrImagePull / ImagePullBackOff", "the image name, the tag, or where the image lives"),
    (2, "CrashLoopBackOff / exit codes", "the application itself: kubectl logs --previous"),
    (3, "Running but 0/1 Ready", "the readiness probe, or what it checks (the database, the port)"),
    (4, "Ready, but unreachable", "the Service: selector, endpoints, ports · then the Ingress"),
]), [
    S("Twelve labs break the platform on purpose, and one method solves them all: the Pod's status tells you which "
      "question to ask. Pending means the scheduler or a volume: describe the Pod and read its events."),
    S("Error image pull and image pull back off: the image name, the tag, or where the image lives."),
    S("Crash loop back off: the application itself. Read the logs of the previous, crashed container."),
    S("Running but not ready: the readiness probe, or whatever it checks."),
    S("And ready but unreachable: the Service, its selector, its endpoints, its ports, and then the Ingress."),
])

scene(None, "Recorded · troubleshooting/01 + 02", "Image problems", terminal(
    rec(T[1], "kubectl get pods -l app=go-status", nth=0, width=150, tones={"ErrImagePull": "bad", "ImagePullBackOff": "bad"})
    + rec(T[2], "docker exec bookshop-worker crictl images", step=1, width=150)
    + rec(T[2], "kubectl get events --field-selector reason=Failed", step=1, wrap=118, tones={"Failed": "bad"}),
    "bash (recorded)"), [
    S("Lab one: a typo in the image name. The new Pod cannot pull the image, while the old Pod keeps serving: the "
      "rolling update protects you.", zoom=1.2),
    S("Lab two is subtler: the image exists, on your computer. But the cluster's nodes have their own image store. The "
      "node does not have python-api one point two, tries Docker Hub, and fails. The fix is kind load, or in a real "
      "cluster: push to a registry.", zoom=1.1),
])

scene(None, "Recorded · troubleshooting/04 + 05", "A selector typo and a crash loop", terminal(
    rec(T[4], "curl -s -w '\\nHTTP %{http_code}\\n' http://bookshop.localhost:8080/api/users", tones={"503": "bad"})
    + rec(T[4], "kubectl get endpointslices -l kubernetes.io/service-name=node-api", step=0, width=150)
    + rec(T[5], "kubectl get pods -l app=node-api", nth=0, step=1, width=150, tones={"CrashLoopBackOff": "bad", "Error": "bad"})
    + rec(T[5], "kubectl logs $NEW --previous", step=1, wrap=118, tones={"Cannot find module": "bad", "MODULE_NOT_FOUND": "bad"}),
    "bash (recorded)"), [
    S("Lab four: five oh three through the Ingress, and the Service has no endpoints. All Pods are fine. The Service's "
      "selector has one extra letter, and selects nothing. Nothing in Kubernetes checks that labels and selectors "
      "match.", zoom=1.15),
    S("Lab five: crash loop back off. The current container has no useful log, so ask for the previous one: cannot find "
      "module. A typo in the command.", zoom=1.15),
])

scene(None, "Recorded · troubleshooting/07 + 11 + 12", "Configuration, ports, and secrets", terminal(
    rec(T[7], "kubectl exec $NEW -- node -e", wrap=118, tones={"ENOTFOUND": "bad", "EAI_AGAIN": "bad", "not ready": "bad"})
    + rec(T[11], "curl -s -i http://bookshop.localhost:8080/api/books", nth=0, step=1, head=6, tones={"502": "bad"})
    + rec(T[12], "kubectl exec $NEW -- node -e", step=2, wrap=118, tones={"password authentication failed": "bad"}),
    "bash (recorded)"), [
    S("Lab seven: one wrong letter in the database host name in the ConfigMap, and after a restart the A P I is not "
      "ready: the name does not resolve.", zoom=1.15),
    S("Lab eleven: the frontend cannot reach the books A P I, five oh two from nginx, because the Service's port no "
      "longer matches what the frontend calls.", zoom=1.15),
    S("Lab twelve: someone replaced the database Secret with a wrong password. Password authentication failed. The "
      "lab restores it from the database's own configuration, without ever printing it.", zoom=1.15),
])

scene(None, "troubleshooting/", "Twelve failures, one method", grid([
    tile(0, "🖼️", "images", "3", "bad", "wrong name · not in the node · port"),
    tile(0, "💥", "the app", "3", "bad", "crash · missing variable · readiness"),
    tile(0, "🔌", "networking", "3", "bad", "selector · targetPort · frontend → backend"),
    tile(0, "🗄️", "data", "3", "bad", "database host · volume · secret"),
], cols=4), [
    S("Twelve labs in four families: images, the application, networking, and data. Each one in the same order: "
      "problem, symptoms, investigation, root cause, fix, verification, lesson learned. Do them in the repository: the "
      "fix is only half the lesson; the investigation is the other half."),
])

# ---------------------------------------------------------------- 34. Final multi-stack deployment
scene("Final multi-stack deployment", "Recorded · capstone/deploy.sh", "Everything, from nothing, in one command", terminal(
    rec(CAP, "bash capstone/deploy.sh", tail=12, tones={"Bookshop is up": "ok"}),
    "bash (recorded)"), [
    S("The capstone. One script does everything the lessons did, in the right order: build the images, create the "
      "cluster and the ingress controller, load the images, create the namespace, configuration and Secrets, start the "
      "database, run the migration Job, deploy every application, create the Ingress, and run the first report. And it "
      "is idempotent: running it twice changes nothing.", zoom=1.1),
])

scene(None, "Recorded · capstone/verify.sh", "Verified, not assumed", terminal(
    rec(CAP, "bash capstone/verify.sh", nth=0, tones={"PASS": "ok", "FAIL": "bad", "0 failed": "ok"}),
    "bash (recorded)"), [
    S("And a verification script checks every capability of the course: all workloads available, the volume bound, the "
      "Job complete, resources and probes everywhere, no latest tags, non-root, the password only in a Secret, every "
      "route through the Ingress, the status board all up, and data that survives the loss of the database Pod.", zoom=1.05),
])

# ---------------------------------------------------------------- 35. Cleanup
scene("Cleanup", "Recorded · kubernetes/cleanup.md", "Leave nothing behind", terminal(
    rec(K["cleanup"], "kubectl delete namespace bookshop", tones={"deleted": "ok"})
    + rec(K["cleanup"], "kind delete cluster --name bookshop", step=1, tones={"Deleted": "ok"}),
    "bash (recorded)"), [
    S("Cleaning up is part of the work. One namespace for the whole platform means one command removes everything in "
      "it: Deployments, Services, the StatefulSet, its volume, Jobs and Secrets.", zoom=1.3),
    S("And deleting the kind cluster removes the nodes themselves. In Compose, down with dash v removes the containers, "
      "networks and the volume.", zoom=1.3),
])

# ---------------------------------------------------------------- 36. Final challenge
scene("Final challenge", "capstone/break.sh", "Monday morning: three weekend changes", grid([
    card(0, "📉", "Statistics are missing", "users report an empty statistics panel", "bad"),
    card(0, "🌀", "Two rollouts are stuck", "and nobody noticed, because old Pods still serve", "bad"),
    card(1, "🔎", "Your tools", "get · describe · logs · endpoints · events · rollout history", "blue"),
    card(1, "✅", "Done when", "capstone/verify.sh passes again", "ok"),
], cols=2), [
    S("The final challenge. A script makes three changes to the running platform, like an eventful weekend. Statistics "
      "are missing, and two rollouts are stuck, hidden by old Pods that still serve traffic."),
    S("You get the same tools as in the labs, and you are done when the verification passes again. Run it before you "
      "read the solution."),
])

scene(None, "Recorded · capstone/README.md", "Found, fixed, verified", terminal(
    rec(CAP, "bash capstone/verify.sh", nth=1, grep="FAIL|passed", tones={"FAIL": "bad"})
    + rec(CAP, "bash capstone/verify.sh", nth=2, step=1, tail=3, tones={"0 failed": "ok"}),
    "bash (recorded)"), [
    S("The verification finds the damage: a Service with no endpoints, and Deployments stuck in the middle of a "
      "rollout. A selector typo, an image tag that was never built, and a misspelled database name in the ConfigMap.", zoom=1.2),
    S("Three fixes: apply the Service, undo the rollout, restore the ConfigMap and restart. And the verification passes "
      "again.", zoom=1.3),
])

scene(None, "What you can do now", "Build → Dockerize → Compose → Deploy → Verify → Scale → Update → Roll back → Troubleshoot", checklist([
    (0, "✓", "Package any application as an image", "seven stacks, one contract, versioned tags"),
    (1, "✓", "Run a platform with Docker Compose", "networks, volumes, health-aware dependencies"),
    (2, "✓", "Choose the right Kubernetes resource", "Deployment, StatefulSet, Job, CronJob, Service, Ingress, ConfigMap, Secret"),
    (3, "✓", "Operate it", "probes, resources, scaling, rolling updates, rollbacks"),
    (4, "✓", "Troubleshoot it", "from the Pod status to the root cause, every time"),
]), [
    S("Look at what you can do now. Package any application as a container image, whatever its language."),
    S("Run a whole platform with Docker Compose."),
    S("Translate it into Kubernetes, choosing the right resource for each job."),
    S("Operate it: probes, resources, scaling, rolling updates and rollbacks."),
    S("And troubleshoot it, from the Pod status to the root cause. Kubernetes manages containers. Now you know how to "
      "give it good ones. Thanks for watching, and happy deploying."),
])
