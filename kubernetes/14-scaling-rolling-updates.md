# 14 · Scaling, rolling updates and rollbacks

> Level 18 of the [roadmap](../README.md). Time: 20 minutes. The concepts: [docs/12](../docs/12-scaling-rolling-updates-rollbacks.md).

## Step 1 · Scale out

<!-- test: contains=scaled -->
```bash
kubectl scale deployment node-api --replicas=3
```

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/node-api --timeout=240s
kubectl get pods -l app=node-api -o wide
```

```text
Waiting for deployment "node-api" rollout to finish: 2 of 3 updated replicas are available...
deployment "node-api" successfully rolled out
NAME                       READY   STATUS    RESTARTS   AGE   IP            NODE              NOMINATED NODE   READINESS GATES
node-api-6f678b5b5-69k57   1/1     Running   0          6s    10.244.1.35   bookshop-worker   <none>           <none>
node-api-6f678b5b5-kjn8h   1/1     Running   0          63s   10.244.1.31   bookshop-worker   <none>           <none>
node-api-6f678b5b5-l2dnl   1/1     Running   0          64s   10.244.1.30   bookshop-worker   <none>           <none>
```

Three identical Pods behind one Service. More replicas mean more capacity, and that one Pod (or its node) can fail
without an outage. In Compose this was copying service blocks or `--scale`; here it is one number.

## Step 2 · Build version 1.1.0

A new version is a new image with a new tag. The version is a build argument (see the
[Dockerfile](../applications/node-api/Dockerfile)); same code, so the change is visible only in the version field:

<!-- test: timeout=900; contains=node-api:1.1.0 -->
```bash
docker build --build-arg APP_VERSION=1.1.0 -t node-api:1.1.0 applications/node-api > /dev/null
kind load docker-image node-api:1.1.0 --name bookshop
```

## Step 3 · Roll it out

<!-- test: contains=image updated -->
```bash
kubectl set image deployment/node-api node-api=node-api:1.1.0
kubectl annotate deployment/node-api kubernetes.io/change-cause="node-api 1.1.0" --overwrite > /dev/null
```

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl rollout status deployment/node-api --timeout=240s
```

```text
Waiting for deployment "node-api" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "node-api" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "node-api" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "node-api" rollout to finish: 1 old replicas are pending termination...
deployment "node-api" successfully rolled out
```

The Deployment created a new ReplicaSet for the new Pod template and moved Pods over one at a time (at most 25 % extra,
at most 25 % unavailable), each new Pod first passing its readiness probe. The old ReplicaSet is kept, scaled to 0:

<!-- test: contains=node-api; output -->
```bash
kubectl get replicasets -l app=node-api
kubectl exec deploy/node-api -- wget -qO- http://127.0.0.1:3000/; echo
```

```text
NAME                  DESIRED   CURRENT   READY   AGE
node-api-698cbcbcdd   3         3         3       81s
node-api-6f678b5b5    0         0         0       6m40s
{"service":"node-api","version":"1.1.0","language":"JavaScript","runtime":"Node.js 24.21.0","description":"Users API of the Bookshop (Express)"}
```

<!-- test: contains=1.1.0; output -->
```bash
kubectl rollout history deployment/node-api
```

```text
deployment.apps/node-api 
REVISION  CHANGE-CAUSE
3         <none>
4         node-api 1.1.0
```

## Step 4 · Roll back

Version 1.1.0 turns out to be bad. Go back to the previous revision; the old ReplicaSet is simply scaled up again:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout undo deployment/node-api
kubectl rollout status deployment/node-api --timeout=240s
```

<!-- test: contains="version":"1.0.0"; output -->
```bash
kubectl get deployment node-api -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
kubectl exec deploy/node-api -- wget -qO- http://127.0.0.1:3000/; echo
```

```text
node-api:1.0.0
{"service":"node-api","version":"1.0.0","language":"JavaScript","runtime":"Node.js 24.21.0","description":"Users API of the Bookshop (Express)"}
```

A rollback is only this easy because every version has its own tag: `node-api:1.0.0` is still exactly the image that
ran before. With `latest`, "the previous version" would not exist anymore.

<!-- test: contains=scaled -->
```bash
kubectl scale deployment node-api --replicas=2
```

The platform is complete. The [troubleshooting labs](../troubleshooting/README.md) break it in twelve ways, and the
[capstone](../capstone/README.md) verifies everything at once. When you are done: [cleanup](cleanup.md).
