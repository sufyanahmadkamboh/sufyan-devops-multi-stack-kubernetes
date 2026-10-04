# 04 · Service selector mismatch

> Time: 10 minutes. Uses the platform from the [Kubernetes lessons](../kubernetes/README.md). The lab restores
> everything at the end.

## Break it

A "small cleanup" of the node-api Service: the selector gets a typo.

<!-- test: contains=service/node-api patched -->
```bash
kubectl patch service node-api -p '{"spec":{"selector":{"app":"node-apii"}}}'
```

## Problem

The users panel is empty and `/api/users` fails, although every node-api Pod is healthy.

## Symptoms

<!-- test: retry=15; contains=503; output -->
```bash
curl -s -w '\nHTTP %{http_code}\n' http://bookshop.localhost:8080/api/users
```

```text
no available server

HTTP 503
```

<!-- test: contains=Running; output -->
```bash
kubectl get pods -l app=node-api
```

```text
NAME                        READY   STATUS    RESTARTS   AGE
node-api-67dfd9488b-hpbpg   1/1     Running   0          2m17s
node-api-67dfd9488b-jqd2m   1/1     Running   0          2m16s
```

`Running`, `1/1`, no restarts. The Pods are fine; the problem is between the Service and the Pods.

## Investigation

A Service sends traffic to its **endpoints**: the Ready Pods whose labels match its selector. No endpoints → nowhere
to send traffic. Compare the selector with the Pods' labels.

## Commands

<!-- test: contains=node-api; output -->
```bash
kubectl get endpointslices -l kubernetes.io/service-name=node-api -o custom-columns='SERVICE:.metadata.labels.kubernetes\.io/service-name,ENDPOINTS:.endpoints[*].addresses[0]'
kubectl describe service node-api | grep -E 'Selector|Endpoints'
```

```text
SERVICE    ENDPOINTS
node-api   <none>
Selector:                 app=node-apii
Endpoints:                
```

<!-- test: contains=app=node-api; output -->
```bash
kubectl get pods -l app=node-api --show-labels
kubectl get pods -l app=node-apii 2>&1
```

```text
NAME                        READY   STATUS    RESTARTS   AGE     LABELS
node-api-67dfd9488b-hpbpg   1/1     Running   0          2m18s   app.kubernetes.io/part-of=bookshop,app=node-api,pod-template-hash=67dfd9488b
node-api-67dfd9488b-jqd2m   1/1     Running   0          2m17s   app.kubernetes.io/part-of=bookshop,app=node-api,pod-template-hash=67dfd9488b
No resources found in bookshop namespace.
```

## Root cause

The Service selects `app=node-apii`; the Pods are labelled `app=node-api`. No Pod matches, so the Service has no
endpoints, and Traefik has no server to send `/api/users` to ("no available server", HTTP 503).

## Fix

<!-- test: contains=service/node-api configured -->
```bash
kubectl apply -f kubernetes/node-api/service.yaml
```

## Verification

<!-- test: retry=15; contains=Ada Lovelace; output -->
```bash
kubectl describe service node-api | grep -E 'Selector|Endpoints'
curl -s http://bookshop.localhost:8080/api/users | head -c 90; echo
```

```text
Selector:                 app=node-api
Endpoints:                10.244.1.92:3000,10.244.1.93:3000
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T18:18:13
```

## Lesson learned

- Healthy Pods + failing Service → `kubectl get endpoints` / `endpointslices` first. Empty = selector mismatch (or no
  Ready Pod).
- The Service selector, the Deployment selector and the Pod template labels must agree.
- Labels are the only link between a Service and its Pods: there is no other "connection" to check.
