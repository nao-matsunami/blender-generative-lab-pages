# Autonomous Production

This project can grow through small public iterations. A study does not need to
be final before publishing, but it must be understandable and not broken.

## Default Standard

Codex can publish a study when all of these are true:

- The web preview loads without JavaScript syntax errors.
- The object is visible within the first viewport.
- The preview has no obvious debug artifacts: stray white dots, wireframes,
  accidental transparent shells, or texture seams that dominate the object.
- The daily report exists and links back to the preview.
- Blender assets exist when the study is past draft state: PNG preview,
  transparent PNG, GLB, and STL.

## Iteration States

- `draft`: idea is visible; roughness is acceptable.
- `review`: shape direction is clear; artifacts are being cleaned.
- `published`: suitable for the public gallery.
- `polish`: later pass for better render, print checks, MP4, or product pack.

## Working Rule

When the user leaves judgment to Codex, Codex should choose one clear visual
intention, make the page match it, run the quality checks, and publish if the
checks pass. The user can still redirect taste, but should not need to approve
every micro-adjustment.

## Commands

```sh
npm run build
npm run check:quality
npm run ship
```

Use `npm run ship` only after the preview direction is coherent enough to show.
It builds the gallery, checks web previews and generated assets, then publishes
to GitHub Pages.
