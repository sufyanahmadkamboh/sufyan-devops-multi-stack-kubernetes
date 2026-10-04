# Multi-Stack Applications on Kubernetes · project summary

**What:** a hands-on lab that takes seven applications in different stacks (React, Node.js, Python, Go, Java/Spring
Boot, PHP/Laravel, plain JavaScript) from Dockerfile to Docker Compose to Kubernetes, as one small platform
("Bookshop") behind one Ingress.

**Problem:** every stack seems to need its own deployment recipe; Kubernetes YAML gets copied without understanding;
moving from Compose to Kubernetes is done by trial and error; and nobody practises the failures before they happen in
production.

**Contents**
- 7 application lessons (build, Dockerize, run, troubleshoot), a Docker Compose lesson, 15 Kubernetes lessons on kind
  with Traefik, 15 concept lessons, a one-page service contract, a 20-level roadmap, a 14-chapter guided tutorial
- 12 troubleshooting labs: wrong image name, image pull failure, wrong container port, Service selector mismatch,
  application crash, missing environment variable, database connection failure, readiness probe failure, volume
  problem, works in the Pod but not through the Service, frontend cannot reach backend, incorrect ConfigMap/Secret
- 6 challenge labs (a new service taken through the whole path), a capstone (one-command deploy, a 25-check
  verification script, a three-fault on-call scenario)
- Study guide PDF (75 pages), glossary (79 terms), 25 interview questions, a 36-chapter video (full and silent)

**Engineering details**
- One contract for every app: port from the environment, `/health` (liveness) vs `/ready` (readiness, checks the
  database), configuration from environment variables, logs to stdout, non-root users, versioned image tags
- Kubernetes resources chosen per job: Deployments, Services, Ingress, ConfigMap, Secrets created from generated
  values, a PostgreSQL StatefulSet with a PersistentVolumeClaim, a migration Job, a CronJob, a two-container Pod
  (nginx + PHP-FPM), startup/liveness/readiness probes, requests and limits
- Measured in the lab (image size, final vs build stage): go-status 16.4 MB (golang image 381 MB), frontend 81.8 MB
  (334 MB), java-api 348 MB (677 MB), node-api 251 MB, python-api 261 MB, laravel-fpm 222 MB + laravel-web 81.5 MB;
  Spring Boot starts in 4.5 s in the cluster
- `tests/mdrun.py` runs every bash block of the lessons and writes the real output back into the docs; GitHub Actions
  runs each app lesson on Docker, the Compose lesson, and all Kubernetes lessons, troubleshooting labs, challenges and
  the capstone on a kind cluster

**Tech:** Docker, Docker Compose, Kubernetes 1.37 (kind), Traefik, Helm, PostgreSQL 18, Node.js 24, React 19 + Vite,
Python 3.14 + FastAPI, Go 1.27, Java 25 + Spring Boot 4.1, PHP 8.5 + Laravel 13, nginx, GitHub Actions.
