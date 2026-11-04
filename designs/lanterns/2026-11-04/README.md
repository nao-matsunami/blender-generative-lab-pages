# Eccentric Horizon Lantern — 2026-11-04

Nonfigurative algorithmic light-object study made on the actual production date. Generator: [`offline/generate_eccentric_horizon_lantern.py`](../../../offline/generate_eccentric_horizon_lantern.py).

## Rule and dimensions

A continuous waisted shell uses radial main term `69 + 22u − 22sin(πu)^1.7` mm, where `u = z/164`. A three-cycle wave adds up to 4 mm at midheight, and a directional drift adds up to 7 mm at the top. Five long horizontal apertures have elliptic ends at z = 37, 63, 89, 115 and 139 mm. Their angular centers follow `−2.2 + 0.85sin(2.2k)` radians, with halfspan `1.12 + 0.16sin(1.9k + 0.3)` radians. The phase beat makes the windows slide around the shell instead of aligning as a grid.

STL bounds: **182.17 × 182.36 × 164.00 mm**. Nominal wall: **2.8 mm**. The designed vertical web between openings is at least approximately **8 mm**, subject to slicer review. A continuous **19 mm** lower ring provides a level base. The open lower and upper mouths and side windows provide access and a possible ventilation path; airflow and temperatures have not been tested.

The intended core is a removable rechargeable cordless consumer LED. The listed Etevia 70 × 70 × 91 mm body has nominal room through the lower opening, but actual protrusions, touch operation, USB-C access, retention, charging removal, light spread and heat remain unmeasured. The rechargeable E26 bulb's outside dimensions are unknown. **No mount or fastening method is fixed.** LED tape and bare boards remain alternatives.

## Review and limits

The first Blender GUI render showed a heavy upper wall and only part of the aperture sequence. I revised the angular phase, opening height, camera, body color and front fill, then rendered again and inspected the final PNG. The five openings read as a staggered horizon rhythm from an oblique view, with no visible clipping or detached parts.

Compared with 2026-11-03 Tessellated Drift Lantern, this changes the tapered nine-face silhouette to a waisted, offset shell with a broad upper mouth; thirty hexagonal cells to five long horizontal openings; a small cell rhythm to broad sliding bands; pale limestone to matte blue-gray mineral; and the camera to the opposite, lower oblique side. It has no anatomy, dark red palette or shadow-picture motif.

The STL has **188,900 triangles**, one connected component, every edge incident to exactly two faces, and positive signed volume. The GLB has one mesh and two materials. This is an **exported design study, not print-ready or a finished electrical product**. Slicer support of the long window edges, physical strength/stability, LED retention and charging access, and electrical/thermal behavior remain untested.
