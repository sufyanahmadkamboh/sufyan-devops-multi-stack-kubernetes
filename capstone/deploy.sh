#!/usr/bin/env bash
# Capstone: deploy the complete Bookshop platform from nothing, in the right order, with one command.
#   capstone/deploy.sh            (from the repository root; needs docker, kind, kubectl, helm)
# Idempotent: re-running it on an existing cluster changes nothing that is already correct.
set -euo pipefail

CLUSTER=bookshop
NS=bookshop
IMAGES=(frontend node-api python-api go-status java-api laravel-fpm laravel-web report-worker)

step() { printf '\n==> %s\n' "$*"; }

step "1/8 images: build every application (Docker layer cache makes rebuilds fast)"
( cd compose && { [ -f .env ] || cp .env.example .env; } && docker compose --profile jobs build --quiet )

step "2/8 cluster: kind + Traefik ingress controller"
if ! kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  kind create cluster --config kubernetes/cluster/kind-config.yaml
fi
helm repo add traefik https://traefik.github.io/charts > /dev/null 2>&1 || true
helm repo update traefik > /dev/null
helm upgrade --install traefik traefik/traefik --version 41.6.1 --namespace traefik --create-namespace \
  --values kubernetes/cluster/traefik-values.yaml --wait --timeout 5m > /dev/null
echo "traefik ready"

step "3/8 images into the cluster"
for i in "${IMAGES[@]}"; do kind load docker-image "$i:1.0.0" --name "$CLUSTER" > /dev/null; done
echo "loaded ${#IMAGES[@]} images"

step "4/8 namespace, configuration, secrets (generated once, never written to disk)"
kubectl apply -f kubernetes/namespace.yaml -f kubernetes/config/bookshop-config.yaml
kubectl -n "$NS" get secret db-credentials > /dev/null 2>&1 ||
  kubectl -n "$NS" create secret generic db-credentials --from-literal=DB_PASSWORD="$(openssl rand -hex 16)"
kubectl -n "$NS" get secret laravel-app-key > /dev/null 2>&1 ||
  kubectl -n "$NS" create secret generic laravel-app-key --from-literal=APP_KEY="base64:$(openssl rand -base64 32)"

step "5/8 database"
kubectl apply -f kubernetes/database/postgres.yaml
kubectl -n "$NS" rollout status statefulset/postgres --timeout=300s

step "6/8 schema migrations (Laravel Job), then the applications"
kubectl -n "$NS" delete job laravel-migrate --ignore-not-found > /dev/null
kubectl apply -f kubernetes/laravel-admin/migrate-job.yaml
kubectl -n "$NS" wait --for=condition=complete job/laravel-migrate --timeout=300s
kubectl apply -f kubernetes/node-api/ -f kubernetes/python-api/ -f kubernetes/java-api/ -f kubernetes/go-status/ \
  -f kubernetes/frontend/ -f kubernetes/laravel-admin/deployment.yaml -f kubernetes/laravel-admin/service.yaml \
  -f kubernetes/report-worker/
kubectl -n "$NS" wait --for=condition=Available deployment --all --timeout=300s

step "7/8 entry point"
kubectl apply -f kubernetes/ingress/ingress.yaml

step "8/8 first report"
kubectl -n "$NS" delete job capstone-report --ignore-not-found > /dev/null
kubectl -n "$NS" create job capstone-report --from=cronjob/report-worker
kubectl -n "$NS" wait --for=condition=complete job/capstone-report --timeout=300s

printf '\nBookshop is up:  http://bookshop.localhost:8080   admin: http://admin.bookshop.localhost:8080\n'
printf 'Verify it:       capstone/verify.sh\n'
