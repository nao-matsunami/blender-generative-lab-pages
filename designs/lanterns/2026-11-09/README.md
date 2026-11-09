# Parallax Oculi Shade — 2026-11-09

Nonfigurative 3D-printable light-object design study. A fivefold low-relief tapered shell is pierced by nine staggered elliptical apertures. The generator is `offline/generate_parallax_oculi_shade.py`.

- Radius (mm): `68 + 13sin(pi*u) - 10u + 7cos(5theta+0.8u) + 7u*cos(theta-0.45)`, `u=z/172`.
- Apertures: three rows at z=48, 88, 128 mm; three holes per row; row phases 0.28, -0.18, 0.38 rad; half-height 23 mm, angular half-width 0.42 rad.
- Final STL envelope: 157.87 × 162.13 × 172.00 mm; nominal radial wall 3.2 mm. Continuous lower band 21 mm and upper band 20 mm. Nine openings separate from open top and bottom; actual minimum web and overhang need slicer inspection.
- First Blender GUI preview had small stepped openings and an overexposed mouth. Increased mesh resolution and aperture size, strengthened fivefold profile, changed camera and material, then rerendered and visually inspected.
- STL has 307,056 triangles; all 460,584 unique edges have two incident triangles. This verifies closed surface incidence, not print success.
- From 2026-11-08 Orbit Terrace Lantern: stepped annular silhouette to tapered fivefold shell; horizontal continuous gaps to isolated elliptical apertures; broad offset piers to continuous punctured skin; sand to blue-grey; higher to lower oblique view.
- Candidate removable rechargeable LED cores are Etevia touch light and rechargeable E26 bulb. Real size, touch/control access, charging, retention, ventilation, thermal behavior, slicer supports, and physical strength remain untested. No fixed mount selected. Design study only, not a finished electrical product or print-ready claim.
