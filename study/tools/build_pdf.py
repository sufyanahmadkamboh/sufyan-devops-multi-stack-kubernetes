# ruff: noqa: E501  (long lines are embedded CSS/HTML for the printed layout)
"""Compile the 15 concept lessons (docs/), the service contract, the troubleshooting method, the capstone, the
glossary and the interview questions into one PDF: study/study-guide.pdf.

Usage:
    pip install markdown
    python study/tools/build_pdf.py            # uses Chrome/Edge in headless mode to print the PDF

Set BROWSER to the path of a Chromium-based browser if it is not found automatically.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parent
OUT = STUDY / "study-guide.pdf"
REPO_URL = "https://github.com/sufyanahmadkamboh/sufyan-devops-multi-stack-kubernetes"

CHAPTERS = ["study/README.md"] + sorted(p.relative_to(REPO).as_posix() for p in (REPO / "docs").glob("[0-9][0-9]-*.md")) + [
    "docs/CONTRACT.md",
    "troubleshooting/README.md",
    "capstone/README.md",
    "study/glossary.md",
    "study/interview-questions.md",
]

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "Inter", Arial, sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1a1f2b; margin: 0; }
h1 { font-size: 21pt; color: #0f3d6b; border-bottom: 3px solid #1d5fa8; padding-bottom: 6px; margin: 0 0 14px; }
h2 { font-size: 14.5pt; color: #1d5fa8; margin: 20px 0 8px; }
h3 { font-size: 12pt; margin: 14px 0 6px; }
p { margin: 6px 0; }
a { color: #1d5fa8; text-decoration: none; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9pt; background: #eef3fa; padding: 1px 4px; border-radius: 3px; }
pre { background: #0f1724; color: #e6edf6; padding: 10px 12px; border-radius: 6px; overflow: hidden; white-space: pre-wrap;
      word-break: break-word; font-size: 8.6pt; line-height: 1.45; break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.3pt; break-inside: auto; }
th, td { border: 1px solid #d5dde6; padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: #eaf2f8; color: #0f3d6b; }
tr { break-inside: avoid; }
blockquote { border-left: 4px solid #1d5fa8; background: #f4f8fc; margin: 8px 0; padding: 6px 12px; }
img { max-width: 100%; border: 1px solid #d5dde6; border-radius: 6px; }
details { background: #f4f8fc; border: 1px solid #d5dde6; border-radius: 6px; padding: 6px 12px; margin: 8px 0; }
details summary { font-weight: 600; color: #1d5fa8; }
.chapter { break-before: page; }
.cover { height: 260mm; display: flex; flex-direction: column; justify-content: center; padding: 0 10mm;
         background: linear-gradient(160deg, #0c1522 0%, #132235 60%, #1d3a5c 100%); color: #eaf1fa; border-radius: 10px; }
.cover .kicker { color: #9cc3f0; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; font-size: 10pt; }
.cover h1 { color: #fff; border: 0; font-size: 30pt; line-height: 1.15; margin: 10px 0 14px; }
.cover p { color: #c3d1e3; font-size: 12.5pt; }
.cover .who { margin-top: 40px; font-size: 11pt; color: #9cc3f0; }
.toc { break-before: page; }
.toc ul { font-size: 11.5pt; line-height: 2.1; list-style: none; padding-left: 0; }
"""


def find_browser() -> str:
    candidates = [
        os.environ.get("BROWSER", ""),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        shutil.which("microsoft-edge") or "",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("No Chromium-based browser found. Set BROWSER=/path/to/chrome")


def anchor(rel: str) -> str:
    return rel.replace("/", "-").removesuffix(".md")


def chapter_html(rel: str) -> tuple[str, str]:
    path = REPO / rel
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)                      # test annotations
    # Answers are collapsed <details> blocks on GitHub; in print they are open, with their markdown converted
    # explicitly (markdown is not processed inside raw HTML blocks).
    def render_details(m: re.Match) -> str:
        summary, body = m.group(1), m.group(2).strip()
        # the summary line is raw HTML on GitHub too: convert its inline markdown (`code`, **bold**) here
        summary = markdown.markdown(summary).removeprefix("<p>").removesuffix("</p>")
        inner = markdown.markdown(body, extensions=["fenced_code", "tables", "sane_lists"])
        return f"\n<details open><summary>{summary}</summary>{inner}</details>\n"

    text = re.sub(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", render_details, text, flags=re.S)
    text = re.sub(r"^Next: .*$", "", text, flags=re.M)                      # GitHub-only navigation
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "md_in_html", "sane_lists"])
    chapters = set(CHAPTERS)

    def fix(m: re.Match) -> str:                                             # links: in-document or GitHub
        href = m.group(1)
        if href.startswith(("http", "#", "mailto:")):
            return m.group(0)
        base, _, frag = href.partition("#")
        target = (path.parent / base).resolve()
        rel_target = target.relative_to(REPO).as_posix() if target.is_relative_to(REPO) else base
        if rel_target in chapters:
            return f'href="#{anchor(rel_target)}"'
        kind = "tree" if target.is_dir() else "blob"
        return f'href="{REPO_URL}/{kind}/main/{rel_target}' + (f"#{frag}" if frag else "") + '"'

    html = re.sub(r'href="([^"]+)"', fix, html)
    title = re.search(r"^#\s+(.+)$", text, re.M).group(1)
    return title, html


def main() -> None:
    parts, toc = [], []
    for rel in CHAPTERS:
        title, html = chapter_html(rel)
        toc.append(f'<li><a href="#{anchor(rel)}">{title}</a></li>')
        parts.append(f'<section class="chapter" id="{anchor(rel)}">{html}</section>')
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Study guide: Multi-Stack Applications on Kubernetes</title><style>{CSS}</style></head><body>
<div class="cover">
  <div class="kicker">Study guide · from Dockerfile to Docker Compose to Kubernetes</div>
  <h1>Multi-Stack Applications on Kubernetes<br>From Docker Compose to Kubernetes</h1>
  <p>Seven applications in seven stacks (React, Node.js, Python, Go, Java with Spring Boot, PHP with Laravel and plain
     JavaScript), packaged as Docker images, run together with Docker Compose and deployed to Kubernetes. 15 lessons:
     the architecture, Dockerfiles across stacks, images and registries, Compose, the mapping from Compose to
     Kubernetes, ConfigMaps and Secrets, health probes, resources, storage, networking and Ingress, scaling and
     rollbacks, debugging, Jobs and CronJobs, multi-container Pods; plus the service contract, the troubleshooting
     method, the capstone, a glossary and 25 interview questions.</p>
  <p class="who">Sufyan Ahmad · DevOps Engineer<br>{REPO_URL}</p>
</div>
<div class="toc"><h1>Contents</h1><ul>{"".join(toc)}</ul>
<p>Each lesson explains one part of taking an application from source code to Kubernetes: what it is, why it is
needed, how it works in this lab, and where you meet it at work, and ends with "check yourself" questions. The tested
hands-on lessons (seven applications, Docker Compose, fifteen Kubernetes lessons), the twelve troubleshooting labs,
the challenges and the guided tutorial are in the repository.</p></div>
{"".join(parts)}
</body></html>"""
    browser = find_browser()
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "study-guide.html"
        page.write_text(doc, encoding="utf-8")
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--disable-extensions", "--disable-sync", "--no-first-run",
             "--no-pdf-header-footer", f"--user-data-dir={Path(tmp) / 'profile'}", f"--print-to-pdf={OUT}", page.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
