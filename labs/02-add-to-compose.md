# Lab 02 · Add quotes-api to Compose, and add an environment variable

## Task

Add `quotes-api` to the Compose platform **without editing** [compose/docker-compose.yml](../compose/docker-compose.yml):
use a second Compose file that extends it. Make the Go status board check quotes-api too, by changing its
configuration (an environment variable), not its code.

## Requirements

1. `labs/work/compose.quotes.yml` defines the service `quotes-api` (image `quotes-api:1.0.0`, built from
   `labs/work/quotes-api`), on the `frontend` network, without a published port.
2. In the same file, override `go-status`'s `TARGETS` so it also checks `quotes-api=http://quotes-api:8000/health`.
3. `docker compose -f compose/docker-compose.yml -f labs/work/compose.quotes.yml up -d --wait` starts everything.
4. The status board reports 7 of 7 services up.

## Hints

- Compose merges several `-f` files: later files add services and override keys of existing ones.
- `TARGETS` is a comma-separated list; copy the existing one from the Compose file and append to it.
- Paths in the second file are relative to the **first** file's directory (`compose/`).

## Expected result

`curl -s http://localhost:8081/api/status` lists `quotes-api` with status `up`, and `up` is 7.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test: contains=compose.quotes.yml -->
```bash
cat > labs/work/compose.quotes.yml <<'EOF'
services:
  quotes-api:
    build: { context: ../labs/work/quotes-api }
    image: quotes-api:1.0.0
    networks: [frontend]
  go-status:
    environment:
      TARGETS: >-
        frontend=http://frontend:8080/health,node-api=http://node-api:3000/health,python-api=http://python-api:8000/health,go-status=http://go-status:8080/health,java-api=http://java-api:8080/health,laravel-admin=http://laravel-web:8080/health,quotes-api=http://quotes-api:8000/health
EOF
ls labs/work
```

<!-- test: timeout=900; contains=Healthy -->
```bash
cd compose
[ -f .env ] || printf 'DB_PASSWORD=%s\nAPP_KEY=base64:%s\n' "$(openssl rand -hex 16)" "$(openssl rand -base64 32)" > .env
docker compose -f docker-compose.yml -f ../labs/work/compose.quotes.yml up -d --wait 2>&1 | tail -3
cd ..
```

<!-- test: retry=20; contains=7 of 7 services up; contains=quotes-api; output -->
```bash
curl -s http://localhost:8081/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"{d['up']} of {d['total']} services up\")
for s in d['services']:
    print(f\"  {s['name']:14} {s['status']}\")"
```

```text
7 of 7 services up
  frontend       up
  go-status      up
  java-api       up
  laravel-admin  up
  node-api       up
  python-api     up
  quotes-api     up
```

```text
⚠️ DESTRUCTIVE COMMAND · stops the Compose platform and deletes its database volume.
```

<!-- test: timeout=300 -->
```bash
cd compose
docker compose -f docker-compose.yml -f ../labs/work/compose.quotes.yml down -v > /dev/null 2>&1
cd ..
```

</details>

## Explanation

You changed what the status board checks without rebuilding it: its configuration is an environment variable, set
outside the image. That is the same idea as the ConfigMap in Kubernetes. The second Compose file is how teams add
local extras (a debug tool, a new service) without touching the shared file; Compose merges them in order.

Next: [Lab 03 · Convert it to Kubernetes](03-convert-to-kubernetes.md).
