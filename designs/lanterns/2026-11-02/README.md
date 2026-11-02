# Splayed Fold Beacon — 2026-11-02

A nonfigurative algorithmic light-object shade study made on 2026-11-02. Generator: [`offline/generate_splayed_fold_beacon.py`](../../../offline/generate_splayed_fold_beacon.py).

## Rule and dimensions

Seven ruled facets splay from a 51.5 mm base apothem to a 79.5 mm upper apothem, with an 11.5 mm triangular crease field and a 9 mm asymmetric lean. Seven graded vertical portals have half widths roughly 0.16–0.26 radians and unequal endpoints. Exterior STL bounds: **171.53 × 173.76 × 172.00 mm**. Nominal wall: **2.8 mm**. Intended minimum portal web: approximately **20 mm**; the bottom is a continuous **16 mm** ring. The lower passage is conservatively at least **97 mm** in diameter in the design geometry; physical tolerance is unmeasured. Both office Prusa machines have a nominal build volume large enough for these bounds, pending slicer checks.

A removable rechargeable cordless LED core is the working integration direction. Etevia's listed 70 × 70 × 91 mm body is a nominal fit through the lower passage; its actual controls, USB port, retention, charging access, ventilation and operating temperature must be measured. The rechargeable E26 alternative has no confirmed exterior dimensions. **No holder or fixed interface is designed yet.**

## Review

The first GUI render looked too cylindrical. Increased fold amplitude and splay, extended the portals, changed the camera and brightened the front fill, then inspected the final Blender GUI PNG. The final preview shows the full silhouette and no detached pieces. STL: 137,408 triangles, one connected component, every edge incident to two faces, positive signed volume. GLB: one mesh, two materials.

Compared with 2026-11-01 Bias Contour Lantern: contour stack to splayed folded shell (silhouette); horizontal slots and four bridges to seven tall portals in a continuous shell (topology/construction); horizontal stepped rhythm to broad vertical folds (surface); chalk/graphite to sand/graphite (material); higher three-quarter view to lower oblique view (camera). No anatomy or shadow-picture motif.

**Exported design study, not print-ready.** Slicer support across the portal tops, actual print strength and stability, LED fit/retention, charge access, electrical and thermal behavior remain untested.
