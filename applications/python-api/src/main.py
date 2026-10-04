"""python-api: statistics for the Bookshop (FastAPI).

GET /api/stats counts users, books and reviews and returns the latest report. It only reads; a table that does not
exist yet (its service has not started) counts as 0.
"""

from __future__ import annotations

import logging
import os
import sys

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

SERVICE = "python-api"
VERSION = os.environ.get("APP_VERSION", "1.0.0")

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s python-api %(message)s")
log = logging.getLogger(SERVICE)

DB_PASSWORD = os.environ.get("DB_PASSWORD")
if not DB_PASSWORD:
    print("python-api: FATAL: the environment variable DB_PASSWORD is not set (the database password is required)",
          file=sys.stderr, flush=True)
    sys.exit(1)

DSN = {
    "host": os.environ.get("DB_HOST", "postgres"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "bookshop"),
    "user": os.environ.get("DB_USER", "bookshop"),
    "password": DB_PASSWORD,
    "connect_timeout": 3,
}

app = FastAPI(title="python-api", version=VERSION)


def connect() -> psycopg.Connection:
    return psycopg.connect(**DSN, autocommit=True)


def count(conn: psycopg.Connection, table: str) -> int:
    exists = conn.execute("SELECT to_regclass(%s)", (f"public.{table}",)).fetchone()[0]
    if exists is None:
        return 0
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # table name comes from a fixed list


@app.middleware("http")
async def access_log(request, call_next):
    response = await call_next(request)
    log.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/")
def root():
    return {"service": SERVICE, "version": VERSION, "language": "Python",
            "runtime": f"CPython {sys.version.split()[0]}",
            "description": "Statistics for the Bookshop: counts of users, books, reviews and the latest report"}


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE, "version": VERSION}


@app.get("/ready")
def ready():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready", "service": SERVICE, "version": VERSION}
    except psycopg.Error as e:
        reason = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
        return JSONResponse(status_code=503, content={"status": "not ready", "service": SERVICE, "reason": reason})


@app.get("/api/stats")
def stats():
    try:
        with connect() as conn:
            result = {"users": count(conn, "users"), "books": count(conn, "books"), "reviews": count(conn, "reviews"),
                      "latest_report": None}
            if conn.execute("SELECT to_regclass('public.reports')").fetchone()[0] is not None:
                cur = conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                if row is not None:
                    cols = [d.name for d in cur.description]
                    result["latest_report"] = {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                                               for k, v in zip(cols, row)}
            return result
    except psycopg.Error as e:
        log.error("database error: %s", str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__)
        return JSONResponse(status_code=503, content={"error": "database unavailable"})
