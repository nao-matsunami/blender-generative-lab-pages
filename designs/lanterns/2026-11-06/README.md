# Interference Basin — 2026-11-06

Nonfigurative, algorithmic light-object design study made on the actual production date. Generator: [`offline/generate_interference_basin.py`](../../../offline/generate_interference_basin.py).

Two concentric printed screens use different aperture rhythms. The flaring exterior has three rows of seven inclined, tapered openings; the interior has four phase-shifted rows of five wider openings. Their overlaps change with viewpoint. A 7 mm high continuous annular foot connects the screens into one body. The shell remains open at the top and through a central lower throat.

Outer radius: `67+16u+5sin(2θ+0.8u)sin²(πu)+3u cos(θ−0.8)` mm. Inner radius: `53+7u+2sin(3θ+u)sin²(πu)` mm, `u=z/160`. The outer openings' centers advance by 0.22 rad over their heights; their rows shift 0.34/7 revolution. Only aperture perimeter vertices are relaxed to remove cell stair steps.

Final STL bounds: **166.06 × 166.05 × 160.00 mm**. Nominal radial wall: **2.8 mm**. Planned narrowest web: approximately **9 mm**. Lower central passage: approximately **φ100.4 mm** in the design. The Etevia listing's 70 × 70 × 91 mm body nominally passes, but actual fit, touch and USB-C access, removal for charging, retention, airflow and heat are untested. The rechargeable E26 bulb dimensions remain unknown. **No mounting method is fixed.** LED tape and bare boards remain alternatives. The rendered LED point is illustrative only.

The first Blender GUI preview showed regular box-like windows. I changed aperture phase, taper and incline, material, light and camera, then rerendered. A subsequent preview revealed jagged opening edges, so I relaxed boundary vertices and rendered again. The final preview has legible nested depth, without visible clipping, detached parts or excessive darkness.

Compared with 2026-11-05 Facet Fan Lantern, silhouette, topology, construction method, surface rhythm, material and camera all change. The STL has **201,468 triangles**, one connected component, every **302,202 edges** incident to two faces, and positive signed volume. The GLB has one mesh and three materials. No anatomical motif, flesh or dark red palette, diagonal lattice or shadow picture appears.

This is an **exported design study, not print-ready or a finished electrical product**. Slicer review, physical strength and stability, print support in the nested gap, real LED controls, charging, retention, ventilation and thermal/electrical tests remain.
