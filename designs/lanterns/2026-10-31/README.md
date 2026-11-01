# Algorithmic lantern studies — 2026-10-31

Three separate shade studies built and rendered in Blender through the GUI job watcher. All have open bottoms for placing a separate LED assembly and open tops for access and ventilation. The exported STL files contain only the shades, not a lamp base or electrical parts.

**Current direction:** Phase Diagrid below replaces Tidal Pleat as the nonfigurative algorithmic lantern study. Night Orchard remains a separate shadow-picture concept. The earlier warm, curved visual language is not a requirement for future versions.

## Current nonfigurative direction — Phase Diagrid

A twisted eight-facet column with two mathematically generated families of crossing diagonal bands. Their phase and pitch drift with height, creating a graded diamond lattice. The geometry itself carries the design; the openings are not intended to project a recognizable picture. The matte mineral-white body and neutral dark backdrop deliberately leave behind the earlier rose/organ palette.

- Approximate outer dimensions: 141 × 141 × 180 mm.
- Nominal radial wall: 2.8 mm; broad integrated diagonal bands, continuous top and bottom rims, open top and bottom.
- Parameters: `radius`, `solid`, `HEIGHT` in `generate_phase_diagrid.py`; shared mesh resolution and wall thickness in `generate.py`.
- Files: `phase-diagrid.stl`, `phase-diagrid.glb`, `phase-diagrid-preview.png`.
- Geometry check: 104,172 STL triangles, one connected component, every edge incident to two faces, positive signed volume.

## 1. Tidal Pleat

A broad ceramic-like sleeve whose radius changes with height and around the circumference. Ten unequal, slowly twisting tapered openings follow that surface. An uneven top lip makes the silhouette change as it rotates. The intended effect is a warm lantern with repeating but nonuniform bands of light. A removable translucent inner liner could soften the points of light.

- Approximate outer dimensions: 145 × 145 × 167 mm (wavy top); nominal body height 160 mm.
- Nominal wall: 2.8 mm; flat open bottom.
- Parameters: `tidal_radius`, `tidal_solid`, `WALL`, `N`, `M` in `generate.py`.
- Files: `tidal-pleat.stl`, `tidal-pleat.glb`, `tidal-pleat-preview.png`.

## 2. Night Orchard

An opaque shade with one large directional window. A broad trunk, five branches, and attached leaf forms remain as one continuous silhouette within the window. Light from a small source set behind the window projects a tree shadow into the surrounding bright field. The Blender shadow study places a wall 220 mm from the shade; source size, source position and wall distance will change the sharpness and scale in a real room.

- Approximate outer dimensions: 145 × 145 × 168 mm.
- Nominal wall: 2.8 mm; flat open bottom.
- Parameters: `orchard_radius`, `orchard_solid`, `BRANCHES`, `LEAVES` in `generate.py`.
- Files: `night-orchard.stl`, `night-orchard.glb`, `night-orchard-preview.png`, `night-orchard-shadow-study.png`.

## Fabrication status

**Exported design studies.** Both meshes were generated as closed solids; edge incidence, dimensions and normals should be checked again after any parameter change. A slicer check, small test print, stable base, LED holder, cable routing and heat test remain to be done. Use a separate low-heat LED assembly for prototypes; a conventional bulb has not been evaluated for this enclosure. The shadow study is a Blender light simulation, not a measurement from a physical build.

Final export check: Tidal Pleat has 165,732 STL triangles and Night Orchard has 199,204. Each has one connected component, every edge is incident to exactly two faces, and signed volume is positive. This geometric check does not establish printability in a specific slicer or material.
