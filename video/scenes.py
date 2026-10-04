"""Multi-Stack Applications on Kubernetes: the video course, 36 chapters.

Every terminal shows real output, recorded while the lessons ran (tests/mdrun.py --record): the applications on
Docker, the platform on Docker Compose and on a kind cluster. Code panels show the real files of the repository.
The chapters are split over six modules; this one collects them and adds the production layer.
"""

from __future__ import annotations

import scenes_1_intro  # noqa: F401  (chapters 1-3)
import scenes_2_apps  # noqa: F401  (chapters 4-15)
import scenes_3_compose  # noqa: F401  (chapters 16-18)
import scenes_4_deploy  # noqa: F401  (chapters 19-24)
import scenes_5_operate  # noqa: F401  (chapters 25-32)
import scenes_6_finish  # noqa: F401  (chapters 33-36)
from production import package
from scenes_common import SCENES

package(SCENES, "From Dockerfile to Docker Compose to Kubernetes",
        ["React", "Node.js", "Python", "Go", "Java", "Laravel", "JavaScript"], {
    "Build, run, and break it on purpose": {2: "error"},
    "334 MB to build, 82 MB to run": {2: "error"},
    "Alive, but not ready": {1: "error"},
    "16 MB, and no shell to attack": {2: "error"},
    "Migrate, serve, and the 502 every PHP developer knows": {2: "error"},
    "docker compose up": {1: "success"},
    "The platform, working": {1: "success"},
    "Prove it from inside the containers": {1: "error"},
    "Image in, Deployment up, Service in front": {3: "success"},
    "Watch the startup probe work": {2: "success"},
    "Migration Job, a 2/2 Pod, and a CronJob": {2: "success"},
    "Take the database away": {0: "error", 2: "success"},
    "A broken liveness probe restarts a healthy app": {1: "error"},
    "Delete the database Pod. Keep the data.": {2: "success"},
    "Through the front door": {1: "success"},
    "A memory limit that is too small": {0: "error", 1: "success"},
    "kubectl rollout undo": {1: "success"},
    "Image problems": {0: "error"},
    "A selector typo and a crash loop": {0: "error", 1: "error"},
    "Configuration, ports, and secrets": {0: "error"},
    "Verified, not assumed": {0: "success"},
    "Found, fixed, verified": {0: "error", 1: "success"},
})

assert len([s for s in SCENES if s["chapter"]]) == 36, [s["chapter"] for s in SCENES if s["chapter"]]
