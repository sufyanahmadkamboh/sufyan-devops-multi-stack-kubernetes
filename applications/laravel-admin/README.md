# laravel-admin · Laravel (PHP) with PHP-FPM and nginx

> **Stack:** PHP 8.5 · Laravel 13 · PHP-FPM · nginx 1.30 · PostgreSQL 18 · **Images:** `laravel-fpm:1.0.0` and
> `laravel-web:1.0.0` · **Time:** about 45 minutes. All commands run from the repository root.

## What is it?

| Term | What it is |
|---|---|
| **PHP** | a programming language made for the web. A PHP script runs once per request: the web server hands it the request, it prints the response, and it ends. |
| **Laravel** | the most widely used PHP framework: routing, controllers, Blade templates, a database layer (Eloquent), migrations, validation, CSRF protection. |
| **Composer** | PHP's package manager (like npm for Node.js or pip for Python). `composer.json` lists the dependencies, `composer.lock` pins the exact versions, `composer install` downloads them into `vendor/`. |
| **PHP-FPM** | the FastCGI Process Manager: a pool of PHP worker processes that waits for requests on port **9000**. It speaks **FastCGI**, not HTTP: a browser cannot talk to it directly. |
| **nginx** | a web server. It speaks HTTP on port 8080, answers static files (CSS, images) itself and passes everything else to PHP-FPM over FastCGI. |

### Why two containers?

Node.js, Python, Go and Java programs contain their own HTTP server: one process, one container. A classic PHP
application needs two programs, a web server **and** the PHP interpreter, and the Docker rule is **one main process
per container**:

```text
Browser ──HTTP──► laravel-web (nginx, port 8080) ──FastCGI──► laravel-fpm (PHP-FPM, port 9000) ──SQL──► PostgreSQL
                     static files: answered here               Laravel: routing, controllers, Blade
```

Two containers means each one has one job, its own logs, its own health and its own update cycle (a security fix
for nginx does not need a new PHP image). The price: they must find each other. In Compose by service name, in
Kubernetes as two containers **in the same Pod**, where they talk over `127.0.0.1`.

## What does the application do?

A small review board for the Bookshop:

| Endpoint | What it does |
|---|---|
| `GET /` | an HTML page (Blade template): a form to add a review and the list of all reviews from PostgreSQL |
| `POST /reviews` | validates the form (book, reviewer, rating 1–5, comment) and stores the review; protected by a CSRF token |
| `GET /health` | `{"status":"ok",...}` when PHP and Laravel answer (no database check) |
| `GET /ready` | `{"status":"ready",...}` when the database answers, otherwise HTTP **503** |
| `GET /info` | service, version, language and runtime as JSON |

The table `reviews` is created by a Laravel **migration** and filled with three example reviews by a **seeder**.
Migrations are a separate, one-off step (`php artisan migrate`), never part of starting the web containers.

## How do I run it locally?

With PHP 8.5, the `pdo_pgsql` extension, Composer and a PostgreSQL server installed on your computer:

<!-- test: skip -->
```bash
cd applications/laravel-admin/src
composer install
cp .env.example .env                # then set DB_HOST / DB_PASSWORD in .env
php artisan key:generate            # writes a new APP_KEY into .env
php artisan migrate --seed
php artisan serve                   # http://localhost:8000
```

`.env` is the file Laravel reads when **no real environment variables** are set. In containers we never use a
`.env` file: every value comes from an environment variable, set by Docker, Compose or Kubernetes. That way the
same image runs everywhere, and no password is ever baked into an image. `.env` stays out of Git and out of the
image (see `.dockerignore`).

The rest of this lesson needs only Docker.

## How do I build the Docker image?

Two Dockerfiles, one build context (`applications/laravel-admin`).

### `Dockerfile.fpm`: the application

| Line | Why |
|---|---|
| `FROM composer:2 AS vendor` | stage 1 uses the official Composer image. Composer is a build tool: it must not end up in the final image. |
| `COPY src/composer.json src/composer.lock ./` then `RUN composer install --no-dev --no-scripts --no-autoloader` | dependencies first, in their own layer: rebuilt only when `composer.json`/`composer.lock` change, not on every code change. `--no-dev` leaves out test tools. |
| `COPY src/ ./` then `composer dump-autoload --no-dev --optimize --classmap-authoritative` | the code, then a fast class map for production |
| `FROM php:8.5-fpm-alpine` | stage 2: the runtime. Small (Alpine) and with PHP-FPM preinstalled |
| `apk add libpq ... docker-php-ext-install pdo_pgsql && apk del .build-deps` | the PostgreSQL driver for PHP. The compilers are installed and removed **in the same layer**, so they never take space in the image |
| `COPY --from=vendor --chown=www-data:www-data /app /var/www/html` | only the result of stage 1, owned by the unprivileged user `www-data` |
| `ENV APP_ENV=production APP_DEBUG=false LOG_CHANNEL=stderr SESSION_DRIVER=cookie ...` | settings that are the same in every environment. `LOG_CHANNEL=stderr`: logs go to the container log, not to a file. `SESSION_DRIVER=cookie`: sessions live in an encrypted cookie, so any number of replicas can serve a user. |
| `USER www-data` | PHP-FPM runs without root |
| `RUN php artisan package:discover && route:cache && view:cache` | prepares the package list, routes and compiled templates once, at build time |
| `ENTRYPOINT ["laravel-entrypoint"]`, `CMD ["php-fpm"]` | a small script checks that `APP_KEY` and `DB_PASSWORD` are set, then starts PHP-FPM (or the command you pass, such as `php artisan migrate`) |

**Why not `php artisan config:cache` at build time?** It writes the *current* values of all environment variables
into a cached file. Run in the Dockerfile, it would freeze the build machine's (empty) database settings into the
image, and the variables set at run time would be ignored. Configuration caches belong to a running environment,
not to an image.

### `Dockerfile.web`: nginx

| Line | Why |
|---|---|
| `FROM nginxinc/nginx-unprivileged:1.30-alpine` | the official nginx image variant that runs without root and listens on 8080 |
| `COPY docker/nginx/default.conf.template /etc/nginx/templates/` | at start, the image fills in `${FPM_HOST}` and `${FPM_PORT}` from the environment |
| `COPY src/public /var/www/html/public` | only the public files: CSS and `index.php` (nginx checks that the file exists before passing the request on) |
| `ENV FPM_HOST=127.0.0.1 FPM_PORT=9000` | the default for Kubernetes (same Pod); Compose sets `FPM_HOST=laravel-fpm` |

Build both:

<!-- test: timeout=1800 -->
```bash
docker build -f applications/laravel-admin/Dockerfile.fpm -t laravel-fpm:1.0.0 applications/laravel-admin
docker build -f applications/laravel-admin/Dockerfile.web -t laravel-web:1.0.0 applications/laravel-admin
```

<!-- test: contains=laravel-fpm; contains=laravel-web; output -->
```bash
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep -E 'REPOSITORY|laravel'
```

```text
REPOSITORY               TAG                             SIZE
laravel-fpm              1.0.0                           222MB
laravel-web              1.0.0                           81.5MB
```

## How do I run the container?

A private network and a PostgreSQL container for the test:

<!-- test: contains=laravel-db -->
```bash
docker network create laravel-lab
docker run -d --name laravel-db --network laravel-lab \
  -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only \
  postgres:18.6-alpine
docker ps --filter name=laravel-db --format '{{.Names}} {{.Status}}'
```

<!-- test: retry=30; contains=accepting connections; output -->
```bash
docker exec laravel-db pg_isready -U bookshop -d bookshop
```

```text
/var/run/postgresql:5432 - accepting connections
```

Laravel needs an **application key** (`APP_KEY`): it encrypts cookies and sessions with it. Generate a fresh one and
put all settings into an **env file**, a plain list of `NAME=value` lines that Docker reads with `--env-file`:

<!-- test: contains=APP_KEY; contains=DB_PASSWORD; output -->
```bash
cat > laravel-lab.env <<EOF
APP_KEY=$(docker run --rm --entrypoint php laravel-fpm:1.0.0 artisan key:generate --show)
DB_HOST=laravel-db
DB_PASSWORD=example-only
EOF
sed -E 's/=.*/=…(hidden)/' laravel-lab.env
```

```text
APP_KEY=…(hidden)
DB_HOST=…(hidden)
DB_PASSWORD=…(hidden)
```

(`--entrypoint php` skips the check script, which would refuse to start without the very key we are generating.)
The file holds secrets: it is in `.gitignore` and we delete it at the end.

**Migrate**, as a one-off container that exits when done:

<!-- test: timeout=300; contains=DONE; output -->
```bash
docker run --rm --network laravel-lab --env-file laravel-lab.env laravel-fpm:1.0.0 php artisan migrate --force --seed
```

```text
laravel-admin 1.0.0: starting: php artisan migrate --force --seed

   INFO  Preparing database.  

  Creating migration table ...................................... 19.83ms DONE

   INFO  Running migrations.  

  2026_10_04_000001_create_reviews_table ......................... 7.28ms DONE


   INFO  Seeding database.  
```

Now the two long-running containers. PHP-FPM gets the name `laravel-fpm`, and nginx finds it by that name:

<!-- test: contains=laravel-fpm; contains=laravel-web; output -->
```bash
docker run -d --name laravel-fpm --network laravel-lab --env-file laravel-lab.env laravel-fpm:1.0.0
docker run -d --name laravel-web --network laravel-lab -e FPM_HOST=laravel-fpm -p 8086:8080 laravel-web:1.0.0
docker ps --filter name=laravel- --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
```

```text
ea0b0592949c9ab5b8928436a7f8b0a7100389d668481f6b29988a058c848f28
3475100c397ec0a7bd6c490049aa6f8212953102b79326ecf26b754e382eef14
NAMES         IMAGE                  PORTS
laravel-web   laravel-web:1.0.0      0.0.0.0:8086->8080/tcp, [::]:8086->8080/tcp
laravel-fpm   laravel-fpm:1.0.0      9000/tcp
laravel-db    postgres:18.6-alpine   5432/tcp
```

Only nginx publishes a port. PHP-FPM is reachable only inside the network, which is exactly right: FastCGI is not
meant for the outside world.

## How does Docker Compose run it?

As **three services**: `laravel-fpm`, `laravel-web` (with `FPM_HOST: laravel-fpm`) and a one-off `laravel-migrate`
that runs `php artisan migrate --force --seed` and exits; both web services wait for it to complete. See
[compose/README.md](../../compose/README.md).

## How does Kubernetes run it?

As **one Pod with two containers**, `fpm` and `web`, in one Deployment. Containers in a Pod share the network, so
nginx reaches PHP-FPM on `127.0.0.1:9000`: the image's default. They always run, scale and restart together. The
migration runs as a Kubernetes **Job** (a Pod that runs to completion). See [kubernetes/README.md](../../kubernetes/README.md).

## What Kubernetes resources are required?

| Resource | Why |
|---|---|
| Deployment `laravel-admin` | runs the Pod with the containers `fpm` (laravel-fpm) and `web` (laravel-web) |
| Service `laravel-admin` | a stable name and port (80 → 8080 of the `web` container) |
| Job `laravel-migrate` | `php artisan migrate --force --seed`, once per release |
| ConfigMap | `DB_HOST`, `DB_NAME`, `DB_USER`, `APP_ENV`, … (not secret) |
| Secret | `APP_KEY` and `DB_PASSWORD` |
| Ingress rule | `admin.bookshop.localhost` → Service `laravel-admin` |

## How do I verify it?

Liveness, readiness and the service information:

<!-- test: retry=15; contains="status":"ok"; output -->
```bash
curl -s http://localhost:8086/health; echo
curl -s http://localhost:8086/ready; echo
curl -s http://localhost:8086/info; echo
```

```text
{"status":"ok","service":"laravel-admin","version":"1.0.0"}
{"status":"ready","service":"laravel-admin","version":"1.0.0"}
{"service":"laravel-admin","version":"1.0.0","language":"PHP","runtime":"PHP 8.5.11 (FPM), Laravel 13.34.0","description":"Book reviews: list and add reviews (server-rendered HTML)"}
```

The page lists the three seeded reviews:

<!-- test: contains=3 reviews; output -->
```bash
curl -s http://localhost:8086/ | grep -E '<h2>|<td>' | head -6
```

```text
        <h2>Add a review</h2>
        <h2>3 reviews</h2>
                    <td>Clean Code</td>
                    <td>Lena</td>
                    <td>★★★</td>
                    <td>Good ideas, some examples feel dated.</td>
```

Add a review the way a browser does: first load the page (it sets a session cookie and contains a CSRF token), then
send the form with both:

<!-- test: contains=302; contains=4 reviews; output -->
```bash
JAR=$(mktemp)
TOKEN=$(curl -s -c "$JAR" http://localhost:8086/ | grep -oE 'name="_token" value="[^"]+"' | cut -d'"' -f4)
curl -s -b "$JAR" -c "$JAR" -w '\nPOST /reviews -> HTTP %{http_code}\n' http://localhost:8086/reviews \
  --data-urlencode "_token=$TOKEN" --data-urlencode "book_title=Designing Data-Intensive Applications" \
  --data-urlencode "reviewer=Sam" --data-urlencode "rating=5" --data-urlencode "comment=Great on databases." | tail -1
curl -s -b "$JAR" http://localhost:8086/ | grep -E 'class="ok"|<h2>[0-9]'
rm -f "$JAR"
```

```text
POST /reviews -> HTTP 302
            <p class="ok">Thank you! Your review was saved.</p>
        <h2>4 reviews</h2>
```

HTTP 302 is the redirect back to the list after a successful save. Without the token Laravel refuses the form with
**419** (CSRF protection):

<!-- test: contains=419; output -->
```bash
curl -s -w '\nPOST without token -> HTTP %{http_code}\n' http://localhost:8086/reviews -d 'book_title=x&reviewer=y&rating=3' | tail -1
```

```text
POST without token -> HTTP 419
```

Both containers log every request, to the console:

<!-- test: contains=review stored; contains=POST /reviews; output -->
```bash
docker logs --tail 4 laravel-fpm 2>&1
docker logs --tail 3 laravel-web 2>&1
```

```text
[2026-10-04 18:07:02] production.INFO: review stored {"id":4,"book_title":"Designing Data-Intensive Applications"} 
172.19.0.4 -  04/Oct/2026:18:07:02 +0000 "POST /index.php" 302
172.19.0.4 -  04/Oct/2026:18:07:02 +0000 "GET /index.php" 200
172.19.0.4 -  04/Oct/2026:18:07:02 +0000 "POST /index.php" 419
172.19.0.1 - - [04/Oct/2026:18:07:02 +0000] "POST /reviews HTTP/1.1" 302 342 "-" "curl/8.19.0" "-"
172.19.0.1 - - [04/Oct/2026:18:07:02 +0000] "GET / HTTP/1.1" 200 3031 "-" "curl/8.19.0" "-"
172.19.0.1 - - [04/Oct/2026:18:07:02 +0000] "POST /reviews HTTP/1.1" 419 6611 "-" "curl/8.19.0" "-"
```

The first log shows Laravel's own line (`review stored`) and PHP-FPM's access lines; the second, nginx's.

## How do I troubleshoot it?

### The fpm container exits immediately

<!-- test: fail; contains=missing required; output -->
```bash
docker run --rm --network laravel-lab -e DB_PASSWORD=example-only laravel-fpm:1.0.0
```

```text
laravel-admin: missing required environment variable(s): APP_KEY
laravel-admin: APP_KEY can be generated with: php artisan key:generate --show
```

The entry-point script refuses to start without `APP_KEY`, with the reason in the log. Without that check, PHP-FPM
would start and Laravel would answer every request with `500 Server Error` (`No application encryption key has
been specified`). Fix: generate a key and pass it (Compose: `environment`, Kubernetes: a Secret).

### 502 Bad Gateway

nginx is up, PHP-FPM is not where nginx looks for it. Start a second nginx without `FPM_HOST`: it uses the default
`127.0.0.1`, and in its own container nothing listens on port 9000:

<!-- test: retry=10; contains=502; contains=Connection refused; output -->
```bash
docker run -d --name laravel-web-broken --network laravel-lab -p 8087:8080 laravel-web:1.0.0 > /dev/null
sleep 2
curl -s -w '\nHTTP %{http_code}\n' http://localhost:8087/health | tail -1
docker logs laravel-web-broken 2>&1 | grep -m1 'connect() failed'
```

```text
HTTP 502
2026/10/04 18:07:06 [error] 35#35: *1 connect() failed (111: Connection refused) while connecting to upstream, client: 172.19.0.1, server: _, request: "GET /health HTTP/1.1", upstream: "fastcgi://127.0.0.1:9000", host: "localhost:8087"
```

The nginx log names the upstream it tried (`fastcgi://127.0.0.1:9000`). Fix: `FPM_HOST` = the name of the FPM
container (Compose) or both containers in one Pod (Kubernetes).

<!-- test-run: docker rm -f laravel-web-broken -->

### 500 Server Error after a new deployment

The containers run, `/ready` is green, and the page fails. Point a second FPM at a brand-new, empty database (no
migration run):

<!-- test: retry=10; contains=HTTP 500; contains=relation "reviews" does not exist; output -->
```bash
docker exec laravel-db createdb -U bookshop fresh 2>/dev/null || true
docker run -d --name laravel-fpm-fresh --network laravel-lab --env-file laravel-lab.env -e DB_NAME=fresh laravel-fpm:1.0.0 > /dev/null
docker run -d --name laravel-web-fresh --network laravel-lab -e FPM_HOST=laravel-fpm-fresh -p 8088:8080 laravel-web:1.0.0 > /dev/null
sleep 3
curl -s -w '\nGET / -> HTTP %{http_code}\n' http://localhost:8088/ | tail -1
curl -s http://localhost:8088/ready; echo
docker logs laravel-fpm-fresh 2>&1 | grep -oE 'SQLSTATE\[42P01\][^(]{0,70}' | head -1
```

```text
GET / -> HTTP 500
{"status":"ready","service":"laravel-admin","version":"1.0.0"}
SQLSTATE[42P01]: Undefined table: 7 ERROR:  relation "reviews" does not exist
```

The database answers, so readiness is fine; the **table** is missing, and the log says so. Readiness proves that a
dependency is reachable, not that the application is correct. Fix: run the migration step before (or together with)
every release: the one-off Compose service, the Kubernetes Job.

<!-- test-run: docker rm -f laravel-web-fresh laravel-fpm-fresh -->

### The database is down

<!-- test: contains="status":"not ready"; contains=503; output -->
```bash
docker stop laravel-db > /dev/null
curl -s -w ' HTTP %{http_code}\n' http://localhost:8086/ready
curl -s -w ' HTTP %{http_code}\n' http://localhost:8086/health
docker start laravel-db > /dev/null
```

```text
{"status":"not ready","reason":"database: QueryException","service":"laravel-admin","version":"1.0.0"} HTTP 503
{"status":"ok","service":"laravel-admin","version":"1.0.0"} HTTP 200
```

Readiness says "do not send me traffic" (503), liveness still says "I am alive" (200). That is the design: restarting
the PHP container would not repair the database.

## How do I clean it up?

```text
⚠️ DESTRUCTIVE COMMAND · removes the lab containers (including the database and its data), the network and the env file.
```

<!-- test: contains=laravel-lab -->
```bash
docker rm -f laravel-web laravel-fpm laravel-db
docker network rm laravel-lab
rm -f laravel-lab.env
```

The images stay: Compose and Kubernetes use them next. To remove them as well:

<!-- test: skip -->
```bash
docker rmi laravel-fpm:1.0.0 laravel-web:1.0.0
```

## Practical challenge

### Task

Run a second, independent copy of the review board for a test team, against its own database `bookshop_test`, on
port 8090, without building a new image.

### Requirements

1. A new database `bookshop_test` in the same PostgreSQL container.
2. The table and the three example reviews in it, created the proper way (migration + seeder).
3. A second FPM and a second nginx; the page on <http://localhost:8090/> shows **3 reviews**, while the first copy
   still shows its own reviews.
4. No change to any file in `applications/`.

### Hints

- The database name is configuration: which environment variable does `config/database.php` read?
- The migration is just another `docker run` of the same image.
- Each nginx needs to know which FPM to use.

### Expected result

Two review boards, one image, two databases: `curl -s localhost:8090/ | grep '<h2>3 reviews'` succeeds.

### Solution

<details>
<summary>Try it yourself first. Then open the solution.</summary>

<!-- test-run: docker network create laravel-lab && docker run -d --name laravel-db --network laravel-lab -e POSTGRES_DB=bookshop -e POSTGRES_USER=bookshop -e POSTGRES_PASSWORD=example-only postgres:18.6-alpine && for i in $(seq 30); do docker exec laravel-db pg_isready -U bookshop -q && break; sleep 1; done && printf 'APP_KEY=%s\nDB_HOST=laravel-db\nDB_PASSWORD=example-only\n' "$(docker run --rm --entrypoint php laravel-fpm:1.0.0 artisan key:generate --show)" > laravel-lab.env -->

<!-- test: timeout=300; retry=10; contains=3 reviews; output -->
```bash
docker exec laravel-db createdb -U bookshop bookshop_test
docker run --rm --network laravel-lab --env-file laravel-lab.env -e DB_NAME=bookshop_test laravel-fpm:1.0.0 php artisan migrate --force --seed
docker run -d --name laravel-fpm-test --network laravel-lab --env-file laravel-lab.env -e DB_NAME=bookshop_test laravel-fpm:1.0.0
docker run -d --name laravel-web-test --network laravel-lab -e FPM_HOST=laravel-fpm-test -p 8090:8080 laravel-web:1.0.0
sleep 3
curl -s http://localhost:8090/ | grep '<h2>'
```

```text
laravel-admin 1.0.0: starting: php artisan migrate --force --seed

   INFO  Preparing database.  

  Creating migration table ....................................... 9.20ms DONE

   INFO  Running migrations.  

  2026_10_04_000001_create_reviews_table ......................... 5.87ms DONE


   INFO  Seeding database.  

c68bc33d88322fe492bff261784bce9b2f4fe581f67ab606aa21972bea28d370
d65e935a9b554e68a96e30720e575a37d8f1f14ba7c5dfaaf3c9465c3ae4bd58
        <h2>Add a review</h2>
        <h2>3 reviews</h2>
```

<!-- test-run: docker rm -f laravel-web-test laravel-fpm-test laravel-db && docker network rm laravel-lab && rm -f laravel-lab.env -->

</details>

### Explanation

The image contains the **code**; the environment decides **which data** it works on. `DB_NAME` (the lab's shared
name, mapped to Laravel's `DB_DATABASE`) selects the database, the migration prepares it, and `FPM_HOST` wires each
nginx to its own FPM. This is the same mechanism Kubernetes uses to run one image as `dev`, `test` and `production`:
the same image, different ConfigMaps and Secrets.
