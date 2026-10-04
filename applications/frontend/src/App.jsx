import { useState } from "react";
import { useApi } from "./useApi.js";

// Runtime configuration from /config.js (written by the container at start, not baked into the bundle).
const config = window.APP_CONFIG || {};

function Panel({ title, stack, state, children }) {
  return (
    <section className="panel">
      <h2>
        {title} <span className="stack">{stack}</span>
      </h2>
      {state.loading && <p className="muted">Loading…</p>}
      {state.error && <p className="error">{state.error}</p>}
      {state.data && children(state.data)}
    </section>
  );
}

function Books() {
  const state = useApi("/api/books", "java-api");
  return (
    <Panel title="Books" stack="Java · Spring Boot" state={state}>
      {(books) => (
        <ul>
          {books.map((b) => (
            <li key={b.id}>
              <strong>{b.title}</strong> <span className="muted">by {b.author}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

function Users() {
  const state = useApi("/api/users", "node-api");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  async function add(event) {
    event.preventDefault();
    const res = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email }),
    });
    setMessage(res.ok ? `Added ${name}` : `node-api answered HTTP ${res.status}`);
    if (res.ok) {
      setName("");
      setEmail("");
      state.reload();
    }
  }

  return (
    <Panel title="Users" stack="Node.js · Express" state={state}>
      {(users) => (
        <>
          <ul>
            {users.map((u) => (
              <li key={u.id}>
                {u.name} <span className="muted">{u.email}</span>
              </li>
            ))}
          </ul>
          <form onSubmit={add}>
            <input placeholder="name" value={name} onChange={(e) => setName(e.target.value)} required />
            <input placeholder="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <button>Add user</button>
          </form>
          {message && <p className="muted">{message}</p>}
        </>
      )}
    </Panel>
  );
}

function Stats() {
  const state = useApi("/api/stats", "python-api");
  return (
    <Panel title="Statistics" stack="Python · FastAPI" state={state}>
      {(s) => (
        <>
          <div className="tiles">
            <div>
              <b>{s.users}</b>users
            </div>
            <div>
              <b>{s.books}</b>books
            </div>
            <div>
              <b>{s.reviews}</b>reviews
            </div>
          </div>
          <p className="muted">
            {s.latest_report
              ? `Latest report (report-worker): ${s.latest_report.created_at}`
              : "No report yet: run the report-worker job."}
          </p>
        </>
      )}
    </Panel>
  );
}

function Status() {
  const state = useApi("/api/status", "go-status");
  return (
    <Panel title="Service status" stack="Go" state={state}>
      {(st) => (
        <>
          <ul className="status">
            {st.services.map((s) => (
              <li key={s.name}>
                <span className={`dot ${s.status === "up" ? "up" : "down"}`} />
                {s.name} <span className="muted">{s.status === "up" ? `${s.latency_ms} ms` : s.status}</span>
              </li>
            ))}
          </ul>
          <p className="muted">
            {st.up} of {st.total} services up
          </p>
        </>
      )}
    </Panel>
  );
}

export default function App() {
  return (
    <main>
      <header>
        <h1>📚 Bookshop</h1>
        <p>One page, five backends, six technology stacks, one platform.</p>
        {config.ADMIN_URL && (
          <a className="admin" href={config.ADMIN_URL}>
            Reviews admin (Laravel) →
          </a>
        )}
      </header>
      <div className="grid">
        <Books />
        <Users />
        <Stats />
        <Status />
      </div>
      <footer>
        frontend {__APP_VERSION__} · React · environment: {config.APP_ENV || "unknown"}
      </footer>
    </main>
  );
}
