# Tessellated Drift Lantern — 2026-11-03

Nonfigurative algorithmic light-object study made on 2026-11-03. Generator: [`offline/generate_tessellated_drift_lantern.py`](../../../offline/generate_tessellated_drift_lantern.py).

## Rule and dimensions

A nine-face shell tapers from 78 to 61 mm apothem over 158 mm height, with a 2 mm vertical swell and a 4 mm directional drift. Three circumferential rows of ten hexagonal openings sit near 40, 79 and 118 mm. The middle row is phase-shifted by 0.25 cell; all rows gain another 0.065 cell of offset per level. Each opening's hex size is `12.5 + 1.1 sin(0.9 column + 1.4 row)` mm. These values create the stagger and unequal aperture rhythm.

STL exterior bounds: **161.01 × 163.30 × 158.00 mm**. Nominal wall thickness: **2.8 mm**. The estimated minimum inter-cell web in the unwrapped design is **8.19 mm**; it is an analytical estimate, not a slicer measurement. A continuous **19 mm** lower ring provides a level footprint. The bottom opening is at least approximately **150 mm** across in the parametric geometry. The open top and cellular sides provide ventilation paths, pending thermal assessment.

The intended light source is a removable rechargeable cordless consumer LED core. The Etevia listing's 70 × 70 × 91 mm body has ample nominal clearance through the lower opening. Actual controls, Type-C port, retention, charging access, light distribution, ventilation and operating temperature remain to be measured. The rechargeable E26 bulb's outer dimensions remain unconfirmed. **No mount has been fixed or fabricated.**

## Review and limits

The initial Blender GUI preview showed the cells but a dark upper face and a near-frontal view. I lowered and rotated the camera, raised the front fill and warmed the limestone material, then rerendered. An estimated 4.67 mm web in that revision prompted a smaller cell size; the final GUI PNG was inspected after the third render. The final silhouette is fully framed, with visible cell depth and no detached parts.

Compared with 2026-11-02 Splayed Fold Beacon, this changes the upward splayed shell to a broad-based taper; seven long portals to thirty enclosed hex cells; ruled creases to a graded, staggered cell field; and sand/graphite to pale limestone/charcoal. The camera shows the wider footprint from an oblique angle. There are no anatomical or shadow-picture motifs.

Final STL: **167,632 triangles**, one connected component, every edge incident to exactly two triangles, positive signed volume. GLB: one mesh and two materials. This is an **exported design study, not print-ready or a finished electrical product**. Slicer support and narrow-web strength, physical printing, removable LED support, access to charging/controls and electrical/thermal behavior remain untested.
