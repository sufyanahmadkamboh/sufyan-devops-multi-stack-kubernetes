# 04 · Deploy python-api (Python)

> Level 10 of the [roadmap](../README.md). Time: 10 minutes. The application: [applications/python-api](../applications/python-api/README.md).

Same pattern as node-api: an image, a Deployment with two replicas, a Service. A different language, the same YAML
shape. Compare [python-api/deployment.yaml](python-api/deployment.yaml) with
[node-api/deployment.yaml](node-api/deployment.yaml): only the name, image, port, user ID and resource numbers differ.

<!-- test: contains=port -->
```bash
diff <(sed 's/python-api/APP/g; s/8000/PORT/g' kubernetes/python-api/deployment.yaml) \
     <(sed 's/node-api/APP/g; s/3000/PORT/g' kubernetes/node-api/deployment.yaml) | grep '^[<>]' | head -12 || true
echo "(only these lines differ, apart from the name and port)"
```

## Step 1 · Load, apply, wait

<!-- test: timeout=300; contains=python-api:1.0.0 -->
```bash
kind load docker-image python-api:1.0.0 --name bookshop
```

<!-- test: timeout=300; contains=successfully rolled out; output -->
```bash
kubectl apply -f kubernetes/python-api/
kubectl rollout status deployment/python-api --timeout=240s
```

```text
deployment.apps/python-api created
service/python-api created
Waiting for deployment "python-api" rollout to finish: 0 of 2 updated replicas are available...
Waiting for deployment "python-api" rollout to finish: 1 of 2 updated replicas are available...
deployment "python-api" successfully rolled out
```

## Step 2 · Verify

<!-- test: retry=10; contains="users":3; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://python-api:8000/api/stats
echo
```

```text
{"users":3,"books":0,"reviews":0,"latest_report":null}
```

python-api counts rows in tables that other services own. `books` and `reviews` are still 0: java-api and Laravel
are not deployed yet, and python-api treats a missing table as 0 instead of failing.

<!-- test: contains=python-api; output=tail:4 -->
```bash
kubectl get pods -l app=python-api -o wide
kubectl logs deploy/python-api --tail=2
```

```text
...
python-api-54c69f569b-fkbk2   1/1     Running   0          7s    10.244.1.10   bookshop-worker   <none>           <none>
Found 2 pods, using pod/python-api-54c69f569b-dwlkk
2026-10-04 18:18:46,630 INFO python-api GET /ready 200
2026-10-04 18:18:46,875 INFO python-api GET /api/stats 200
```

Next: [05 · go-status](05-go-status.md).
