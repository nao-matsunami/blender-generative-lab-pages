# Bias Contour Lantern — 2026-11-01

Nonfigurative contour-lamella light-object study. Generator: `../../../offline/generate_bias_contour_lantern.py`. The lower and upper openings remain clear for an independent low-heat LED prototype and air movement. No electrical assembly is part of the model.

The generating rule uses a five-facet radial contour with an apothem of `47.5 + 18.5u + 4.2 sin(pi u)` mm, and an offset of `12u cos(theta - 0.30) + 5u sin(theta + 0.65)` mm. Horizontal bands use center heights 23, 36.5, 51, 66.6, 83.4, 101.3, 120.5, 141 and 155 mm. Four broad, slightly drifting vertical bridges connect all layers. The base and top have continuous 14 and 10 mm tall rings.

Measured STL bounding box: 206.89 × 214.02 × 168.00 mm. Nominal shell wall: 2.8 mm. Narrowest intended band: 7.0 mm; narrowest bridge at the base: about 8.7 mm. The flat annular base rim supplies the stable contact surface. STL has 136,072 triangles, one connected component, every edge incident to two triangles, and positive signed volume. GLB has one mesh and two materials.

The first GUI preview showed an overly dark near bridge. A second GUI render used a more oblique camera, stronger neutral fill and higher exposure. The final preview was visually inspected. The retained `.blend` file is the saved final session. Slicer review, physical print, base/LED fit, cable routing and thermal/electrical testing remain open; this is not a print-ready electrical lamp.

The specific open tasks and printer/LED inputs are tracked in [light-object-validation.md](../../../docs/light-object-validation.md). The office has a Prusa MK4S and CORE One. Rotation of the STL by about 63.05° about Z reduces its XY bounding box to about 200.27 × 195.28 mm, within both nominal build volumes. Slicer verification is pending.

The current shape has an approximately 89.4 mm centered bottom clearance diameter. The user's intended lighting approach is a removable rechargeable consumer LED core inside a custom printed shade/support. An Amazon Etevia touch light is listed at 70 × 70 × 91 mm and dimensionally passes the modeled lower throat; a rechargeable remote-controlled E26 bulb is another reference but its body dimensions are unverified. The holder, charging access, controls and thermal path remain to be designed. See the validation note for product sources and uncertainties.
