#!/usr/bin/env python3
"""Screenshot a URL with a headless Chromium-based browser (Edge or Chrome), for the lesson images.

    python3 tests/screenshot.py <url> <out.png> [width height]

Skips (exit 0, with a message) when no supported browser is installed, so lessons still run in CI.
"""
import os
import shutil
import subprocess
import sys
import tempfile

CANDIDATES = [
    os.environ.get("BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("microsoft-edge") or "",
]

url, out = sys.argv[1], os.path.abspath(sys.argv[2])
w, h = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ("1400", "900")
browser = next((b for b in CANDIDATES if b and os.path.exists(b)), None)
if not browser:
    print("screenshot skipped: no Chromium-based browser found")
    sys.exit(0)
os.makedirs(os.path.dirname(out), exist_ok=True)
with tempfile.TemporaryDirectory() as profile:
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--disable-extensions", "--disable-sync",
                    "--no-first-run", "--hide-scrollbars", f"--user-data-dir={profile}", f"--window-size={w},{h}",
                    "--virtual-time-budget=4000", f"--screenshot={out}", url],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"screenshot: {out}")
