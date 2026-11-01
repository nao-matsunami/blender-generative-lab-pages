# GUI Job Watcher

Use this when Blender GUI opens but command-line/background startup crashes.

## On-demand lifecycle for Codex — 2026-11-01

Blender makes the user's computer slow when left running. Start Blender **only for a job that needs it**, and close it after the queue, renders, and exports finish. A stale watcher heartbeat while Blender is closed is expected; start the GUI watcher again for the next job.

From Codex desktop, use Computer Use to get or launch the Blender app, focus its main editor, press Shift+F4 for the Python Console, paste the `exec(open(...gui_job_watcher.py).read())` command below, and press Return. Verify a fresh heartbeat with `npm run watcher:status` before submitting jobs. The shell `npm run watcher:start` is a fallback and may fail when macOS denies AppleScript keyboard access. Never use Blender `--background` for this project.

After work, confirm that there are no pending or running jobs and that the expected assets exist. Inspect the current Blender window before quitting. If it contains unsaved work, save that work to an appropriate project file or leave Blender open and request the user's decision; do not discard unsaved user state. Then quit Blender through the GUI and verify it is closed. This lifecycle is part of the daily automation, not a request for the user to keep Blender open.

## Start Watcher

## Current Symptom To Check

If `blender-jobs/` contains old `*.job.py` files and no matching `*.running`, `*.done`, or `*.failed` files are appearing, Blender may be open but the watcher is not running.

As of the 2026-09-15 check, Blender was open, but `gui_job_watcher.py` was not running, and jobs from 2026-09-09 onward were still pending. In that state, public web sketches can continue to appear, but Blender PNG/GLB/STL outputs will not be generated.

### Automatic Paste

From Terminal:

```sh
npm run watcher:start
```

This opens/activates Blender, switches to the Python Console, places this command on the clipboard, pastes it:

```python
exec(open("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py").read())
```

and presses Return.

macOS may ask for Accessibility permission because the script uses System Events to press keys. If it asks, allow Terminal/iTerm/Codex, then run `npm run watcher:start` again.

If UI automation fails, the command is copied to the clipboard. Paste it into Blender's Python Console and press Return.

After it starts, check that jobs are moving:

```sh
find blender-jobs -maxdepth 1 -type f -name '*.job.py' | sort
find blender-jobs -maxdepth 1 -type f -name '*.running' -o -name '*.done' -o -name '*.failed' | sort | tail
cat blender-jobs/watcher.status.txt
```

Or run the concise diagnostic:

```sh
npm run watcher:status
```

If `*.job.py` files are not moving, paste the same `exec(open(...).read())` command again. Every execution now replaces the previous timer, performs one immediate queue drain, and then writes a heartbeat every two seconds. This also repairs the state where Blender retained an old "started" flag after its timer had stopped.

### Manual Start

1. Open Blender normally.
2. Go to `Scripting`.
3. `Text > Open`.
4. Open:

```txt
/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py
```

5. Press `Run Script`.
6. Leave Blender open while jobs are running, then save any unsaved work and close it.

## Submit Jobs From Terminal

```sh
npm run job:organic
npm run job:voronoi
npm run job:all
```

Then check:

```sh
npm run check:assets
```

## Job Files

Jobs are written to:

```txt
blender-jobs/
```

The watcher renames them as it works:

```txt
*.job.py       waiting
*.running     running
*.done        completed
*.failed      error log
*.failed.py   failed job body
```

This is more stable than AppleScript keystrokes because Blender itself runs the Python code through `bpy.app.timers`.

The AppleScript is only used to start the watcher. After that, jobs are file-based and handled inside Blender.
