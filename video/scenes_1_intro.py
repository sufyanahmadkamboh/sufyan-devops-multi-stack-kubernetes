"""Chapters 1-3: introduction, the project architecture, why multiple technology stacks."""

from __future__ import annotations

from components import arrow, box, card, checklist, code, grid, label, notes, svg
from scenes_common import S, excerpt, scene

# ---------------------------------------------------------------- 1. Introduction
scene("Introduction", "Multi-Stack on Kubernetes", "Seven stacks. One platform. Docker, Compose, Kubernetes.", svg(
    box(0, 0, 20, 230, 150, "⚛️", "React", ["the UI"], "blue")
    + box(0, 250, 20, 230, 150, "🟩", "Node.js", ["users API"], "ok", "#0f2a22")
    + box(0, 500, 20, 230, 150, "🐍", "Python", ["statistics"], "amber", "#2b2410")
    + box(0, 750, 20, 230, 150, "🐹", "Go", ["status board"], "blue")
    + box(0, 1000, 20, 230, 150, "☕", "Java", ["books API"], "bad", "#2a1520")
    + box(0, 1250, 20, 230, 150, "🐘", "Laravel", ["reviews admin"], "violet", "#221a3a")
    + box(0, 1500, 20, 220, 150, "📜", "JavaScript", ["a batch job"], "ok", "#0f2a22")
    + arrow(1, 860, 190, 860, 260)
    + box(1, 330, 270, 1060, 120, "🐳", "Dockerfile → image → container → Docker Compose", ["every application, the same workflow"], "blue", "#16306a")
    + arrow(2, 860, 400, 860, 470)
    + box(2, 330, 480, 1060, 120, "☸️", "Kubernetes: Deployments, Services, Ingress, probes, storage, ...", ["the same images, the right resource for each job"], "ok", "#0f2a22")
    + label(3, 860, 680, "Build → Dockerize → Compose → Deploy → Verify → Scale → Update → Roll back → Troubleshoot", 28, "amber", "middle", 800)
), [
    S("Welcome. In this course you take seven applications, written in seven different technology stacks: React, "
      "Node.js, Python, Go, Java, Laravel, and plain JavaScript. Together they form one small platform: a bookshop."),
    S("You package every one of them as a Docker image, run each image as a container, and then run the whole "
      "platform with Docker Compose."),
    S("Then you deploy the exact same images to Kubernetes, and for each application you choose the right Kubernetes "
      "resource: a Deployment, a Service, a ConfigMap, a Secret, a Job, a StatefulSet, an Ingress."),
    S("And then you do what engineers do every day: scale, update, roll back, and troubleshoot twelve realistic failures."),
])

scene(None, "How this course works", "Every command you will see was really run", grid([
    card(0, "🧪", "Tested lessons", "every command runs automatically in CI: Docker, Compose, a real Kubernetes cluster", "ok"),
    card(0, "📺", "Real output", "every terminal in this video is a recording of those runs, nothing typed for the camera", "blue"),
    card(1, "🧭", "20 levels", "from one Dockerfile to the complete platform; each level ends with something that works", "amber"),
    card(1, "🔧", "12 failures", "wrong image, selector mismatch, crash loops, probes, volumes, secrets, ...", "bad"),
], cols=2), [
    S("Everything comes from one free repository on GitHub. Each lesson is a Markdown file whose commands are executed "
      "automatically on fresh machines in C I. Every terminal you see in this video is a real recording of those runs."),
    S("The course follows a roadmap of twenty levels, and after each section there are challenges, then twelve "
      "troubleshooting labs and a final capstone."),
])

# ---------------------------------------------------------------- 2. Project architecture
scene("Project architecture", "docs/01", "The Bookshop platform", svg(
    box(0, 660, 0, 400, 110, "🌐", "Browser", ["bookshop.localhost:8080"], "blue")
    + arrow(0, 860, 115, 860, 165)
    + box(1, 360, 170, 1000, 100, "🚪", "Ingress (Traefik)", ["routes by path and host name"], "amber", "#2b2410")
    + arrow(2, 470, 275, 120, 335) + arrow(2, 640, 275, 420, 335) + arrow(2, 860, 275, 720, 335)
    + arrow(2, 1060, 275, 1020, 335) + arrow(2, 1250, 275, 1320, 335) + arrow(2, 1340, 275, 1600, 335)
    + box(2, 0, 340, 270, 130, "⚛️", "frontend", ["/  · React"], "blue")
    + box(2, 290, 340, 270, 130, "🟩", "node-api", ["/api/users"], "ok", "#0f2a22")
    + box(2, 580, 340, 270, 130, "☕", "java-api", ["/api/books"], "bad", "#2a1520")
    + box(2, 870, 340, 270, 130, "🐍", "python-api", ["/api/stats"], "amber", "#2b2410")
    + box(2, 1160, 340, 270, 130, "🐹", "go-status", ["/api/status"], "blue")
    + box(2, 1450, 340, 270, 130, "🐘", "laravel-admin", ["admin. host"], "violet", "#221a3a")
    + arrow(3, 425, 480, 760, 560) + arrow(3, 715, 480, 800, 560) + arrow(3, 1005, 480, 900, 560) + arrow(3, 1585, 480, 980, 580)
    + box(3, 560, 560, 600, 110, "🗄️", "PostgreSQL 18", ["one database, one table per owner"], "blue", "#16306a")
    + box(4, 1250, 590, 470, 110, "📜", "report-worker", ["JavaScript · writes reports"], "ok", "#0f2a22")
    + arrow(4, 1245, 640, 1165, 625)
), [
    S("Here is the platform. Users open the bookshop in the browser, and every request enters through one door: the "
      "Ingress."),
    S("The Ingress looks at the path. Slash goes to the React frontend. Slash A P I slash users goes to the Node.js "
      "A P I, books to the Java A P I, stats to the Python A P I, status to the Go status board."),
    S("And requests for the admin host name go to the Laravel reviews admin. Seven applications, one entry point."),
    S("Four of them store their data in one PostgreSQL database, each in its own table: users from Node.js, books from "
      "Java, reviews from Laravel."),
    S("And a small JavaScript job runs on a schedule, collects statistics and the status of all services, and writes "
      "a report into the database."),
])

scene(None, "docs/CONTRACT.md", "One contract, seven implementations", code(
    "applications/node-api/src/server.js (excerpt)",
    excerpt("applications/node-api/src/server.js", "liveness", "res.status(503)"), "javascript", 21) + notes([
    (0, "Port from the environment", "PORT, listening on 0.0.0.0"),
    (1, "/health: am I alive?", "never checks the database: used for liveness"),
    (2, "/ready: can I do my job?", "checks the database: used for readiness"),
    (3, "Config from env, logs to stdout", "DB_HOST ... DB_PASSWORD; a missing password stops the app with a clear message"),
]), [
    S("Seven languages could mean seven different ways of doing everything. So every application follows one "
      "contract. First: the port comes from an environment variable."),
    S("Second: slash health answers as soon as the process works. It does not check the database, on purpose.", hl=(1, 2)),
    S("Third: slash ready answers only when the database answers too. Kubernetes will use these two endpoints in "
      "completely different ways.", hl=(4, 11)),
    S("And fourth: all configuration comes from environment variables, and all logs go to standard out. These few "
      "rules are what Kubernetes actually needs. The language behind them does not matter."),
], layout="code")

# ---------------------------------------------------------------- 3. Why multiple technology stacks?
scene("Why multiple technology stacks?", "docs/02", "What Kubernetes sees, and what it doesn't", grid([
    card(0, "👀", "Kubernetes sees", "an image · a port · environment variables · /health and /ready · stdout · exit codes · SIGTERM", "ok"),
    card(1, "🙈", "Kubernetes does not see", "the language · the framework · the build tool · how the code is organised", "bad"),
    card(2, "🏢", "Why companies have many stacks", "teams choose the best tool for each job; acquisitions; old and new systems side by side", "amber"),
    card(3, "🧩", "The pattern you learn", "once you can deploy these seven, you can deploy the eighth, in any language", "blue"),
], cols=2), [
    S("Why seven stacks? Because that is what a real company looks like. And because it proves the most important "
      "idea of this course. Kubernetes sees an image, a port, environment variables, health endpoints, logs and exit "
      "codes."),
    S("It does not see the language, the framework or the build tool. A Go binary and a Java JAR look the same to it: "
      "a container."),
    S("Companies end up with many stacks for good reasons: each team picks the right tool, old systems live next to "
      "new ones."),
    S("So the skill is not deploying Node.js or deploying Java. It is a pattern, and once you have used it seven times, "
      "you can use it for the eighth."),
])

scene(None, "docs/02", "JavaScript is a language. Node.js is a runtime.", svg(
    box(0, 0, 60, 540, 280, "🌐", "In the browser", ["React (the frontend)", "JavaScript runs in the user's browser", "the container only serves files"], "blue")
    + box(1, 590, 60, 540, 280, "🟩", "On the server", ["node-api (Express)", "JavaScript runs in Node.js", "a server: runs until stopped"], "ok", "#0f2a22")
    + box(2, 1180, 60, 540, 280, "📜", "As a batch job", ["report-worker (no framework)", "JavaScript runs in Node.js", "does one task, then exits"], "amber", "#2b2410")
    + label(3, 860, 450, "One language, three very different workloads:", 32, "sky", "middle", 800)
    + label(3, 860, 510, "a Deployment serving files · a Deployment serving an API · a CronJob that exits", 30, "amber", "middle", 700)
), [
    S("Three of our seven applications are JavaScript, and that is a lesson on its own. JavaScript is a language. "
      "In React, it runs in the user's browser; our container only serves the files."),
    S("Node.js is a runtime that runs JavaScript outside the browser. node-api is a server: it runs until it is stopped."),
    S("report-worker is JavaScript on Node.js too, but it is a batch job: it does one task and exits."),
    S("For Kubernetes these are three different workloads: a Deployment serving files, a Deployment serving an A P I, "
      "and a CronJob. The language is not what decides; the behaviour is."),
])
