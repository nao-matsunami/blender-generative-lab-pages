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

printf "%s" "$PYTHON_CODE" | pbcopy

open "$BLENDER_APP" || true

osascript <<'APPLESCRIPT'
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

tell application "Blender" to activate
delay 2

tell application "System Events"
  tell process "Blender"
    set frontmost to true
    delay 0.5
    key code 118 using {shift down}
    delay 0.8
    keystroke "v" using {command down}
    delay 0.2
    key code 36
  end tell
end tell
APPLESCRIPT

echo "Watcher start command was pasted into Blender's Python Console."
echo "If macOS asks for Accessibility permission, allow Terminal/iTerm/Codex and run this command again."
