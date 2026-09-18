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
from datetime import datetime
from pathlib import Path

import bpy


PROJECT_ROOT = Path("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab")
JOBS_DIR = PROJECT_ROOT / "blender-jobs"
STATUS_FILE = JOBS_DIR / "watcher.status.txt"
TIMER_KEY = "__blender_generative_lab_job_watcher_timer__"
os.environ["BLENDER_LAB_ROOT"] = str(PROJECT_ROOT)

JOBS_DIR.mkdir(parents=True, exist_ok=True)


def write_status(message):
    stamp = datetime.now().isoformat(timespec="seconds")
    STATUS_FILE.write_text(f"{stamp} {message}\n", encoding="utf-8")


def poll_jobs():
    pending = sorted(JOBS_DIR.glob("*.job.py"))
    write_status(f"poll pending={len(pending)}")
    for job in pending:
        running = job.with_suffix(".running")
        done = job.with_suffix(".done")
        failed = job.with_suffix(".failed")
        log = job.with_suffix(".log")

        try:
            write_status(f"running job={job.name}")
            job.rename(running)
            log.write_text(f"Running {running.name}\n", encoding="utf-8")
            runpy.run_path(str(running), run_name="__main__")
            log.write_text(log.read_text(encoding="utf-8") + "Done\n", encoding="utf-8")
            running.rename(done)
            write_status(f"done job={done.name}")
        except Exception:
            failed.write_text(traceback.format_exc(), encoding="utf-8")
            write_status(f"failed job={job.name} details={failed.name}")
            try:
                running.rename(job.with_suffix(".failed.py"))
            except Exception:
                pass

    remaining = len(list(JOBS_DIR.glob("*.job.py")))
    write_status(f"ready pending={remaining}")
    return 2.0


namespace = bpy.app.driver_namespace
previous_timer = namespace.get(TIMER_KEY)
if previous_timer is not None and bpy.app.timers.is_registered(previous_timer):
    bpy.app.timers.unregister(previous_timer)

namespace[TIMER_KEY] = poll_jobs
bpy.app.timers.register(poll_jobs, first_interval=2.0, persistent=True)
print(f"Blender Generative Lab watcher restarted: {JOBS_DIR}")

poll_jobs()
