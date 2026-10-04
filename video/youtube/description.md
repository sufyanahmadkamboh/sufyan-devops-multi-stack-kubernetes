Multi-Stack Applications on Kubernetes: take seven applications written in different stacks (React, Node.js with Express, Python with FastAPI, Go, Java with Spring Boot, PHP with Laravel, and a plain JavaScript batch job), package each one as a Docker image, run them together with Docker Compose, and deploy the same images to Kubernetes with the right resource for each job: Deployments, Services, an Ingress, ConfigMaps, Secrets, a StatefulSet with a persistent volume, a Job, a CronJob and a multi-container Pod. Then health probes, resources, scaling, rolling updates and rollbacks, and twelve troubleshooting labs. Every terminal shows real output, recorded while the lessons ran on Docker and on a real kind cluster.

💻 The lab (free, open source): https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Do it yourself (Docker, kind, kubectl and Helm, no cloud account):
1. git clone https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes.git
2. Open tutorial/00-start-here.md and follow the 20 levels
3. Break the platform with the troubleshooting labs, then take the capstone

⏱️ Chapters
0:00 Introduction
1:16 Project architecture
2:47 Why multiple technology stacks?
4:10 Build the Node.js application
4:46 Dockerize Node.js
5:47 Build the React application
6:44 Dockerize React
7:39 Build the Python application
8:04 Dockerize Python
8:50 Build the Go application
9:13 Dockerize Go
9:52 Build the Java application
10:20 Dockerize Java
11:08 Build the Laravel application
11:48 Dockerize Laravel
12:43 Run everything with Docker Compose
14:09 Understand Compose networking
14:58 From Compose to Kubernetes
16:13 Deploy Node.js
17:17 Deploy React
17:44 Deploy Python
18:08 Deploy Go
18:28 Deploy Java
19:19 Deploy Laravel
20:18 Services and networking
21:19 ConfigMaps and Secrets
22:10 Health probes
23:10 Storage
23:36 Ingress
24:28 Scaling
25:17 Rolling updates
25:43 Rollbacks
26:09 Troubleshooting
28:39 Final multi-stack deployment
29:26 Cleanup
29:49 Final challenge

📊 What you will see (all recorded)
• seven Dockerfiles: single-stage, multi-stage, distroless (go-status 16 MB vs a 381 MB build image)
• Docker Compose with health-aware dependencies and network isolation ("bad address 'postgres'")
• every Compose line mapped to a Kubernetes resource, side by side
• a startup probe protecting a slow JVM; readiness vs liveness with the database taken away
• OOMKilled (exit 137) stopped by a rolling update; rollout undo with versioned tags
• ImagePullBackOff, CrashLoopBackOff, empty endpoints, 503 "no available server", "password authentication failed"

#Kubernetes #Docker #DevOps
