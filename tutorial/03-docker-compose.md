# 03 · Docker Compose

> Goal: the whole platform runs on your machine with one command, and you understand every block of the Compose
> file. Levels 5–6 of the [roadmap](../README.md#4-the-roadmap). Time: about 60 minutes.

## Before you start

All eight images from chapter 02 exist (`docker images` shows them with tag `1.0.0`). If one is missing, Compose
builds it, which only takes longer.

## The walk

### 1. Read docs/05 first

[docs/05](../docs/05-docker-compose.md) explains services, networks, volumes, the `.env` file and `depends_on`
conditions. Then open [compose/docker-compose.yml](../compose/docker-compose.yml) next to it and find each concept in
the real file.

### 2. Run the Compose lesson

Work through [compose/README.md](../compose/README.md) from Step 1 to Step 9.

Watch for these moments:

- **Step 1:** `report-worker` is missing from `docker compose config --services`. It is in the profile `jobs`, so
  `up` does not start it. A batch job is not a service you keep running.
- **Step 3:** the start order. `up -d --wait` returns only when health checks pass:

  ```text
   Container bookshop-laravel-migrate-1 Exited
   Container bookshop-go-status-1 Healthy
   Container bookshop-frontend-1 Healthy
   Container bookshop-node-api-1 Healthy
   Container bookshop-java-api-1 Healthy
  ```

  `laravel-migrate` **Exited**, and that is correct: it created the `reviews` table and stopped.
- **Step 6, the isolation test:** the frontend container cannot even resolve the database's name.

  ```text
  wget: bad address 'postgres:5432'
  ```

  Not "connection refused": the name does not exist on the `frontend` network. Networks are a security boundary.
- **Step 8, persistence:** the user you added survives `docker compose down` because the database files live in the
  named volume `pgdata`. Only `down -v` deletes them, and the lesson marks it as a destructive command.

### 3. Notice the race that the health checks prevent

Without the health conditions, `depends_on` only waits for a container to **start**, not for the application inside
to be ready. Java needs a few seconds; the first page would show errors in its Books panel. The lesson's table in
Step 3 explains which service waits for which condition. This exact problem returns in Kubernetes, where it is
solved by readiness probes instead.

## Expert commentary

- **`${DB_PASSWORD:?...}`** makes Compose refuse to start without the secret. It is a one-character habit that
  prevents a whole class of "it started with an empty password" incidents.
- **Never print secrets.** The lesson's `cut -d= -f1 .env` shows only the variable names. Screenshots, terminal
  recordings and CI logs leak passwords far more often than attackers steal them.
- **Compose is the right tool** for a developer's machine and for simple single-host setups. The table at the end
  of the lesson lists what it cannot do (several machines, self-healing, rolling updates). That right-hand column is
  the reason for the rest of this course.
- **Interview angle:** "What does `depends_on` guarantee?" Only start order, unless you add a `condition`; and even
  then only at start, not later.

## Checkpoint

- [ ] The Compose lesson passes, and the status board showed `6 of 6 services up`.
- [ ] You can explain why the frontend cannot reach `postgres`, and why that is good.
- [ ] You can explain the difference between `down` and `down -v` without looking.
- [ ] You did the practical challenge at the end of the lesson (a second python-api).

Next: [04 · From Compose to Kubernetes](04-compose-to-kubernetes.md)
