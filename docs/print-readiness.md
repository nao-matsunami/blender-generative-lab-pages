# Print Readiness

## Status Labels

Use these labels in study notes.

- `preview`: web/render concept only
- `exported`: STL/GLB exists
- `slicer-check`: opened in slicer and inspected
- `test-print`: small test printed
- `print-ready`: dimensions and material assumptions are documented

## Checklist

Before marking a piece `print-ready`:

- dimensions are in millimeters
- minimum wall thickness is documented
- the mesh is manifold
- normals face outward
- object sits on a practical base or has a clear support plan
- thin spikes and unsupported bridges are removed or thickened
- slicer preview has no unexpected holes
- material and nozzle assumptions are recorded

## Common Starting Assumptions

These are only starting points. Adjust for the printer/material.

- wall thickness: 2.0-3.0 mm
- small decorative ribs: 1.2 mm or thicker
- tiny contact points: avoid where possible
- test scale: 40-70 mm height

## Notes for Organic Forms

Organic forms often look good in render but fail as prints because of thin local features. Keep a "render form" and a "print form" if needed.
