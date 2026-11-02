"""Splayed Fold Beacon: faceted ruled shell with seven tall graded portals, mm."""

import math
import os
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "splayed-fold-beacon"
HEIGHT = 172.0
FACETS = 7
TAU = 2 * math.pi
REVISION = int(os.environ.get("SPLAYED_FOLD_REVISION", "3"))


def wrap(a):
    return (a + math.pi) % TAU - math.pi


def radius(theta, z):
    u = z / HEIGHT
    phase = -.13 + .055 * u
    facet = wrap(theta - phase + math.pi / FACETS) % (TAU / FACETS) - math.pi / FACETS
    # A ruled heptagonal section opens upward. Alternate creases push the
    # midsides outward; the resulting fold faces, rather than decoration,
    # determine the surface and silhouette.
    apothem = 51.5 + (14.0 if REVISION == 0 else 28.0) * u + 2.5 * math.sin(math.pi * u)
    ridge = (4.3 if REVISION == 0 else 11.5) * (1 - abs(facet) / (math.pi / FACETS)) * math.sin(math.pi * (.16 + .78 * u))
    lean = (5.5 if REVISION == 0 else 9.0) * u * math.cos(theta - .7)
    return apothem / math.cos(facet) + ridge + lean


def solid(theta, z):
    if z < 16 or z > 164:
        return True
    u = z / HEIGHT
    for k in range(FACETS):
        center = TAU * (k + .5) / FACETS - .13 + .055 * u
        d = abs(wrap(theta - center))
        low = (25.0 + 5.0 * math.sin(1.4 * k + .3)) if REVISION < 3 else (21.0 + 3.0 * math.sin(1.4 * k + .3))
        high = (145.0 - 5.0 * math.cos(1.8 * k)) if REVISION < 3 else (160.0 - 2.0 * math.cos(1.8 * k))
        if low < z < high:
            t = (z - low) / (high - low)
            # Tapered portals leave at least ~22 mm of uncut wall between them.
            half = .175 + .065 * math.sin(math.pi * t) + .018 * math.sin(k * 2.1)
            if d < half:
                return False
    return True


def export_mesh(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(ROOT / "exports/stl" / f"{SLUG}.stl"),
                          export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT / "exports/glb" / f"{SLUG}.glb"),
                              export_format="GLB", use_selection=True, export_apply=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    stone = LIB["material"]("cool_sand_fold_faces", (.72, .69, .60), roughness=.76)
    inside = LIB["material"]("graphite_fold_sections", (.33, .34, .33), roughness=.88)
    shade = LIB["build_shade"](SLUG, HEIGHT, radius, solid, stone, inside)
    camera = (250, -280, 214) if REVISION == 0 else ((310, -205, 200) if REVISION == 1 else (370, -160, 180))
    scene = LIB["setup_scene"](SLUG, HEIGHT, camera, 275 if REVISION == 0 else 305)
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 960, 1120
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.015, .019, .021, 1)
    scene.view_settings.exposure = 2.25 if REVISION == 0 else (2.40 if REVISION == 1 else 2.50)
    bpy.ops.object.light_add(type="AREA", location=(80, -150, 145))
    fill = bpy.context.object
    fill.data.energy = 18000 if REVISION == 0 else (30000 if REVISION == 1 else 62000)
    fill.data.color = (.90, .94, 1)
    fill.data.size = 140
    LIB["add_led"]((0, 0, 65))
    if REVISION:
        export_mesh(shade)
    scene.render.film_transparent = True
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}.png" if REVISION else f"{SLUG}-initial-alpha.png"))
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}-preview.png" if REVISION else f"{SLUG}-initial-preview.png"))
    bpy.ops.render.render(write_still=True)
    if REVISION:
        target = ROOT / "designs/lanterns/2026-11-02" / f"{SLUG}.blend"
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))


if __name__ == "__main__":
    main()
