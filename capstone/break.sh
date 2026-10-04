#!/usr/bin/env bash
# Capstone scenario "Monday morning": three changes were made to the running platform over the weekend.
# Run it, then find and fix every problem until capstone/verify.sh passes. Don't read this file first.
set -euo pipefail
NS=bookshop
kubectl -n "$NS" patch service python-api -p '{"spec":{"selector":{"app":"python-apii"}}}' > /dev/null
kubectl -n "$NS" set image deployment/go-status go-status=go-status:1.0.1 > /dev/null
kubectl -n "$NS" patch configmap bookshop-config --type merge -p '{"data":{"DB_NAME":"bookshp"}}' > /dev/null
kubectl -n "$NS" rollout restart deployment/java-api > /dev/null
echo "The weekend changes are in. Users report problems. Good luck."
