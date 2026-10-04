# 10 · It works inside the Pod, but not through the Service

> Time: 15 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

Someone "fixes" the python-api Service and sets its `targetPort` to 8080, the port most other services in the lab
use:

<!-- test: contains=service/python-api patched -->
```bash
kubectl patch service python-api --type json -p '[{"op":"replace","path":"/spec/ports/0/targetPort","value":8080}]'
```

## Problem

The statistics panel fails. The developer of python-api says: "My application works, I just checked it."

## Symptoms

<!-- test: retry=15; contains=502; output -->
```bash
curl -s -w '\nHTTP %{http_code}\n' http://bookshop.localhost:8080/api/stats
kubectl get pods -l app=python-api
```

```text
Bad Gateway
HTTP 502
NAME                          READY   STATUS    RESTARTS   AGE
python-api-54c69f569b-2wcr5   1/1     Running   0          3m
python-api-54c69f569b-tht6x   1/1     Running   0          3m6s
```

The Pods are `Running` and `1/1` Ready. Unlike [lab 04](04-service-selector-mismatch.md), Traefik has servers to send
the request to (502 Bad Gateway, not 503), but they do not answer.

## Investigation

Test the same request at each hop: inside the Pod (application), through the Service (Kubernetes networking), and
compare the ports.

## Commands

Inside a python-api Pod, the application answers on its own port 8000:

<!-- test: contains="status":"ok"; output -->
```bash
kubectl exec deploy/python-api -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode())"
```

```text
{"status":"ok","service":"python-api","version":"1.0.0"}
```

Through the Service, from another Pod:

<!-- test: contains=refused; output -->
```bash
kubectl exec deploy/node-api -- wget -qO- -T 3 http://python-api:8000/health 2>&1 || true
```

```text
wget: can't connect to remote host (10.96.214.218): Connection refused
command terminated with exit code 1
```

<!-- test: contains=8080; output -->
```bash
kubectl describe service python-api | grep -E 'Port|Endpoints'
kubectl get pods -l app=python-api -o jsonpath='{.items[0].spec.containers[0].ports[0].containerPort}{"\n"}'
```

```text
Port:                     http  8000/TCP
TargetPort:               8080/TCP
Endpoints:                10.244.1.99:8080,10.244.1.98:8080
8000
```

## Root cause

The Service listens on port 8000 but forwards to port **8080** of the Pods (`targetPort`), where nothing listens: the
endpoints list `<pod-ip>:8080`. The application is fine; the Service sends traffic to the wrong door.

## Fix

<!-- test: contains=service/python-api configured -->
```bash
kubectl apply -f kubernetes/python-api/service.yaml
```

## Verification

<!-- test: retry=15; contains=:8000; contains="users"; output -->
```bash
kubectl describe service python-api | grep -E 'TargetPort|Endpoints'
curl -s http://bookshop.localhost:8080/api/stats; echo
```

```text
TargetPort:               http/TCP
Endpoints:                10.244.1.98:8000,10.244.1.99:8000
{"users":4,"books":5,"reviews":3,"latest_report":{"id":5,"created_at":"2026-10-04T18:50:15.930844+00:00","users":4,"books":5,"reviews":3,"services_up":6,"services_total":6}}
```

## Lesson learned

- Test hop by hop: inside the Pod (`127.0.0.1`), through the Service name, through the Ingress. The first hop that
  fails is where the problem is.
- `port` is what clients of the Service use; `targetPort` is where the Pods listen. Naming the container port
  (`targetPort: http`, as the lab's manifests do) avoids repeating the number.
- 503 from the ingress controller = no endpoints; 502 = endpoints that do not answer.
