# Secrets

No real Secret is stored in this repository. The lessons create them from generated values:

```text
kubectl -n bookshop create secret generic db-credentials --from-literal=DB_PASSWORD="$(openssl rand -hex 16)"
kubectl -n bookshop create secret generic laravel-app-key --from-literal=APP_KEY="base64:$(openssl rand -base64 32)"
```

[db-credentials.example.yaml](db-credentials.example.yaml) only shows the shape of such a Secret, with a value that is
obviously an example. See [docs/07](../../docs/07-configmaps-and-secrets.md) for what Secrets do and do not protect.
