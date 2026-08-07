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
blender --background --python offline/generate_organic_growth_vessel.py
blender --background --python offline/generate_voronoi_light_shell.py
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
