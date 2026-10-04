"""Chapters 4-15: build and Dockerize each application (Node.js, React, Python, Go, Java, Laravel)."""

from __future__ import annotations

from components import arrow, box, code, label, notes, svg, terminal
from recordings import rec
from scenes_common import APP, S, bare, excerpt, scene

SHOT = "../../docs/images/bookshop-ui-kubernetes.png"


def lines_of(first: str, last: str, path: str = "applications/frontend/Dockerfile") -> tuple[int, int]:
    """Line range in bare(path) from the line starting with `first` to the next line starting with `last`.
    A `first` ending in a newline must match the whole line (to tell two similar FROM lines apart)."""
    ls = bare(path).splitlines()
    exact = first.endswith("\n")
    f = first.rstrip("\n")
    a = next(i for i, x in enumerate(ls, 1) if (x == f if exact else x.startswith(f)))
    return a, next(i for i, x in enumerate(ls, 1) if i >= a and last in x)


def hl_in(text: str, first: str, last: str) -> tuple[int, int]:
    """Line range inside an excerpt."""
    ls = text.splitlines()
    a = next(i for i, x in enumerate(ls, 1) if first in x)
    return a, next(i for i, x in enumerate(ls, 1) if i >= a and last in x)


PY_EX = excerpt("applications/python-api/src/main.py", '@app.get("/health")', "def stats")

# ---------------------------------------------------------------- 4. Node.js
scene("Build the Node.js application", "applications/node-api", "node-api: users, with Express", code(
    "applications/node-api/src/server.js (excerpt)",
    excerpt("applications/node-api/src/server.js", "if (!process.env.DB_PASSWORD)", "password: process.env.DB_PASSWORD"),
    "javascript", 21) + notes([
    (0, "Fail fast", "no password → a clear message and exit code 1, not a crash later"),
    (1, "Configuration from env", "host, port, database, user, password: nothing hard-coded"),
    (2, "Endpoints", "/, /health, /ready, GET and POST /api/users; table users created and seeded at start"),
]), [
    S("The first application: a users A P I in Node.js with Express. Before anything else, it checks that the database "
      "password is set. If not, it prints a clear message and exits with code 1.", hl=(1, 5)),
    S("All connection settings come from environment variables. Nothing about the environment is written in the code."),
    S("Besides the health endpoints it has two routes: list users, and add a user. When it starts, it creates its table "
      "and three sample users. That is all the application logic we need: the subject is deployment."),
], layout="code")

scene("Dockerize Node.js", "applications/node-api/Dockerfile", "A Dockerfile for an interpreted language", code(
    "applications/node-api/Dockerfile", bare("applications/node-api/Dockerfile"), "docker", 22) + notes([
    (0, "Base image with a pinned version", "node:24.21-alpine, never latest"),
    (1, "Dependencies first", "package files, then npm ci: this layer is cached until they change"),
    (2, "Then the code, the version, the port", "APP_VERSION is a build argument: the tag and the app agree"),
    (3, "Not root", "USER node; CMD in exec form, so Node is process 1 and receives SIGTERM"),
]), [
    S("The Dockerfile. Node.js needs no compile step, so this is a single stage: start from the official Node image, "
      "with a pinned version."),
    S("Copy only the package files first, and install production dependencies. Docker caches this layer: changing your "
      "code does not reinstall every package.", hl=(3, 4)),
    S("Then the source code, the version as a build argument, and the port.", hl=(5, 9)),
    S("And finally: run as the unprivileged user node, with the command in exec form, so Node is process one and "
      "receives the stop signal directly.", hl=(10, 12)),
], layout="code")

scene(None, "Recorded · applications/node-api", "Build, run, and break it on purpose", terminal(
    rec(APP["node-api"], "docker images node-api", grep="IMAGE|REPOSITORY|1\.0\.0", drop="WARNING")
    + rec(APP["node-api"], "curl -s http://localhost:3000/api/users", step=1, width=150, tones={"Ada": "ok"})
    + rec(APP["node-api"], "docker run --rm node-api:1.0.0", step=2, wrap=118, tones={"DB_PASSWORD": "bad"}),
    "bash (recorded)"), [
    S("Build the image and look at it: about 250 megabytes, most of it the Node.js runtime."),
    S("Run it next to a PostgreSQL container, and the A P I answers with the three seeded users.", zoom=1.2),
    S("And without a password, it refuses to start, with a message that says exactly what is missing. Remember this "
      "behaviour: in Kubernetes it turns into a crash loop with an obvious cause.", zoom=1.3),
])

# ---------------------------------------------------------------- 6. React
scene("Build the React application", "applications/frontend", "Development server vs production build", svg(
    box(0, 0, 40, 820, 300, "🛠️", "npm run dev (development)", ["Vite dev server on port 5173", "hot reload while you edit", "unoptimised, needs Node.js and node_modules", "NEVER for production"], "amber", "#2b2410")
    + box(1, 900, 40, 820, 300, "📦", "npm run build (production)", ["plain static files in dist/", "minified, hashed file names, 244 KB", "any web server can serve them", "the browser runs the JavaScript"], "ok", "#0f2a22")
    + arrow(2, 1310, 350, 1310, 430)
    + box(2, 900, 440, 820, 200, "🌐", "nginx serves dist/ on port 8080", ["+ /health, /config.js, and in Compose", "  a proxy for /api/* to the APIs"], "blue")
    + label(3, 420, 470, "The React code does not run in the container.", 30, "sky", "middle", 800)
    + label(3, 420, 520, "It runs in the user's browser.", 30, "sky", "middle", 800)
), [
    S("React is the one stack that is not a server. While you develop, Vite's dev server compiles on the fly and "
      "reloads the page when you edit. Great for development, never for production."),
    S("For production, npm run build turns the whole application into a few static files: about two hundred and "
      "forty kilobytes."),
    S("Any web server can serve those files. We use nginx, which also answers the health check, serves the runtime "
      "configuration, and in Compose forwards the A P I calls."),
    S("The important insight: the React code never runs in the container. It runs in the browser. The container is "
      "just a file server."),
])

scene(None, "applications/frontend", "Four panels, four backends", f'<img class="shot st" data-s="0" src="{SHOT}" alt="The Bookshop UI" style="height:700px;width:auto">', [
    S("The page has four panels: books from Java, users from Node.js, statistics from Python, and the status of every "
      "service from Go. Each panel shows its own error when its backend is missing, which will help us troubleshoot."),
])

scene("Dockerize React", "applications/frontend/Dockerfile", "A multi-stage build: Node to build, nginx to serve", code(
    "applications/frontend/Dockerfile", bare("applications/frontend/Dockerfile"), "docker", 17) + notes([
    (0, "Stage 1: node", "npm ci, npm run build → dist/"),
    (1, "Stage 2: nginx-unprivileged", "only dist/ is copied over; Node.js stays behind"),
    (2, "Runtime configuration", "config.js written at container start from env: one image for every environment"),
]), [
    S("This Dockerfile has two stages. The first one starts from Node, installs the dependencies and runs the build.",
      hl=lines_of("FROM node", "RUN npm run build")),
    S("The second stage starts fresh from nginx, and copies only the built files from the first. Node.js, the "
      "dependencies and the source code are left behind.", hl=lines_of("FROM nginxinc", "EXPOSE")),
    S("One more trick: the settings, like the admin link, are written into a small config file when the container "
      "starts. A normal React build bakes them in at build time, which would need one image per environment."),
], layout="code")

scene(None, "Recorded · applications/frontend", "334 MB to build, 82 MB to run", terminal(
    rec(APP["frontend"], "docker images --format 'table {{.Repository}}:{{.Tag}}", drop="WARNING", tones={"frontend:1.0.0": "ok"})
    + rec(APP["frontend"], "curl -s http://localhost:8081/config.js", step=1)
    + rec(APP["frontend"], "curl -s -w '\\nHTTP %{http_code}\\n' http://localhost:8081/api/books", step=2, tones={"502": "bad"}),
    "bash (recorded)"), [
    S("The result: the build stage is three hundred and thirty-four megabytes, the final image eighty-two. What you "
      "ship is only what you need to run.", zoom=1.25),
    S("The runtime configuration, generated when the container started.", zoom=1.3),
    S("And with no backend running, an A P I call returns a clean five oh two with a JSON message, instead of nginx "
      "refusing to start.", zoom=1.3),
])

# ---------------------------------------------------------------- 8. Python
scene("Build the Python application", "applications/python-api", "python-api: statistics, with FastAPI", code(
    "applications/python-api/src/main.py (excerpt)",
    PY_EX, "python", 21) + notes([
    (0, "/health", "the process answers: liveness"),
    (1, "/ready", "SELECT 1 against PostgreSQL: 503 with the reason when it fails"),
    (2, "/api/stats", "counts rows in tables other services own; a missing table counts as 0"),
]), [
    S("The Python A P I uses FastAPI. Slash health just answers.", hl=hl_in(PY_EX, "/health", "return")),
    S("Slash ready runs a tiny query against the database and returns five oh three with the reason if it fails.",
      hl=hl_in(PY_EX, "/ready", "503")),
    S("And slash A P I slash stats counts the users, books and reviews that the other services store. A table that "
      "does not exist yet counts as zero, so the order in which services start does not matter."),
], layout="code")

scene("Dockerize Python", "applications/python-api/Dockerfile", "A virtual environment, built once, copied over", code(
    "applications/python-api/Dockerfile", bare("applications/python-api/Dockerfile"), "docker", 19) + notes([
    (0, "Build stage", "create a venv and pip install the pinned requirements"),
    (1, "Final stage", "a fresh python:3.14-slim plus only the venv and the code"),
    (2, "Same rules", "non-root user 10001, versioned, logs unbuffered to stdout"),
]), [
    S("Python is interpreted, but its dependencies can include compiled parts and build tools. So we install them in a "
      "virtual environment, in a build stage.", hl=lines_of("FROM python:3.14-slim AS build", "pip install", "applications/python-api/Dockerfile")),
    S("The final stage starts clean and copies only the virtual environment and the code.",
      hl=lines_of("FROM python:3.14-slim\n", "CMD", "applications/python-api/Dockerfile")),
    S("Same rules as before: a fixed user I D instead of root, the version as a build argument, logs unbuffered to "
      "standard out."),
], layout="code")

scene(None, "Recorded · applications/python-api", "Alive, but not ready", terminal(
    rec(APP["python-api"], "curl -s http://localhost:18000/api/stats", tones={"users": "ok"})
    + rec(APP["python-api"], "-> HTTP %{http_code}\\n' http://localhost:18000/ready", step=1, wrap=118, tones={"503": "bad", "200": "ok"}),
    "bash (recorded)"), [
    S("Running against PostgreSQL, the statistics endpoint counts the rows."),
    S("Now stop the database. Slash ready answers five oh three: I cannot do my job. Slash health still answers two "
      "hundred: I am alive. In Kubernetes, that difference decides between taking a Pod out of traffic and restarting "
      "it.", zoom=1.2),
])

# ---------------------------------------------------------------- 10. Go
scene("Build the Go application", "applications/go-status", "go-status: checks every service, in parallel", code(
    "applications/go-status/main.go (excerpt)",
    excerpt("applications/go-status/main.go", "var wg sync.WaitGroup", "wg.Wait()"), "go", 22) + notes([
    (0, "TARGETS from the environment", "name=url pairs: the /health URL of every service"),
    (1, "One goroutine per target", "all checks run at the same time, each with a 2 s timeout"),
    (2, "No dependencies at all", "only Go's standard library: go.mod has no require lines"),
]), [
    S("The Go service is the status board. It reads the list of services to check from one environment variable."),
    S("For each target it starts a goroutine, so all the health checks run in parallel, each with a two second "
      "timeout, and then it waits for all of them."),
    S("And it uses nothing but Go's standard library. No framework, no dependencies."),
], layout="code")

scene("Dockerize Go", "applications/go-status/Dockerfile", "Compile, then ship only the binary", code(
    "applications/go-status/Dockerfile", bare("applications/go-status/Dockerfile"), "docker", 19) + notes([
    (0, "Build stage: golang", "a static binary: CGO_ENABLED=0, stripped, version baked in"),
    (1, "Final stage: distroless", "no shell, no package manager, no libc: just the binary and a non-root user"),
]), [
    S("Go compiles to a single binary. The build stage uses the full Go toolchain and builds a static, stripped "
      "binary, with the version baked in.", hl=lines_of("FROM golang", "go build", "applications/go-status/Dockerfile")),
    S("The final stage is distroless: no shell, no package manager, nothing but our binary and a non-root user.",
      hl=lines_of("FROM gcr.io", "ENTRYPOINT", "applications/go-status/Dockerfile")),
], layout="code")

scene(None, "Recorded · applications/go-status", "16 MB, and no shell to attack", terminal(
    rec(APP["go-status"], "docker build -t go-status:1.0.0", grep="^IMAGE|^go-status", cmd="docker images go-status", tones={"go-status": "ok"})
    + rec(APP["go-status"], "golang:1.27-alpine", step=1, drop="WARNING", cmd="docker images golang:1.27-alpine")
    + rec(APP["go-status"], "docker exec go-lab-status sh -c 'echo hi'", step=2, wrap=118, tones={"executable file not found": "bad"}),
    "bash (recorded)"), [
    S("The final image: about sixteen megabytes.", zoom=1.3),
    S("The toolchain image it was built with: three hundred and eighty. None of that is shipped.", zoom=1.3),
    S("And there is no shell inside. Trying to open one fails. That is a security feature: an attacker who gets in finds "
      "nothing to work with.", zoom=1.2),
])

# ---------------------------------------------------------------- 12. Java
scene("Build the Java application", "applications/java-api", "java-api: books, with Spring Boot", code(
    "applications/java-api/src/main/java/lab/bookshop/BookController.java (excerpt)",
    excerpt("applications/java-api/src/main/java/lab/bookshop/BookController.java", '@GetMapping("/health")', '@GetMapping("/api/books")'),
    "java", 20) + notes([
    (0, "Spring Boot 4.1 on Java 25", "web MVC + plain JDBC; no JPA, no actuator: deliberately small"),
    (1, "/health and /ready", "the same contract, in Java"),
    (2, "Starts even without a database", "/ready says why it is not ready; the schema is created when the database answers"),
]), [
    S("The books A P I in Java, with Spring Boot. A plain controller with plain J D B C: as small as a Spring application gets."),
    S("The same contract again: slash health, and slash ready with a real query."),
    S("And one design choice: it starts even when the database is unreachable, and reports why in slash ready. A "
      "service that refuses to start because a dependency is briefly down causes restart storms."),
], layout="code")

scene("Dockerize Java", "applications/java-api/Dockerfile", "Maven builds a JAR, a JRE runs it", code(
    "applications/java-api/Dockerfile", bare("applications/java-api/Dockerfile"), "docker", 19) + notes([
    (0, "Build stage: Maven + JDK", "dependencies first (cached), then mvn package → app.jar"),
    (1, "Final stage: JRE only", "no compiler, no Maven, no source code"),
    (2, "-XX:MaxRAMPercentage=75", "the JVM sizes its heap from the container's memory limit"),
]), [
    S("Java has a real build: Maven downloads the dependencies, compiles, and packages one JAR file. Dependencies "
      "first, so they are cached.", hl=lines_of("FROM maven", "mvn -B -q package", "applications/java-api/Dockerfile")),
    S("The final stage needs only a Java runtime, not the compiler and not Maven.",
      hl=lines_of("FROM eclipse-temurin", "COPY --from=build", "applications/java-api/Dockerfile")),
    S("And one line matters a lot in containers: max RAM percentage tells the JVM to size its heap from the container's "
      "memory limit, not from the memory of the whole machine.", hl=lines_of("ENTRYPOINT", "ENTRYPOINT", "applications/java-api/Dockerfile")),
], layout="code")

scene(None, "Recorded · applications/java-api", "Sizes, and seconds to start", terminal(
    rec(APP["java-api"], "--target build -t java-api:build-stage", drop="WARNING", tones={"java-api:1.0.0": "ok"})
    + rec(APP["java-api"], "grep -E 'Starting|Started|Tomcat started|books table'", step=1, width=150, tones={"Started": "ok"}),
    "bash (recorded)"), [
    S("The build stage with Maven and the full JDK, against the runtime image: the runtime is about half the size.", zoom=1.2),
    S("And the startup: a few seconds on a free CPU, more when the CPU is limited. Kubernetes must know that, or it "
      "will kill the JVM while it is still starting. We will give it a startup probe.", zoom=1.15),
])

# ---------------------------------------------------------------- 14. Laravel
scene("Build the Laravel application", "applications/laravel-admin", "Why Laravel needs two containers", svg(
    box(0, 0, 60, 520, 230, "🌐", "nginx (laravel-web)", ["HTTP on port 8080", "serves CSS and images itself", "passes *.php to PHP-FPM"], "blue")
    + arrow(0, 530, 175, 640, 175, label="FastCGI :9000")
    + box(1, 650, 60, 520, 230, "🐘", "PHP-FPM (laravel-fpm)", ["runs the PHP code", "Laravel 13 on PHP 8.5", "a pool of PHP workers"], "violet", "#221a3a")
    + arrow(1, 1180, 175, 1290, 175)
    + box(1, 1300, 60, 420, 230, "🗄️", "PostgreSQL", ["table reviews"], "blue", "#16306a")
    + box(2, 650, 360, 520, 200, "🧰", "migrations (once)", ["php artisan migrate --seed", "same image as FPM, then exit"], "amber", "#2b2410")
    + arrow(2, 1180, 460, 1290, 300)
    + label(3, 860, 640, "One process per container: the web server and the PHP runtime are separate, and scale together.", 28, "sky", "middle", 700)
), [
    S("Laravel is the most complex stack here, because PHP usually runs behind a web server. nginx handles H T T P and "
      "static files, and passes PHP requests to PHP F P M over FastCGI on port nine thousand."),
    S("PHP F P M runs the Laravel code, which reads and writes the reviews table."),
    S("And database migrations are a separate step that runs once, with the same image, and exits. Never in every "
      "copy of the application at startup."),
    S("Two containers, because each container should run one process. In Kubernetes they will become one Pod with two "
      "containers."),
])

scene("Dockerize Laravel", "applications/laravel-admin/Dockerfile.fpm", "Composer to install, PHP-FPM to run", code(
    "applications/laravel-admin/Dockerfile.fpm", bare("applications/laravel-admin/Dockerfile.fpm"), "docker", 15) + notes([
    (0, "Stage 1: composer", "install PHP dependencies without dev packages, optimised autoloader"),
    (1, "Stage 2: php:8.5-fpm-alpine", "+ the pdo_pgsql extension, the app, non-root www-data"),
    (2, "No config:cache at build", "configuration differs per environment: it is read at start"),
]), [
    S("The PHP image: Composer installs the dependencies in a first stage, without development packages.",
      hl=lines_of("FROM composer", "composer install", "applications/laravel-admin/Dockerfile.fpm")),
    S("The final stage is the official PHP F P M image with the PostgreSQL extension, the application, and the "
      "unprivileged www-data user."),
    S("Laravel can cache its configuration for speed, but we deliberately do not do that at build time: the values come "
      "from the environment and differ between Compose and Kubernetes."),
], layout="code")

scene(None, "Recorded · applications/laravel-admin", "Migrate, serve, and the 502 every PHP developer knows", terminal(
    rec(APP["laravel-admin"], "docker images --format 'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}' | grep -E 'REPOSITORY|laravel'", drop="WARNING")
    + rec(APP["laravel-admin"], "php artisan migrate --force --seed", step=1, tail=4)
    + rec(APP["laravel-admin"], "laravel-web-broken", step=2, tail=3, wrap=118, tones={"502": "bad"}),
    "bash (recorded)"), [
    S("Two images: PHP F P M, and nginx with the public files."),
    S("The migration runs once in a throw-away container, creates the reviews table and adds three sample reviews."),
    S("And the classic failure: nginx without a reachable PHP F P M answers five oh two, bad gateway. Its log says "
      "connection refused to port nine thousand. Now you know where to look when you see it.", zoom=1.2),
])
