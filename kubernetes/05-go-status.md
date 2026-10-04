# 05 · Deploy go-status (Go)

> Level 11 of the [roadmap](../README.md). Time: 10 minutes. The application: [applications/go-status](../applications/go-status/README.md).

go-status has no database, so its Deployment has no Secret and its readiness probe is `/health`. Its configuration
is one variable, `TARGETS`, the list of `/health` URLs it checks, from the ConfigMap. They are the **Service names**:
the same names as in Compose, resolved by the cluster's DNS.

<!-- test: contains=node-api=http://node-api:3000/health; output -->
```bash
kubectl get configmap bookshop-config -o jsonpath='{.data.TARGETS}' | tr ',' '\n'
```

```text
frontend=http://frontend:8080/health
node-api=http://node-api:3000/health
python-api=http://python-api:8000/health
go-status=http://go-status:8080/health
java-api=http://java-api:8080/health
laravel-admin=http://laravel-admin:8080/health
```

<!-- test: timeout=300; contains=go-status:1.0.0 -->
```bash
kind load docker-image go-status:1.0.0 --name bookshop
```

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/go-status/
kubectl rollout status deployment/go-status --timeout=240s
```

The status board, from inside the cluster:

<!-- test: retry=10; contains=node-api; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- http://go-status:8080/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"{d['up']} of {d['total']} services up\")
for s in d['services']:
    print(f\"  {s['name']:14} {s['status']:5} {s.get('http_status') or ''}\")"
```

```text
4 of 6 services up
  frontend       up    200
  go-status      up    200
  java-api       down  
  laravel-admin  down  
  node-api       up    200
  python-api     up    200
```

The board already knows the whole platform. What is not deployed yet shows as down: its Service name does not exist
yet. That will change in the next lessons.

The image is the smallest of the lab (a static binary on a distroless base, [docs/03](../docs/03-dockerfiles-across-stacks.md)),
and the container has no shell at all: `kubectl exec` into it fails. That is a security feature, not a bug.

<!-- test: fail; output -->
```bash
kubectl exec deploy/go-status -- sh -c 'echo hello'
```

```text
error: Internal error occurred: Internal error occurred: error executing command in container: failed to exec in container: failed to start exec "845c51db7c4aa8f4a2b84836cc2e9e275e9c34e8355ada3c67a905a4b80e57e4": OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file not found in $PATH
```

Next: [06 · java-api](06-java-api.md).
