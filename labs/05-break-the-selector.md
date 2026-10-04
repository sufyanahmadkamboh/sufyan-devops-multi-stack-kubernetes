# Lab 05 · Break the Service selector, and fix it

## Task

A colleague "cleaned up the labels" of the quotes-api Service. Reproduce the mistake, find it with kubectl only, and
fix it.

## Requirements

1. Break: patch the Service so its selector is `app: quote-api` (one letter missing).
2. Show the symptom from outside, and find the cause with `kubectl` (not by reading the YAML).
3. Fix it by applying your file from lab 03, and prove it works again.

## Hints

- What does a Service send traffic to? Not Pods directly: its **endpoints**.
- Compare the Service's selector with the Pods' labels: `kubectl get pods --show-labels`.

## Expected result

While broken: the Ingress answers `503` and the Service has no endpoints. After the fix: quotes again.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: contains=service/quotes-api patched -->
```bash
kubectl patch service quotes-api -p '{"spec":{"selector":{"app":"quote-api"}}}'
```

<!-- test: retry=10; contains=503; output -->
```bash
curl -s -w '\nHTTP %{http_code}\n' http://bookshop.localhost:8080/api/quotes
```

```text
no available server

HTTP 503
```

<!-- test: contains=quote-api; output -->
```bash
kubectl get endpointslices -l kubernetes.io/service-name=quotes-api -o custom-columns='NAME:.metadata.name,ENDPOINTS:.endpoints[*].addresses[0]'
kubectl get service quotes-api -o jsonpath='{.spec.selector}'; echo
kubectl get pods -l app=quotes-api --show-labels --no-headers | head -1 | awk '{print $1, $NF}'
```

```text
NAME               ENDPOINTS
quotes-api-cx4np   <none>
{"app":"quote-api"}
quotes-api-5cc5b7c6c5-884rv app=quotes-api,pod-template-hash=5cc5b7c6c5
```

No endpoints, because no Pod has the label `app=quote-api`. The Pods are fine; the Service selects nothing.

<!-- test: retry=15; contains=author; output -->
```bash
kubectl apply -f labs/work/k8s/quotes-api.yaml > /dev/null
curl -s http://bookshop.localhost:8080/api/quotes; echo
```

```text
{"quote": "Programs must be written for people to read.", "author": "Harold Abelson", "version": "1.0.0"}
```

</details>

## Explanation

Labels and selectors are the only link between a Service and its Pods; nothing checks that they match. A selector
that matches nothing is perfectly valid YAML, which is why this is one of the most common Kubernetes mistakes. The
fastest diagnosis is always the same: **empty endpoints → compare selector and labels**
([troubleshooting/04](../troubleshooting/04-service-selector-mismatch.md)).

Next: [Lab 06 · Upgrade and roll back](06-upgrade-and-rollback.md).
