#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab"
BLENDER_APP="${BLENDER_APP:-/Applications/Blender.app}"
WATCHER="$PROJECT_ROOT/offline/gui_job_watcher.py"
PYTHON_CODE="exec(open(\"$WATCHER\").read())"

if [ ! -d "$BLENDER_APP" ]; then
  echo "Blender app not found: $BLENDER_APP" >&2
  exit 1
fi

if [ ! -f "$WATCHER" ]; then
  echo "Watcher not found: $WATCHER" >&2
  exit 1
fi

open "$BLENDER_APP" || true

if osascript <<'APPLESCRIPT'
set watcherCommand to "exec(open(\"/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py\").read())"
set the clipboard to watcherCommand

on wait_for_blender()
  repeat 30 times
    tell application "System Events"
      if exists process "Blender" then return true
    end tell
    delay 1
  end repeat
  return false
end wait_for_blender

if wait_for_blender() is false then
  error "Blender process did not appear."
end if

tell application "System Events"
  tell process "Blender"
    set frontmost to true
    delay 1
    key code 118 using {shift down}
    delay 0.8
    keystroke "v" using {command down}
    delay 0.2
    key code 36
  end tell
end tell
APPLESCRIPT
then
  echo "Watcher start command was pasted into Blender's Python Console."
  echo "If macOS asks for Accessibility permission, allow Terminal/iTerm/Codex and run this command again."
else
  osascript -e 'set the clipboard to "exec(open(\"/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py\").read())"' || true
  echo "Could not automate Blender's UI from this shell."
  echo "The watcher command has been copied to the clipboard if clipboard access is available."
  echo "Paste it into Blender's Python Console and press Return:"
  echo
  echo 'exec(open("/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_job_watcher.py").read())'
  exit 2
fi
