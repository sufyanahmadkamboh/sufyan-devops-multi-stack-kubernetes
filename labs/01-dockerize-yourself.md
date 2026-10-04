# Lab 01 · Dockerize quotes-api yourself

## Task

Write a Dockerfile for [quotes-api/app.py](quotes-api/app.py), build the image `quotes-api:1.0.0`, run it, and prove
that `/health` and `/api/quotes` answer.

## Requirements

1. Base image `python:3.14-slim` (a pinned minor version, not `latest`).
2. The image runs as a **non-root** user.
3. The version is a build argument `APP_VERSION` (default `1.0.0`) that ends up in the environment.
4. The container listens on port 8000 and stops cleanly on `docker stop`.
5. A `.dockerignore` keeps everything except `app.py` out of the build context.

## Hints

- quotes-api has no dependencies: no `pip install` needed. Compare with [python-api's Dockerfile](../applications/python-api/Dockerfile).
- `USER 10001` (a numeric user lets Kubernetes verify "non-root" later).
- Use the exec form: `CMD ["python", "app.py"]`, so Python is process 1 and receives SIGTERM.

## Expected result

`curl http://localhost:18099/health` → `{"status": "ok", "service": "quotes-api", "version": "1.0.0"}`.

## Solution

<details>
<summary>Open the solution</summary>

<!-- test-run: rm -rf labs/work && mkdir -p labs/work -->

<!-- test: contains=Dockerfile -->
```bash
mkdir -p labs/work/quotes-api && cp labs/quotes-api/app.py labs/work/quotes-api/
cat > labs/work/quotes-api/Dockerfile <<'EOF'
FROM python:3.14-slim
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION} PORT=8000 PYTHONUNBUFFERED=1
WORKDIR /app
COPY app.py .
USER 10001
EXPOSE 8000
CMD ["python", "app.py"]
EOF
printf '*\n!app.py\n' > labs/work/quotes-api/.dockerignore
ls -A labs/work/quotes-api
```

<!-- test: timeout=600; contains=quotes-api; output -->
```bash
docker build -q -t quotes-api:1.0.0 labs/work/quotes-api > /dev/null
docker images quotes-api --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'
```

```text
REPOSITORY   TAG       SIZE
quotes-api   2.0.0     189MB
quotes-api   1.0.0     189MB
```

<!-- test: retry=10; contains="status": "ok"; contains=author; output -->
```bash
docker rm -f quotes-lab > /dev/null 2>&1 || true
docker run -d --name quotes-lab -p 18099:8000 quotes-api:1.0.0 > /dev/null
sleep 1
curl -s http://localhost:18099/health; echo
curl -s http://localhost:18099/api/quotes; echo
```

```text
{"status": "ok", "service": "quotes-api", "version": "1.0.0"}
{"quote": "First, solve the problem. Then, write the code.", "author": "John Johnson", "version": "1.0.0"}
```

<!-- test: contains=SIGTERM; output=tail:2 -->
```bash
docker stop quotes-lab > /dev/null
docker logs quotes-lab
docker rm quotes-lab > /dev/null
```

```text
...
quotes-api GET /api/quotes 200
quotes-api: SIGTERM, shutting down
```

</details>

## Explanation

The seven Dockerfiles of the platform look different because their stacks need different build steps, but every one
answers the same questions this tiny file answers: which runtime (`FROM`), which files (`COPY`), which user (`USER`),
which configuration (`ENV`, `ARG`), which port (`EXPOSE`), which process (`CMD`). The `.dockerignore` with `*` and
`!app.py` is an allow-list: nothing enters the image by accident. `docker stop` sends SIGTERM; the app logs it and
exits at once, instead of being killed after 10 seconds.

Next: [Lab 02 · Add it to Compose](02-add-to-compose.md).
