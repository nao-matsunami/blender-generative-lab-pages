# GUI Manual Run

Use this route when Blender opens manually but command-line/background execution crashes.

## Run All Studies

1. Open Blender normally.
2. Switch to the `Scripting` workspace.
3. In the Text editor, choose `Text > Open`.
4. Open:

```txt
/Users/nao/Documents/Codex/2026-08-03-xr-glsl-vj/blender-generative-lab/offline/gui_run_all.py
```

5. Press `Run Script`.

Expected outputs:

```txt
exports/stl/organic-growth-vessel.stl
exports/glb/organic-growth-vessel.glb
renders/organic-growth-vessel.png
exports/stl/voronoi-light-shell.stl
exports/glb/voronoi-light-shell.glb
renders/voronoi-light-shell.png
```

Then check from Terminal:

```sh
npm run check:assets
```

If the render is too close or cropped, rerun this same GUI script after pulling the latest project files. The camera targets are set near the generated object's center and should frame the full object.

For repeated work, use `docs/gui-job-watcher.md` instead. It lets Terminal submit jobs while Blender stays open. You can start the watcher with:

```sh
npm run watcher:start
```

## Why This Exists

On the current Mac mini M4 / macOS 26.5 environment, Blender 4.2, 4.5, and 5.2 all crash during command-line/background startup at Metal backend detection. The normal GUI can still open, so this file runs the same project scripts from inside Blender after the UI has already started.

## If It Fails

Open Blender's system console or check the Info panel for the Python error. If the error references mesh/export operators rather than Metal startup, the project script can be fixed. If Blender itself closes, it is still a Blender/Metal crash.
