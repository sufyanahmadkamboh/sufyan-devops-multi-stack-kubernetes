# Lab 04 · Scale quotes-api and watch the load spread

## Task

Run quotes-api with 4 replicas and prove that requests through the Ingress are answered by different Pods.

## Requirements

1. 4 Ready Pods, without editing the YAML file.
2. Send 20 requests through `http://bookshop.localhost:8080/api/quotes`.
3. Count how many requests each Pod handled, from the Pods' own logs.

## Hints

- `kubectl scale`. Then `kubectl rollout status` waits for the new Pods.
- Every request is one log line containing `GET /api/quotes`; `kubectl logs <pod>` per Pod, `grep -c` to count.

## Expected result

Four Pods, each with a share of the 20 requests (the exact split varies).

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl scale deployment quotes-api --replicas=4
kubectl rollout status deployment/quotes-api --timeout=240s
```

<!-- test: contains=quotes-api; output -->
```bash
for i in $(seq 1 20); do curl -s http://bookshop.localhost:8080/api/quotes > /dev/null; done
for p in $(kubectl get pods -l app=quotes-api -o name); do
  echo "$p: $(kubectl logs $p | grep -c 'GET /api/quotes') requests"
done
```

```text
pod/quotes-api-5cc5b7c6c5-884rv: 3 requests
pod/quotes-api-5cc5b7c6c5-f625h: 6 requests
pod/quotes-api-5cc5b7c6c5-st7q6: 6 requests
pod/quotes-api-5cc5b7c6c5-v99n5: 6 requests
```

</details>

## Explanation

Scaling is a single number in the Deployment; the Service (and Traefik in front of it) spread requests across all
Ready Pods. Note what `kubectl scale` did **not** do: it did not change your YAML file. The next `kubectl apply` of
that file sets `replicas: 2` again. In real projects, change the file (or use an autoscaler), so Git stays the truth.

Next: [Lab 05 · Break the selector](05-break-the-selector.md).
