# GUI Job Watcher

Use this when Blender GUI opens but command-line/background startup crashes.

## Start Watcher

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

### Manual Start

1. Open Blender normally.
2. Go to `Scripting`.
3. `Text > Open`.
4. Open:

```txt
/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py
```

5. Press `Run Script`.
6. Leave Blender open.

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
