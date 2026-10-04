"""quotes-api: the service you deploy yourself in the labs. Python standard library only, no dependencies.

GET /            service info        GET /health   liveness (always 200 while the process runs)
GET /api/quotes  a random quote      PORT (default 8000), APP_VERSION (default 1.0.0) from the environment
"""
import json
import os
import random
import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = os.environ.get("APP_VERSION", "1.0.0")
PORT = int(os.environ.get("PORT", "8000"))
QUOTES = [
    {"quote": "Simplicity is prerequisite for reliability.", "author": "Edsger W. Dijkstra"},
    {"quote": "Programs must be written for people to read.", "author": "Harold Abelson"},
    {"quote": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
    {"quote": "Make it work, make it right, make it fast.", "author": "Kent Beck"},
]


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": "quotes-api", "version": VERSION})
        elif self.path == "/":
            self._json(200, {"service": "quotes-api", "version": VERSION, "language": "Python",
                             "runtime": f"CPython {sys.version.split()[0]}", "description": "random quotes"})
        elif self.path.startswith("/api/quotes"):
            body = dict(random.choice(QUOTES), version=VERSION)
            if VERSION != "1.0.0":
                body["served_by"] = os.environ.get("HOSTNAME", "unknown")   # new in 2.0.0: which Pod answered
            self._json(200, body)
        else:
            self._json(404, {"error": "not found", "path": self.path})

    def log_message(self, fmt, *args):  # one line per request, to stdout
        print(f"quotes-api {self.command} {self.path} {args[1] if len(args) > 1 else ''}", flush=True)


server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
signal.signal(signal.SIGTERM, lambda *_: (print("quotes-api: SIGTERM, shutting down", flush=True), sys.exit(0)))
print(f"quotes-api {VERSION} listening on :{PORT}", flush=True)
server.serve_forever()
