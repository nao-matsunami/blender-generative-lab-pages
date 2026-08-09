# Blender Troubleshooting

## Current Mac Note

Blender 5.2.0 LTS was detected at:

```txt
/Applications/Blender.app/Contents/MacOS/Blender
```

`--help` works, but Python/background startup currently crashes during Metal GPU initialization with exit code `139`.

The crash happens before the project generator scripts run, so this is not caused by the organic vessel or Voronoi shell scripts.

## Recommended Fix

Install the Apple Silicon / arm64 build of Blender 4.5 LTS side-by-side and point the project to it:

```sh
BLENDER_BIN="/Applications/Blender 4.5.app/Contents/MacOS/Blender" npm run blender:organic
BLENDER_BIN="/Applications/Blender 4.5.app/Contents/MacOS/Blender" npm run blender:voronoi
```

Blender 4.5 LTS is a better production target for this lab until 5.2 startup is stable on this Mac.

## Architecture Mismatch

If this Mac reports `arm64` but `file /Applications/Blender.app/Contents/MacOS/Blender` reports `x86_64`, the Intel build was installed.

Check:

```sh
uname -m
file /Applications/Blender.app/Contents/MacOS/Blender
```

On Apple Silicon, install the Apple Silicon / arm64 Blender build. The Intel build may run through Rosetta for some UI cases, but it is not a good target for this background generation pipeline.

## Minimal Startup Test

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-expr 'import bpy; print(bpy.app.version_string)'
```

If that crashes, generation scripts will also crash.

## Crash Files

Blender writes crash text to a temporary path such as:

```txt
/var/folders/.../T/blender.crash.txt
```

The current observed backtrace points at Metal backend detection:

```txt
blender::gpu::supports_barycentric_whitelist
blender::gpu::MTLBackend::metal_is_supported
GPU_backend_type_selection_detect
```

## What Not To Debug First

Do not spend time tuning STL geometry, modifiers, or render settings until the minimal startup test works.
