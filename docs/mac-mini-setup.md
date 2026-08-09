# Mac Mini Setup

## Install

Install Blender LTS on the Mac mini. Use the LTS build first because this project depends on repeatable Python rendering more than the newest experimental features.

Install ffmpeg if it is not already available:

```sh
brew install ffmpeg
```

## First Run

From this project directory:

```sh
npm run blender:organic
npm run blender:voronoi
npm run check:assets
```

Expected outputs:

```txt
exports/stl/organic-growth-vessel.stl
exports/glb/organic-growth-vessel.glb
renders/organic-growth-vessel.png
exports/stl/voronoi-light-shell.stl
exports/glb/voronoi-light-shell.glb
renders/voronoi-light-shell.png
```

## Manual Render Check

Open Blender normally and inspect:

- object scale
- material look
- wall thickness
- camera framing
- export paths

## Blender Path

The helper scripts look for Blender in this order:

1. `BLENDER_BIN`
2. `blender` on `PATH`
3. `/Applications/Blender.app/Contents/MacOS/Blender`
4. `/Applications/Blender 4.5.app/Contents/MacOS/Blender`

If multiple versions are installed, choose explicitly:

```sh
BLENDER_BIN="/Applications/Blender 4.5.app/Contents/MacOS/Blender" npm run blender:organic
```

If Blender 5.2 crashes during startup on this Mac, install Blender 4.5 LTS side-by-side and use `BLENDER_BIN`.

On Apple Silicon Macs, confirm that the Blender binary is arm64:

```sh
uname -m
file /Applications/Blender.app/Contents/MacOS/Blender
```

If the Mac is `arm64` but Blender is `x86_64`, install the Apple Silicon build instead.

If Blender is arm64 but still crashes during Metal initialization, generate fallback STL studies while Blender is blocked:

```sh
npm run fallback:stl
```

## Video Expansion

After the still/object export works, add a turntable script:

```txt
frame range: 1-480
fps: 30
duration: 16 seconds
camera: orbit or locked front
output: PNG sequence
```

Then encode:

```sh
ffmpeg -framerate 30 -i renders/turntable/frame_%04d.png -c:v libx264 -pix_fmt yuv420p organic-growth-vessel.mp4
ffmpeg -framerate 30 -i renders/turntable/frame_%04d.png -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le organic-growth-vessel-alpha.mov
```
