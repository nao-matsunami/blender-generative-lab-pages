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

## Fourth Study

`Tidal Coral Helix` is a twisting reef-like column for slow VJ turntables, translucent PNG compositing, and future vase or lamp-object print tests.

## Fifth Study

`Manta Bloom Shell` is a manta-ray and flower-petal inspired shell for slow VJ loops and print-form exploration.

## Sixth Study

`Spore Current Lantern` is a spore-pod and current-carved lantern form for VJ loops and hollow print-form exploration.

## Seventh Study

`Kelp Pulse Torus` is a kelp-vein ring form for slow VJ loops, pendant-like print objects, and hanging part studies.

## Eighth Study

`Visceral Tide Knot` is a grotesque organ-like tube knot for darker VJ loops and continuous printable form studies.

## Ninth Study

`Neural Gut Bloom` is a grotesque nerve-and-gut colony with a swollen core and looping tendrils.

## Tenth Study

`Membrane Maw Cluster` is a red-purple grotesque membrane shell with mouth-like openings.

## Eleventh Study

`Arterial Fold Nest` is a red grotesque membrane study with heavier folds and artery-like dark channels.

## Twelfth Study

`Peristaltic Coil Womb` is a continuous red intestinal coil for darker VJ loops and compact printable forms.

## Thirteenth Study

`Adhesion Gut Wreath` is a self-pressing gut loop with wet grooves and dark inner contact zones.

## Fourteenth Study

`Hepatic Vessel Bloom` shifts the grotesque line from intestine-like loops to a liver-like asymmetric mass with raised vessel striations.

## Fifteenth Study

`Valvular Chamber Bloom` abstracts heart valves, an asymmetric chamber sac, and thick root vessels for the organ-motif series.

## Sixteenth Study

`Alveolar Sac Cluster` abstracts lung alveoli as clustered sacs with dark mouths and bronchial branching.

## Seventeenth Study

`Renal Pelvis Vessel` abstracts a kidney-like hilum, dark renal pelvis, and branching vessel bundle as a wet organ-form study.

## Eighteenth Study

`Gastric Rugae Maw` abstracts a stomach-like pouch, compressed rugae folds, and a dark inner maw without decorative vessel overlays.

## Nineteenth Study

`Pancreatic Membrane Slab` abstracts a flattened pancreatic or splenic mass with fused membrane folds and dark clefts, avoiding thin vessel decoration.

## Twentieth Study

`Adhesive Spleen Fold` abstracts pressed spleen-like lobes with fused membrane seams and dark contact slits, avoiding thin vessel decoration.

## Twenty-first Study

`Inverted Membrane Cavity` abstracts an inward-folding organ membrane with a thick lip and dark inner void. The web preview supports mouse and mobile rotate, zoom, and pan controls.

## Twenty-second Study

`Valve Cusp Maw` abstracts cardiac valve cusps as three overlapping membranes around a dark chamber opening, using a thick annulus instead of thin vessel decoration.

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
exports/stl/tidal-coral-helix.stl
exports/glb/tidal-coral-helix.glb
renders/tidal-coral-helix.png
renders/tidal-coral-helix-preview.png
exports/stl/spore-current-lantern.stl
exports/glb/spore-current-lantern.glb
renders/spore-current-lantern.png
renders/spore-current-lantern-preview.png
exports/stl/kelp-pulse-torus.stl
exports/glb/kelp-pulse-torus.glb
renders/kelp-pulse-torus.png
renders/kelp-pulse-torus-preview.png
exports/stl/visceral-tide-knot.stl
exports/glb/visceral-tide-knot.glb
renders/visceral-tide-knot.png
renders/visceral-tide-knot-preview.png
exports/stl/neural-gut-bloom.stl
exports/glb/neural-gut-bloom.glb
renders/neural-gut-bloom.png
renders/neural-gut-bloom-preview.png
exports/stl/membrane-maw-cluster.stl
exports/glb/membrane-maw-cluster.glb
renders/membrane-maw-cluster.png
renders/membrane-maw-cluster-preview.png
exports/stl/arterial-fold-nest.stl
exports/glb/arterial-fold-nest.glb
renders/arterial-fold-nest.png
renders/arterial-fold-nest-preview.png
exports/stl/peristaltic-coil-womb.stl
exports/glb/peristaltic-coil-womb.glb
renders/peristaltic-coil-womb.png
renders/peristaltic-coil-womb-preview.png
exports/stl/adhesion-gut-wreath.stl
exports/glb/adhesion-gut-wreath.glb
renders/adhesion-gut-wreath.png
renders/adhesion-gut-wreath-preview.png
exports/stl/hepatic-vessel-bloom.stl
exports/glb/hepatic-vessel-bloom.glb
renders/hepatic-vessel-bloom.png
renders/hepatic-vessel-bloom-preview.png
exports/stl/valvular-chamber-bloom.stl
exports/glb/valvular-chamber-bloom.glb
renders/valvular-chamber-bloom.png
renders/valvular-chamber-bloom-preview.png
exports/stl/alveolar-sac-cluster.stl
exports/glb/alveolar-sac-cluster.glb
renders/alveolar-sac-cluster.png
renders/alveolar-sac-cluster-preview.png
exports/stl/renal-pelvis-vessel.stl
exports/glb/renal-pelvis-vessel.glb
renders/renal-pelvis-vessel.png
renders/renal-pelvis-vessel-preview.png
exports/stl/gastric-rugae-maw.stl
exports/glb/gastric-rugae-maw.glb
renders/gastric-rugae-maw.png
renders/gastric-rugae-maw-preview.png
exports/stl/pancreatic-membrane-slab.stl
exports/glb/pancreatic-membrane-slab.glb
renders/pancreatic-membrane-slab.png
renders/pancreatic-membrane-slab-preview.png
exports/stl/adhesive-spleen-fold.stl
exports/glb/adhesive-spleen-fold.glb
renders/adhesive-spleen-fold.png
renders/adhesive-spleen-fold-preview.png
exports/stl/inverted-membrane-cavity.stl
exports/glb/inverted-membrane-cavity.glb
renders/inverted-membrane-cavity.png
renders/inverted-membrane-cavity-preview.png
exports/stl/valve-cusp-maw.stl
exports/glb/valve-cusp-maw.glb
renders/valve-cusp-maw.png
renders/valve-cusp-maw-preview.png
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
- `docs/autonomous-production.md`
