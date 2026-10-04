# tests · how the lessons are tested

Every command in this repository's lessons is executed automatically. The outputs under the commands are what they
printed in a real run.

## The runner: mdrun.py

`tests/mdrun.py` reads Markdown files and runs their ```bash blocks in order, on your computer, from the repository
root (a `cd` in one block carries over to the next, like in your terminal). An HTML comment right above a block (it
does not show on GitHub) says what to expect:

| Annotation | Meaning |
|---|---|
| `contains=TEXT` / `absent=TEXT` | the output must / must not contain TEXT (can repeat) |
| `fail` | the command is expected to fail (non-zero exit), e.g. when we break something on purpose |
| `retry=N` | repeat up to N times, 2 s apart (for things that become ready over time) |
| `timeout=S` | give up after S seconds (default 600) |
| `output`, `output=head:N`, `output=tail:N` | with `--update`, write the real output into the ```text block below |
| `skip` | never run (interactive commands such as `docker compose up` in the foreground) |
| `<!-- test-run: command -->` | a hidden step that runs but is not shown (setup or cleanup) |

```text
python3 tests/mdrun.py [--update] [--record DIR] [--stop-on-failure] FILE.md [FILE.md ...]
```

`--record DIR` saves every command with its output, exit code and duration (the video's terminals are built from
these). Outputs are sanitised before they are written: your home and repository paths, your user name and anything
that looks like a cloud account ID are masked.

(The runner can also execute blocks inside virtual machines; that feature comes from an earlier course and is not used
here.)

## In CI

[.github/workflows/test.yaml](../.github/workflows/test.yaml) runs the levels separately, on fresh GitHub-hosted
Ubuntu machines:

| Job | What it proves |
|---|---|
| Static checks | every relative link resolves; every Kubernetes manifest is valid (kubeconform); the Compose file is valid |
| App lesson (× 7) | each application builds, runs and behaves as its lesson says, using Docker only |
| Compose lesson | the whole platform works with Docker Compose |
| Kubernetes | a kind cluster with Traefik; all Kubernetes lessons, the troubleshooting labs, the challenges, the capstone and the cleanup, in order |
| Publish (main) | the versioned images are pushed to GitHub Container Registry |

Each job uploads its recordings and a patch with the real outputs as an artifact.

## Helpers

| File | Purpose |
|---|---|
| [check_links.py](check_links.py) | every relative link and `#anchor` in every Markdown file |
| [screenshot.py](screenshot.py) | headless browser screenshots for the lesson images (skipped where no browser exists) |
