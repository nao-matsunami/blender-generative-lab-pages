# Blender Generative Lab Pipeline

## Goal

Use Blender as a generative design workstation for objects that can become web previews, rendered motion, and physical 3D prints.

## Daily Flow

1. Pick a form direction.
2. Generate a web preview in `outputs/`.
3. Generate the Blender object with `offline/*.py`.
4. Export STL and GLB.
5. Render a still or turntable.
6. Add a daily report.
7. Publish the lightweight site to GitHub Pages.

## Print Gate

Before calling an object printable:

- Check scale in millimeters.
- Check wall thickness.
- Check manifold/non-manifold issues.
- Check overhangs and support needs.
- Slice a small test first.

## Saleable Packs

Candidate bundle:

- STL
- GLB
- `.blend`
- generation Python
- still render
- turntable MP4
- license text
