# Blender Generative Lab

Algorithmic design studies for Blender, VJ visuals, and 3D printing.

The main series is **Organic Motion Objects**: looping organic 3D forms for web previews, rendered VJ assets, GLB/STL packs, and future `.blend` source products.

This project is separate from the VJ sample sites. It focuses on forms that can become:

- Web previews for GitHub Pages
- Blender renders for MP4 / alpha MOV
- STL / GLB exports for 3D printing and web inspection
- Source packs built from `.blend`, Python scripts, and generated assets

## First Study

`Organic Growth Vessel` is a procedural vessel form designed for both screen-based visual work and 3D print development.

## Second Study

`Voronoi Light Shell` is a perforated shell direction for lampshade tests, wall objects, and rendered turntables.

## Third Study

`Luminous Seed Vessel` is a seed, vessel, and lampshade hybrid for the Organic Motion Objects direction.

## Local Site

```sh
npm run build
python3 -m http.server 4247
```

Open `http://localhost:4247/`.

## Blender Generation

Install Blender on the Mac mini, then run:

```sh
npm run watcher:start
npm run job:all
npm run blender:organic
npm run blender:voronoi
```

Because this Mac currently crashes on Blender CLI/background startup, prefer `watcher:start` + `job:all`. The `blender:*` commands remain for environments where CLI startup works.

Expected outputs:

```txt
exports/stl/organic-growth-vessel.stl
exports/glb/organic-growth-vessel.glb
renders/organic-growth-vessel.png
renders/organic-growth-vessel-preview.png
exports/stl/voronoi-light-shell.stl
exports/glb/voronoi-light-shell.glb
renders/voronoi-light-shell.png
renders/voronoi-light-shell-preview.png
exports/stl/luminous-seed-vessel.stl
exports/glb/luminous-seed-vessel.glb
renders/luminous-seed-vessel.png
renders/luminous-seed-vessel-preview.png
```

Check whether the expected files were created:

```sh
npm run check:assets
```

Use the `*-preview.png` files for visual review. The non-preview PNG files keep a transparent background for compositing, so many image viewers display the transparent area as black.

## Print Notes

Start with a small test print before committing to a large object.

- Use millimeters as the working unit.
- Keep minimum wall thickness above the nozzle/material limit.
- Check manifold status in Blender or the slicer.
- Expect support material for aggressive overhangs.
- Treat the first STL as a design study, not a final manufacturing file.

## Docs

- `docs/mac-mini-setup.md`
- `docs/blender-troubleshooting.md`
- `docs/gui-manual-run.md`
- `docs/gui-job-watcher.md`
- `docs/ai-blender-workflow.md`
- `docs/print-readiness.md`
- `docs/pipeline.md`
