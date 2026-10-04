# 04 · Images, tags and registries

> Time: 20 minutes

## Anatomy of an image name

```text
   ghcr.io / sufyanahmadkamboh / bookshop-node-api : 1.0.0 @ sha256:3f2a…
   ───┬───   ────────┬────────   ────────┬────────   ──┬──   ──────┬──────
   registry     namespace          repository        tag       digest
   (where)      (whose)            (what)            (which    (exactly these bytes,
                                                      version)  can never change)
```

| Part | Default when you leave it out | Example in this lab |
|---|---|---|
| registry | `docker.io` (Docker Hub) | `ghcr.io` for the published images; none for local images |
| namespace | `library` (Docker's official images) | `postgres:18.6-alpine` is really `docker.io/library/postgres:18.6-alpine` |
| tag | `latest` | `1.0.0` |
| digest | – | `kindest/node:v1.37.0@sha256:a1ed56cf…` in [kind-config.yaml](../kubernetes/cluster/kind-config.yaml) |

A **tag** is a label that can be moved to another image at any time. A **digest** is the hash of the image content:
the same digest always means the same bytes.

## Why never `latest`

`latest` is just a tag name, with no meaning of "newest". Using it in a deployment causes three classic problems:

| Problem | What happens |
|---|---|
| **Not reproducible** | two nodes pull `node-api:latest` an hour apart and run different code |
| **No visible change** | you push a new `latest`, re-apply the same YAML: nothing changes, because the manifest did not change |
| **No rollback target** | "go back to the previous version": which one was it? `latest` already points somewhere else |

So every image in this lab carries its **version as the tag**, and the version is baked into the image too
(`ARG APP_VERSION=1.0.0`, shown by every service's `/health`):

```text
node-api:1.0.0   python-api:1.0.0   go-status:1.0.0   java-api:1.0.0
frontend:1.0.0   laravel-fpm:1.0.0  laravel-web:1.0.0 report-worker:1.0.0
```

The rolling-update lesson builds `node-api:1.1.0` and changes the Deployment's image from `1.0.0` to `1.1.0`.
Because the tag in the manifest changes, Kubernetes sees a new version and rolls it out; `kubectl rollout undo` goes
back to the Pod template with `1.0.0`. Version tags make updates and rollbacks visible and exact. See
[12](12-scaling-rolling-updates-rollbacks.md).

## How does the image get into the cluster?

Kubernetes never builds images. Each node's container runtime pulls the image named in the Pod spec. It needs a way
to get it:

```text
  docker build ──► image on YOUR computer ──┬── kind load docker-image ──► copied into each kind node (this lab)
                                            ├── docker push ──► Docker Hub   (docker.io/<user>/<name>:<tag>)
                                            ├── docker push ──► GHCR          (ghcr.io/<user>/<name>:<tag>)
                                            └── docker push ──► Amazon ECR    (<account>.dkr.ecr.<region>.amazonaws.com/...)
                                                                    │
                                                    the nodes pull from the registry
```

| Option | When | What you need |
|---|---|---|
| **`kind load docker-image`** | local kind clusters (this lab) | nothing: the image is copied straight into the node containers |
| **Docker Hub** | public images, small projects | an account; `docker login`; private images need an `imagePullSecret` |
| **GHCR** (GitHub Container Registry) | projects on GitHub | the repository's `GITHUB_TOKEN` in CI can push; public packages need no login to pull |
| **ECR** (or ACR, Artifact Registry) | clusters in a cloud | the nodes' cloud identity is allowed to pull |

This lab uses **`kind load`** so you need no account and no internet upload:

```text
kind load docker-image node-api:1.0.0 --name bookshop
```

The published copies use the GHCR naming from [CONTRACT.md](CONTRACT.md):
`ghcr.io/sufyanahmadkamboh/bookshop-<service>:<version>`. Same image, different name: `docker tag` adds a name,
`docker push` uploads it.

## imagePullPolicy

Every Deployment in this lab says:

```yaml
image: node-api:1.0.0
imagePullPolicy: IfNotPresent      # use the image loaded into the cluster (kind load docker-image)
```

| Policy | Behaviour | Default when |
|---|---|---|
| `IfNotPresent` | use the node's copy if there is one, pull only if missing | the tag is not `latest` |
| `Always` | ask the registry every time a container starts (the image is downloaded only if the digest differs) | the tag is `latest` or missing |
| `Never` | only ever use the node's copy | – |

With `kind load` there is no registry that knows `node-api:1.0.0`, so `Always` would fail. That is one of the
troubleshooting labs.

## ErrImagePull and ImagePullBackOff

When a node cannot get the image, the Pod never starts:

```text
NAME                        READY   STATUS             RESTARTS   AGE
node-api-7c9d8b6f5d-x2k4p   0/1     ImagePullBackOff   0          40s
```

- `ErrImagePull`: the last pull attempt failed.
- `ImagePullBackOff`: Kubernetes waits longer and longer between attempts (back-off).

The reason is in the Pod's events, `kubectl describe pod <name>`: a misspelt name or tag ("not found"), a private
image without credentials ("pull access denied" / "unauthorized"), or no network to the registry. The fix is always
in the image reference or in the access to the registry, never in the application.

## Check yourself

<details><summary>What is the full name of <code>postgres:18.6-alpine</code>?</summary>

`docker.io/library/postgres:18.6-alpine`: Docker Hub, the official-images namespace `library`, repository `postgres`,
tag `18.6-alpine`.
</details>

<details><summary>Why does re-applying a Deployment with <code>image: node-api:latest</code> after pushing a new latest often change nothing?</summary>

The manifest did not change, so Kubernetes sees no new Pod template and starts no rollout. Running Pods keep the
image they started with.
</details>

<details><summary>How do images get into the kind cluster of this lab?</summary>

`kind load docker-image <name>:<tag> --name bookshop` copies the image from your local Docker into every kind node.
No registry is involved.
</details>

<details><summary>What would <code>imagePullPolicy: Always</code> do with a kind-loaded image?</summary>

It would try to pull `node-api:1.0.0` from Docker Hub, where it does not exist, and the Pod would end in
`ErrImagePull` / `ImagePullBackOff`.
</details>

<details><summary>Tag or digest: which one guarantees the exact same image every time?</summary>

The digest. A tag can be moved to another image; a digest is the hash of the content.
</details>

Next: [05 · Docker Compose](05-docker-compose.md)
