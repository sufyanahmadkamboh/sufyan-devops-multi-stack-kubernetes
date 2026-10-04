Multi-Stack Applications on Kubernetes: take seven applications written in different stacks (React, Node.js with Express, Python with FastAPI, Go, Java with Spring Boot, PHP with Laravel, and a plain JavaScript batch job), package each one as a Docker image, run them together with Docker Compose, and deploy the same images to Kubernetes with the right resource for each job: Deployments, Services, an Ingress, ConfigMaps, Secrets, a StatefulSet with a persistent volume, a Job, a CronJob and a multi-container Pod. Then health probes, resources, scaling, rolling updates and rollbacks, and twelve troubleshooting labs. Every terminal shows real output, recorded while the lessons ran on Docker and on a real kind cluster.

💻 The lab (free, open source): https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Do it yourself (Docker, kind, kubectl and Helm, no cloud account):
1. git clone https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes.git
2. Open tutorial/00-start-here.md and follow the 20 levels
3. Break the platform with the troubleshooting labs, then take the capstone

⏱️ Chapters
{{CHAPTERS}}

📊 What you will see (all recorded)
• seven Dockerfiles: single-stage, multi-stage, distroless (go-status 16 MB vs a 381 MB build image)
• Docker Compose with health-aware dependencies and network isolation ("bad address 'postgres'")
• every Compose line mapped to a Kubernetes resource, side by side
• a startup probe protecting a slow JVM; readiness vs liveness with the database taken away
• OOMKilled (exit 137) stopped by a rolling update; rollout undo with versioned tags
• ImagePullBackOff, CrashLoopBackOff, empty endpoints, 503 "no available server", "password authentication failed"

#Kubernetes #Docker #DevOps
