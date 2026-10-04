// Bookshop users API: Node.js 24 + Express 5. Configuration comes only from environment variables.
"use strict";

const express = require("express");
const { Pool } = require("pg");

const SERVICE = "node-api";
const VERSION = process.env.APP_VERSION || "dev";
const PORT = Number(process.env.PORT || 3000);

const log = (msg) => console.log(`${new Date().toISOString()} ${SERVICE} ${msg}`);

if (!process.env.DB_PASSWORD) {
  console.error(`${new Date().toISOString()} ${SERVICE} ERROR: DB_PASSWORD is not set. ` +
    "Set it (Compose: environment, Kubernetes: a Secret) and start again.");
  process.exit(1);
}

const pool = new Pool({
  host: process.env.DB_HOST || "postgres",
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || "bookshop",
  user: process.env.DB_USER || "bookshop",
  password: process.env.DB_PASSWORD,
  connectionTimeoutMillis: 3000,
});
pool.on("error", (err) => log(`database pool error: ${err.message}`));

const SEED = [
  ["Ada Lovelace", "ada@example.com"],
  ["Grace Hopper", "grace@example.com"],
  ["Linus Torvalds", "linus@example.com"],
];

let schemaReady = false;
async function ensureSchema() {
  if (schemaReady) return;
  await pool.query(`CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now())`);
  for (const [name, email] of SEED) {
    await pool.query("INSERT INTO users (name, email) VALUES ($1, $2) ON CONFLICT (email) DO NOTHING", [name, email]);
  }
  schemaReady = true;
  log("table users ready");
}

const app = express();
app.use(express.json());
app.use((req, res, next) => {
  res.on("finish", () => log(`${req.method} ${req.originalUrl} ${res.statusCode}`));
  next();
});

app.get("/", (req, res) => res.json({
  service: SERVICE, version: VERSION, language: "JavaScript", runtime: `Node.js ${process.versions.node}`,
  description: "Users API of the Bookshop (Express)",
}));

// liveness: the process can serve requests (no database check on purpose)
app.get("/health", (req, res) => res.json({ status: "ok", service: SERVICE, version: VERSION }));

// readiness: the database answers
app.get("/ready", async (req, res) => {
  try {
    await pool.query("SELECT 1");
    await ensureSchema();
    res.json({ status: "ready", service: SERVICE, version: VERSION });
  } catch (err) {
    res.status(503).json({ status: "not ready", service: SERVICE, reason: err.message });
  }
});

app.get("/api/users", async (req, res) => {
  try {
    await ensureSchema();
    const { rows } = await pool.query("SELECT id, name, email, created_at FROM users ORDER BY id");
    res.json(rows);
  } catch (err) {
    log(`GET /api/users failed: ${err.message}`);
    res.status(503).json({ error: "database unavailable", detail: err.message });
  }
});

app.post("/api/users", async (req, res) => {
  const { name, email } = req.body || {};
  if (!name || !email) return res.status(400).json({ error: "name and email are required" });
  try {
    await ensureSchema();
    const { rows } = await pool.query(
      "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id, name, email, created_at", [name, email]);
    res.status(201).json(rows[0]);
  } catch (err) {
    if (err.code === "23505") return res.status(409).json({ error: "email already exists" });
    log(`POST /api/users failed: ${err.message}`);
    res.status(503).json({ error: "database unavailable", detail: err.message });
  }
});

const server = app.listen(PORT, "0.0.0.0", () => {
  log(`version ${VERSION} listening on port ${PORT}`);
  ensureSchema().catch((err) => log(`database not reachable yet: ${err.message}`));
});

function shutdown(signal) {
  log(`${signal} received, shutting down`);
  server.close(() => pool.end().then(() => process.exit(0)));
  setTimeout(() => process.exit(0), 5000).unref();
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
