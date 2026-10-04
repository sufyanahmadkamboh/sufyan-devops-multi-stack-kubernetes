"""Shared helpers for the scene scripts (scenes_1_*.py ... scenes_6_*.py, collected by scenes.py)."""

from __future__ import annotations

from pathlib import Path

SCENES: list[dict] = []
REPO = Path(__file__).resolve().parent.parent


def S(say: str, hl: tuple[int, int] | None = None, tts: str | None = None, zoom: float = 1) -> dict:
    """One narration step. zoom > 1 moves the camera into the terminal, centred on the lines this step reveals."""
    return {"say": say, "hl": hl, "tts": tts, "zoom": zoom}


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


def src(path: str) -> str:
    """A real file from the repository, for code panels."""
    return (REPO / path).read_text(encoding="utf-8")


def lines(text: str, first: str, last: str) -> tuple[int, int]:
    """1-based line range from the first line containing `first` to the next line containing `last`."""
    ls = text.splitlines()
    a = next(i for i, x in enumerate(ls, 1) if first in x)
    return a, next(i for i, x in enumerate(ls, 1) if i >= a and last in x)


APP = {n: f"applications/{n}/README.md" for n in
       ["frontend", "node-api", "python-api", "go-status", "java-api", "laravel-admin", "report-worker"]}
COMPOSE = "compose/README.md"
K = {n: f"kubernetes/{n}.md" for n in [
    "00-cluster", "01-foundation", "02-node-api", "03-frontend", "04-python-api", "05-go-status", "06-java-api",
    "07-laravel-admin", "08-report-worker", "09-ingress", "10-config-and-secrets", "11-health-probes", "12-storage",
    "13-resources", "14-scaling-rolling-updates", "cleanup"]}
TS = "troubleshooting/{:02d}-{}.md"
CAP = "capstone/README.md"


def excerpt(path: str, first: str, last: str) -> str:
    """The lines of a real file from the line containing `first` to the next line containing `last` (inclusive)."""
    text = src(path).splitlines()
    a = next(i for i, x in enumerate(text) if first in x)
    b = next(i for i, x in enumerate(text) if i >= a and last in x)
    return "\n".join(text[a:b + 1])


def bare(path: str) -> str:
    """A real file without full-line comments and blank lines (Dockerfiles and YAML on one screen)."""
    return "\n".join(x for x in src(path).splitlines() if x.strip() and not x.lstrip().startswith("#"))
