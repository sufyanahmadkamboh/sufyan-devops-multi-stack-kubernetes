// Bookshop report job: plain JavaScript (no framework) on Node.js 24.
// It runs once and exits: collect statistics and the service status, store one row in "reports", print a summary.
"use strict";

const { Client } = require("pg");

const SERVICE = "report-worker";
const VERSION = process.env.APP_VERSION || "dev";
const STATS_URL = process.env.STATS_URL || "http://python-api:8000/api/stats";
const STATUS_URL = process.env.STATUS_URL || "http://go-status:8080/api/status";

const log = (msg) => console.log(`${new Date().toISOString()} ${SERVICE} ${msg}`);
const fail = (msg) => {
  console.error(`${new Date().toISOString()} ${SERVICE} ERROR: ${msg}`);
  process.exit(1);
};

async function getJson(url) {
  let res;
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(5000) });   // fetch is built into Node.js
  } catch (err) {
    throw new Error(`GET ${url} failed: ${err.cause?.code || err.name}: ${err.cause?.message || err.message}`);
  }
  if (!res.ok) throw new Error(`GET ${url} answered HTTP ${res.status}`);
  return res.json();
}

async function main() {
  if (!process.env.DB_PASSWORD) {
    fail("DB_PASSWORD is not set. Set it (Compose: environment, Kubernetes: a Secret) and run again.");
  }
  log(`version ${VERSION} starting: stats from ${STATS_URL}, status from ${STATUS_URL}`);

  const [stats, status] = await Promise.all([getJson(STATS_URL), getJson(STATUS_URL)]);

  const db = new Client({
    host: process.env.DB_HOST || "postgres",
    port: Number(process.env.DB_PORT || 5432),
    database: process.env.DB_NAME || "bookshop",
    user: process.env.DB_USER || "bookshop",
    password: process.env.DB_PASSWORD,
    connectionTimeoutMillis: 5000,
  });
  await db.connect();
  try {
    await db.query(`CREATE TABLE IF NOT EXISTS reports (
      id SERIAL PRIMARY KEY,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      users INT, books INT, reviews INT,
      services_up INT, services_total INT)`);
    const { rows } = await db.query(
      `INSERT INTO reports (users, books, reviews, services_up, services_total)
       VALUES ($1, $2, $3, $4, $5) RETURNING id`,
      [stats.users ?? 0, stats.books ?? 0, stats.reviews ?? 0, status.up ?? 0, status.total ?? 0]);
    log(`report #${rows[0].id} saved: users=${stats.users ?? 0} books=${stats.books ?? 0} ` +
        `reviews=${stats.reviews ?? 0} services up=${status.up ?? 0}/${status.total ?? 0}`);
  } finally {
    await db.end();
  }
}

process.on("SIGTERM", () => fail("SIGTERM received before the report was finished"));

main().then(() => process.exit(0)).catch((err) => fail(err.message));
