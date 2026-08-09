"""Start a Blender GUI job watcher.

Use this once after opening Blender manually:

1. Open Blender.
2. Scripting > Text > Open this file.
3. Run Script.

Then submit jobs from Terminal:

npm run job:all
"""

import os
import runpy
import traceback
from pathlib import Path

import bpy


PROJECT_ROOT = Path("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab")
JOBS_DIR = PROJECT_ROOT / "blender-jobs"
os.environ["BLENDER_LAB_ROOT"] = str(PROJECT_ROOT)

JOBS_DIR.mkdir(parents=True, exist_ok=True)


def poll_jobs():
    for job in sorted(JOBS_DIR.glob("*.job.py")):
        running = job.with_suffix(".running")
        done = job.with_suffix(".done")
        failed = job.with_suffix(".failed")
        log = job.with_suffix(".log")

        try:
            job.rename(running)
            log.write_text(f"Running {running.name}\n", encoding="utf-8")
            runpy.run_path(str(running), run_name="__main__")
            log.write_text(log.read_text(encoding="utf-8") + "Done\n", encoding="utf-8")
            running.rename(done)
        except Exception:
            failed.write_text(traceback.format_exc(), encoding="utf-8")
            try:
                running.rename(job.with_suffix(".failed.py"))
            except Exception:
                pass

    return 1.0


if not getattr(bpy.types.Scene, "blender_lab_watcher_started", False):
    bpy.types.Scene.blender_lab_watcher_started = True
    bpy.app.timers.register(poll_jobs, persistent=True)
    print(f"Blender Generative Lab watcher started: {JOBS_DIR}")
else:
    print("Blender Generative Lab watcher is already running.")
