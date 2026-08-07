# Blender Generative Lab

Algorithmic design studies for Blender, VJ visuals, and 3D printing.

This project is separate from the VJ sample sites. It focuses on forms that can become:

- Web previews for GitHub Pages
- Blender renders for MP4 / alpha MOV
- STL / GLB exports for 3D printing and web inspection
- Source packs built from `.blend`, Python scripts, and generated assets

## First Study

`Organic Growth Vessel` is a procedural vessel form designed for both screen-based visual work and 3D print development.

## Local Site

```sh
npm run build
python3 -m http.server 4247
```

Open `http://localhost:4247/`.

## Blender Generation

Install Blender on the Mac mini, then run:

```sh
blender --background --python offline/generate_organic_growth_vessel.py
```

Expected outputs:

```txt
exports/stl/organic-growth-vessel.stl
exports/glb/organic-growth-vessel.glb
renders/organic-growth-vessel.png
```

## Print Notes

Start with a small test print before committing to a large object.

- Use millimeters as the working unit.
- Keep minimum wall thickness above the nozzle/material limit.
- Check manifold status in Blender or the slicer.
- Expect support material for aggressive overhangs.
- Treat the first STL as a design study, not a final manufacturing file.
