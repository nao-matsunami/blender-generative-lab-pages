# Facet Fan Lantern — 2026-11-05

Nonfigurative algorithmic light-object study made on the actual production date. Generator: [`offline/generate_facet_fan_lantern.py`](../../../offline/generate_facet_fan_lantern.py).

## Rule and dimensions

A nine-face drum follows apothem `66 + 17sin(πu)^1.3` mm, where `u = z/166`. A nine-cycle ridge adds up to 3.2 mm and the center drifts up to 4 mm. Nine vertical blade centers follow `2π(k + 0.06sin(1.8k))/9`, with a maximum 0.07 rad height sway. Their half-widths are `0.17 + 0.025sin(2.1k + 0.4) + 0.025sin(πu)` rad. A continuous crown tilts up to ±8 mm. The blades never cross; upper and lower collars join them.

STL bounds: **169.62 × 171.05 × 174.00 mm**. Nominal wall: **2.8 mm**. Intended minimum blade width: approximately **19 mm**. A **19 mm** continuous lower ring provides a level base. The bottom and top are open; side gaps provide a potential ventilation path. Actual airflow and temperatures are untested.

The removable rechargeable cordless LED is a design hypothesis. The Etevia listing's 70 × 70 × 91 mm body has nominal room through the approximately φ126 mm bottom passage, but physical fit, touch operation, Type-C access, retention, removal for charging and heat require checking. The rechargeable E26 bulb's outside dimensions are unknown. **No mount is fixed.** LED tape and bare boards remain alternatives. The rendered point light is illustrative only.

## Review and limits

The first Blender GUI preview showed an overly dark front and a heavy level crown. I changed the crown height, blade widths, camera, material and front fill; inspected two more renders and changed the camera again. The final Blender PNG shows a skewed faceted crown and readable side gaps, without visible clipping or floating parts.

Compared with 2026-11-04 Eccentric Horizon Lantern, the silhouette changes from a waisted shell to a broad faceted drum, the aperture topology from five horizontal windows to nine continuous vertical gaps, the construction rhythm from a cut skin to separate blades joined by collars, the material from matte blue-gray to satin pewter, and the camera to a higher oblique side view. There is no anatomy, crimson palette, diagonal lattice or shadow picture.

The STL has **144,356 triangles**, one connected component, every edge incident to two faces and positive signed volume. The GLB has one mesh and two materials. This is an **exported design study, not print-ready or a finished electrical product**. Slicer support at the crown, upright blade strength, physical stability, core controls and charging, and electrical/thermal behavior remain untested.
