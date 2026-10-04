# 10 · Configuration changes: ConfigMaps and Secrets in practice

> Level 15 of the [roadmap](../README.md). Time: 15 minutes. The concepts: [docs/07](../docs/07-configmaps-and-secrets.md).

## Step 1 · Change a value, and notice that nothing happens

The UI's "Reviews admin" link comes from `ADMIN_URL` in the ConfigMap. Change it:

<!-- test: contains=configmap/bookshop-config patched -->
```bash
kubectl patch configmap bookshop-config --type merge -p '{"data":{"ADMIN_URL":"http://admin.bookshop.localhost:8080/?from=kubernetes"}}'
```

<!-- test: contains=http://admin.bookshop.localhost:8080"; output -->
```bash
curl -s http://bookshop.localhost:8080/config.js
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080", APP_ENV: "kubernetes" };
```

Still the old value. Environment variables are copied into a container **when it starts**; changing the ConfigMap
later does not change running processes. (ConfigMaps mounted as **files** are updated in the Pod after a short delay,
but the application must re-read them.)

## Step 2 · Roll the Deployment to pick it up

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl rollout restart deployment/frontend
kubectl rollout status deployment/frontend --timeout=240s
```

<!-- test: retry=10; contains=from=kubernetes; output -->
```bash
curl -s http://bookshop.localhost:8080/config.js
```

```text
window.APP_CONFIG = { ADMIN_URL: "http://admin.bookshop.localhost:8080/?from=kubernetes", APP_ENV: "kubernetes" };
```

`rollout restart` replaced the Pods one by one (a rolling update, [14](14-scaling-rolling-updates.md)): no downtime.
Put the original value back the same way:

<!-- test: timeout=300; contains=successfully rolled out -->
```bash
kubectl apply -f kubernetes/config/bookshop-config.yaml
kubectl rollout restart deployment/frontend
kubectl rollout status deployment/frontend --timeout=240s
```

## Step 3 · What a Secret really contains

Use a throwaway example, never a real secret, to see how a Secret is stored:

<!-- test: contains=c3VwZXItc2VjcmV0; contains=super-secret; output -->
```bash
kubectl create secret generic demo-secret --from-literal=PASSWORD=super-secret
kubectl get secret demo-secret -o jsonpath='{.data.PASSWORD}'; echo
kubectl get secret demo-secret -o jsonpath='{.data.PASSWORD}' | base64 -d; echo
kubectl delete secret demo-secret
```

```text
secret/demo-secret created
c3VwZXItc2VjcmV0
super-secret
secret "demo-secret" deleted from bookshop namespace
```

The stored value is **base64**, an encoding anyone can reverse. A Secret is still the right place for passwords:
access to Secrets can be limited separately with RBAC, they stay out of images and Git, they are mounted only into the
Pods that reference them, and clusters can encrypt them at rest. But "it's in a Secret" does not mean "it's encrypted".

The real `db-credentials` Secret is referenced by name; the password itself never appears in any file:

<!-- test: contains=secretKeyRef; output -->
```bash
grep -B1 -A1 'secretKeyRef' kubernetes/node-api/deployment.yaml
```

```text
            - name: DB_PASSWORD                     # the only secret value, from a Secret, never from the ConfigMap
              valueFrom: { secretKeyRef: { name: db-credentials, key: DB_PASSWORD } }
          livenessProbe:                     # "should Kubernetes restart this container?"
```

Next: [11 · Health probes in action](11-health-probes.md).
