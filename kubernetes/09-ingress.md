# 09 · Services, networking and the Ingress

> Level 14 of the [roadmap](../README.md). Time: 20 minutes. The concepts: [docs/11](../docs/11-services-networking-and-ingress.md).

Every application has a Service now, reachable inside the cluster by name. The outside world needs **one** entry
point that sends each request to the right Service. In Compose the frontend's nginx did that for `/api/*`, and each UI
had its own host port. In Kubernetes, an **Ingress** describes the routes and the ingress controller (Traefik,
installed in [00](00-cluster.md)) carries them out.

```text
 http://bookshop.localhost:8080/            ─┐
 http://bookshop.localhost:8080/api/users    │                     ┌─► Service frontend      :8080
 http://bookshop.localhost:8080/api/books    ├─► Traefik ─ rules ──┼─► Service node-api      :3000
 http://bookshop.localhost:8080/api/stats    │   (Ingress)         ├─► Service java-api      :8080
 http://bookshop.localhost:8080/api/status   │                     ├─► Service python-api    :8000
 http://admin.bookshop.localhost:8080/      ─┘                     ├─► Service go-status     :8080
                                                                   └─► Service laravel-admin :8080
```

Path rules (`/api/users`, ...) and a host rule (`admin.bookshop.localhost`) in one object:
[ingress/ingress.yaml](ingress/ingress.yaml). The longest matching path wins, so `/api/users` goes to node-api and
everything else under `/` to the frontend.

## Step 1 · The Services, all together

<!-- test: contains=ClusterIP; contains=laravel-admin; output -->
```bash
kubectl get services
```

```text
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
frontend        ClusterIP   10.96.50.192    <none>        8080/TCP   3m10s
go-status       ClusterIP   10.96.211.41    <none>        8080/TCP   2m44s
java-api        ClusterIP   10.96.195.75    <none>        8080/TCP   2m26s
laravel-admin   ClusterIP   10.96.208.165   <none>        8080/TCP   2m3s
node-api        ClusterIP   10.96.169.17    <none>        3000/TCP   3m21s
postgres        ClusterIP   None            <none>        5432/TCP   5m55s
python-api      ClusterIP   10.96.214.218   <none>        8000/TCP   2m53s
```

Every Service has a stable virtual IP and a DNS name. `postgres` has no IP (`None`): it is the headless Service of
the StatefulSet, and its name resolves directly to the Pod. The endpoints are the Ready Pods behind each name:

<!-- test: contains=node-api; output -->
```bash
kubectl get endpointslices -o custom-columns='SERVICE:.metadata.labels.kubernetes\.io/service-name,ADDRESSES:.endpoints[*].addresses[0]'
```

```text
SERVICE         ADDRESSES
frontend        10.244.1.8,10.244.1.7
go-status       10.244.1.11
java-api        10.244.1.12
laravel-admin   10.244.1.14
node-api        10.244.1.5,10.244.1.6
postgres        10.244.1.4
python-api      10.244.1.9,10.244.1.10
```

## Step 2 · Apply the Ingress

<!-- test: contains=ingress.networking.k8s.io/bookshop created -->
```bash
kubectl apply -f kubernetes/ingress/ingress.yaml
```

<!-- test: contains=bookshop.localhost; output -->
```bash
kubectl get ingress bookshop
kubectl describe ingress bookshop | sed -n '/Rules:/,/Annotations:/p'
```

```text
NAME       CLASS     HOSTS                                         ADDRESS   PORTS   AGE
bookshop   traefik   bookshop.localhost,admin.bookshop.localhost             80      1s
Rules:
  Host                      Path  Backends
  ----                      ----  --------
  bookshop.localhost        
                            /api/users    node-api:3000 (10.244.1.5:3000,10.244.1.6:3000)
                            /api/books    java-api:8080 (10.244.1.12:8080)
                            /api/stats    python-api:8000 (10.244.1.9:8000,10.244.1.10:8000)
                            /api/status   go-status:8080 (10.244.1.11:8080)
                            /             frontend:8080 (10.244.1.8:8080,10.244.1.7:8080)
  admin.bookshop.localhost  
                            /   laravel-admin:8080 (10.244.1.14:8080)
Annotations:                <none>
```

## Step 3 · Through the front door

The same URLs a browser uses:

<!-- test: retry=15; contains=<title>Bookshop</title>; contains=Ada Lovelace; contains=Moby-Dick; output -->
```bash
B=http://bookshop.localhost:8080
curl -s $B/ | grep -o '<title>[^<]*</title>'
curl -s $B/api/users | head -c 90; echo
curl -s $B/api/books | head -c 140; echo
curl -s $B/api/stats; echo
```

```text
<title>Bookshop</title>
[{"id":1,"name":"Ada Lovelace","email":"ada@example.com","created_at":"2026-10-04T18:18:13
[{"id":1,"title":"Pride and Prejudice","author":"Jane Austen","year":1813},{"id":2,"title":"Moby-Dick","author":"Herman Melville","year":185
{"users":3,"books":5,"reviews":3,"latest_report":{"id":2,"created_at":"2026-10-04T18:20:01.436166+00:00","users":3,"books":5,"reviews":3,"services_up":6,"services_total":6}}
```

<!-- test: retry=15; contains=6 of 6 services up; output -->
```bash
curl -s http://bookshop.localhost:8080/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['up']} of {d['total']} services up\")"
curl -s http://admin.bookshop.localhost:8080/ | grep -o '<title>[^<]*</title>'
```

```text
6 of 6 services up
<title>Bookshop · Reviews</title>
```

Open <http://bookshop.localhost:8080> in your browser: the UI shows books (Java), users (Node.js), statistics
(Python), the status board (Go) and links to the reviews admin (Laravel) at <http://admin.bookshop.localhost:8080>.

![The Bookshop UI on Kubernetes](../docs/images/bookshop-ui-kubernetes.png)

<!-- test-run: python3 tests/screenshot.py http://bookshop.localhost:8080/ docs/images/bookshop-ui-kubernetes.png -->

## Step 4 · Which Pod answered?

A Service balances requests across its Ready Pods. node-api has two replicas; ten requests through the Ingress land
on both (each Pod logs every request):

<!-- test: contains=node-api; output -->
```bash
for i in $(seq 1 10); do curl -s http://bookshop.localhost:8080/api/users > /dev/null; done
for p in $(kubectl get pods -l app=node-api -o name); do
  echo "$p: $(kubectl logs $p --since=60s | grep -c 'GET /api/users') requests"
done
```

```text
pod/node-api-6f678b5b5-lffs6: 6 requests
pod/node-api-6f678b5b5-xjpjv: 6 requests
```

Next: [10 · ConfigMaps and Secrets in practice](10-config-and-secrets.md).
