#!/usr/bin/env bash
# Capstone verification: checks that the running platform has every capability the course teaches.
#   capstone/verify.sh            exit code 0 = all checks passed
set -uo pipefail

NS=bookshop
BASE=http://bookshop.localhost:8080
ADMIN=http://admin.bookshop.localhost:8080
pass=0; fail=0
check() {  # check "description" command...
  local name=$1; shift
  if out=$("$@" 2>&1); then printf '  PASS  %s\n' "$name"; pass=$((pass + 1))
  else printf '  FAIL  %s\n        %s\n' "$name" "$(echo "$out" | tail -2)"; fail=$((fail + 1)); fi
}
k() { kubectl -n "$NS" "$@"; }

echo "Workloads"
check "6 Deployments, all Available" bash -c "[ \$(kubectl -n $NS get deploy --no-headers | wc -l) -eq 6 ] && kubectl -n $NS wait --for=condition=Available deployment --all --timeout=60s"
check "no Deployment is stuck in the middle of a rollout" bash -c "kubectl -n $NS get deploy -o json | python3 -c \"
import sys, json
bad = [d['metadata']['name'] for d in json.load(sys.stdin)['items']
       if d['status'].get('updatedReplicas', 0) != d['spec']['replicas'] or d['status'].get('unavailableReplicas', 0)]
print(bad); sys.exit(1 if bad else 0)\""
check "PostgreSQL StatefulSet ready (1/1)" bash -c "[ \"\$(kubectl -n $NS get sts postgres -o jsonpath='{.status.readyReplicas}')\" = 1 ]"
check "database volume claim Bound" bash -c "kubectl -n $NS get pvc data-postgres-0 -o jsonpath='{.status.phase}' | grep -qx Bound"
check "migration Job completed" bash -c "kubectl -n $NS get job laravel-migrate -o jsonpath='{.status.succeeded}' | grep -qx 1"
check "report CronJob exists" k get cronjob report-worker
check "laravel-admin Pod runs 2 containers" bash -c "[ \$(kubectl -n $NS get pod -l app=laravel-admin -o jsonpath='{.items[0].spec.containers[*].name}' | wc -w) -eq 2 ]"

echo "Good practice in every Deployment"
check "every container has CPU and memory requests and limits" bash -c "kubectl -n $NS get deploy -o json | python3 -c \"
import sys, json
bad = [c['name'] for d in json.load(sys.stdin)['items'] for c in d['spec']['template']['spec']['containers']
       if not all(c.get('resources', {}).get(a, {}).get(r) for a in ('requests', 'limits') for r in ('cpu', 'memory'))]
print(bad); sys.exit(1 if bad else 0)\""
check "every HTTP container has a liveness probe" bash -c "kubectl -n $NS get deploy -o json | python3 -c \"
import sys, json
bad = [c['name'] for d in json.load(sys.stdin)['items'] for c in d['spec']['template']['spec']['containers'] if 'livenessProbe' not in c]
print(bad); sys.exit(1 if bad else 0)\""
check "every Service-facing container has a readiness probe" bash -c "kubectl -n $NS get deploy -o json | python3 -c \"
import sys, json
bad = [c['name'] for d in json.load(sys.stdin)['items'] for c in d['spec']['template']['spec']['containers']
       if c['name'] != 'laravel-fpm' and 'readinessProbe' not in c]
print(bad); sys.exit(1 if bad else 0)\""
check "java-api has a startupProbe" bash -c "kubectl -n $NS get deploy java-api -o jsonpath='{.spec.template.spec.containers[0].startupProbe.httpGet.path}' | grep -qx /health"
check "no image uses the tag latest (or no tag)" bash -c "! kubectl -n $NS get deploy,cronjob -o jsonpath='{range .items[*]}{..image}{\"\\n\"}{end}' | tr ' ' '\n' | grep -vE ':[0-9]+\.[0-9]+\.[0-9]+$' | grep ."
check "every Pod runs as non-root" bash -c "[ -z \"\$(kubectl -n $NS get deploy -o jsonpath='{range .items[*]}{.spec.template.spec.securityContext.runAsNonRoot}{\"\n\"}{end}' | grep -vx true)\" ]"
check "the database password comes from a Secret, not a ConfigMap" bash -c "! kubectl -n $NS get configmap bookshop-config -o jsonpath='{.data}' | grep -qi password"

echo "Through the Ingress"
check "UI: /" bash -c "curl -sf $BASE/ | grep -q '<title>Bookshop</title>'"
check "Node.js: /api/users" bash -c "curl -sf $BASE/api/users | python3 -c 'import sys,json; sys.exit(0 if len(json.load(sys.stdin))>=3 else 1)'"
check "Java: /api/books" bash -c "curl -sf $BASE/api/books | python3 -c 'import sys,json; sys.exit(0 if len(json.load(sys.stdin))>=5 else 1)'"
check "Python: /api/stats (with a report)" bash -c "curl -sf $BASE/api/stats | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d[\"books\"]>=5 and d[\"reviews\"]>=3 and d[\"latest_report\"] else 1)'"
check "Go: /api/status, every service up" bash -c "curl -sf $BASE/api/status | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[\"up\"], d[\"total\"]); sys.exit(0 if d[\"up\"]==d[\"total\"]>=6 else 1)'"
check "Laravel: admin host" bash -c "curl -sf $ADMIN/ | grep -q 'Reviews'"

echo "Resilience"
check "data survives the loss of the database Pod" bash -c "
  email=capstone-\$RANDOM@example.com
  curl -sf -X POST $BASE/api/users -H 'Content-Type: application/json' -d '{\"name\":\"Capstone Check\",\"email\":\"'\$email'\"}' > /dev/null &&
  kubectl -n $NS delete pod postgres-0 --wait=true > /dev/null &&
  kubectl -n $NS rollout status statefulset/postgres --timeout=180s > /dev/null &&
  for i in \$(seq 1 60); do curl -sf $BASE/api/users | grep -q \"\$email\" && exit 0; sleep 2; done; exit 1"
check "every Deployment Available again afterwards" kubectl -n "$NS" wait --for=condition=Available deployment --all --timeout=180s

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
