Most teams don't run one language. They run a React frontend, a Node.js API, a Python service, something in Go, a Java backend, an old Laravel app, and a few scripts. And each one somehow gets deployed differently. So I built a free lab that takes seven stacks through one path: Dockerfile → Docker Compose → Kubernetes. 🧩👇

Think of shipping containers. Seven different factories make seven different products. But the port doesn't care what's inside: every product goes into the same standard box, and one crane moves them all. In this lab the box is a container image with a small contract (a port, /health, /ready, config from environment variables, logs to stdout), and Kubernetes is the crane.

That is "Multi-Stack Applications on Kubernetes", a small Bookshop platform:

⚛️ React UI (built by Vite, served by nginx)
🟩 Node.js users API (Express)
🐍 Python statistics API (FastAPI)
🐹 Go status board that checks every service
☕ Java books API (Spring Boot)
🐘 Laravel reviews admin (nginx + PHP-FPM in one Pod)
📜 a plain JavaScript batch job that runs as a CronJob

Every app is Dockerized first, then the whole platform runs with Docker Compose, then the same images go to Kubernetes: Deployments, Services, ConfigMaps, Secrets, a StatefulSet for PostgreSQL, a Job for migrations, probes, resource limits and one Ingress.

Real numbers from the lab (image size, final vs build stage):
📦 Go: 16.4 MB (built with a 381 MB toolchain image)
📦 React: 81.8 MB (build stage 334 MB)
📦 Java: 348 MB (build stage 677 MB)

And 12 troubleshooting labs reproduce the errors you meet at work:
⛔ ImagePullBackOff
⛔ CrashLoopBackOff: "Cannot find module"
⛔ OOMKilled, exit code 137
⛔ 503 "no available server" from a Service selector typo
⛔ "password authentication failed" after a wrong Secret

Each one: symptoms → investigation → root cause → fix → verification.

✅ Every command in the lessons runs automatically in GitHub Actions: each app on Docker, the platform on Compose, and everything on a real kind cluster. The outputs in the docs are the real outputs.
✅ The capstone deploys the whole platform with one script, and a verification script runs 22 checks. Then a "Monday morning" scenario breaks three things at once for you to fix.

Study material: 15 concept lessons, a 14-chapter guided tutorial, 6 challenge labs, a 36-chapter video (full and silent versions), a 75-page study guide PDF, a 79-term glossary and 25 interview questions.

🔗 Repository: https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes
🌐 All my projects: https://sufyanahmadkamboh.github.io/

How many stacks does your team ship to Kubernetes? 💬

#Kubernetes #Docker #DockerCompose #DevOps #CloudNative #Microservices #LearningDevOps #OpenSource
