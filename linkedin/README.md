# LinkedIn package

| File | Use |
|---|---|
| `post.md` | Post text, written for a beginner audience |
| `carousel/carousel.pdf` | **Recommended:** upload as a *Document* post. LinkedIn shows it as a swipeable carousel |
| `carousel/slide-01.png` … `slide-11.png` | The same slides as images (1080×1350), for a multi-image post |
| `carousel/slides.html` | Source of the slides. Edit it and re-render each slide with a headless browser (`slides.html?s=N`) |
| `carousel/qr-repo.svg`, `qr-portfolio.svg` | The QR codes used on the last slide |
| `project-image.png` | Single overview image (1200×627) |
| `project-summary.md` | Short technical summary |
| `hashtags.txt` | Hashtags |

## The slides (visual first: one picture per idea, short captions)

| # | Visual | Message |
|---|---|---|
| 1 | Seven stack tiles; "the usual way" vs "this lab" | What it is, and the pain |
| 2 | 4 panels: 7 recipes, copied YAML, Compose→K8s guesswork, no failure practice | Why multi-stack deploys go wrong |
| 3 | Seven factories → one standard box → one port and crane | The idea: shipping containers |
| 4 | "Use it when" / "skip it when" panels | Who it is for |
| 5 | A metro map with the 20 levels | How a learner uses it (the roadmap) |
| 6 | Browser → Ingress → six services → PostgreSQL, CronJob and migration Job | Architecture |
| 7 | The contract; lesson.md → mdrun.py → real output; CI jobs | How it works |
| 8 | Image size bars (final vs build stage), 4.5 s start, 22 checks, five real error messages | Measured results (lab) |
| 9 | Number tiles: 7 / 15 / 15 / 12 / 6 / 14, video, PDF, glossary | Study material |
| 10 | Terminal staircase: clone, compose up, kind, Traefik, deploy.sh, verify.sh | Run it yourself |
| 11 | QR codes to the repository and the portfolio, and a question | Links |

## How to post

1. Start a post, choose **Add a document**, and upload `carousel/carousel.pdf`.
2. Give it a title, for example *"Seven stacks, one path: Dockerfile → Compose → Kubernetes"*.
3. Paste the text from `post.md`.
4. Optional: post `project-image.png` as a single image instead, or upload the 11 PNGs as a multi-image post.
5. Reply to deployment questions in the comments with the matching lab in `troubleshooting/`.
