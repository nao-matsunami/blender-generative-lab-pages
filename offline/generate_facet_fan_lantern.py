"""Facet Fan Lantern: nine noncrossing radial blade sectors, in millimetres."""

import math
import os
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "facet-fan-lantern"
HEIGHT = 166.0
TAU = 2 * math.pi
BLADES = 9
REVISION = int(os.environ.get("FAN_REVISION", "0"))


def wrap(a):
    return (a + math.pi) % TAU - math.pi


def radius(theta, z):
    u = z / HEIGHT
    # A wide faceted drum, with a broken rather than circular perimeter.
    face = wrap(theta + math.pi / BLADES) % (TAU / BLADES) - math.pi / BLADES
    apothem = 66 + 17 * math.sin(math.pi * u) ** 1.3
    facet = apothem / math.cos(face)
    ridge = 3.2 * math.cos(BLADES * theta + .3) * math.sin(math.pi * u) ** 2
    offset = 4.0 * u * math.cos(theta - .55)
    return facet + ridge + offset


def solid(theta, z):
    # Continuous collars carry nine separated broad vertical blades. Apertures
    # run between the blades; no diagonal bars or horizontal cutout rows.
    if z < 19 or z > 147:
        return True
    u = (z - 19) / 128
    for k in range(BLADES):
        center = TAU * (k + .06 * math.sin(1.8 * k)) / BLADES
        center += .07 * math.sin(math.pi * u) * math.sin(k * 1.3 + .5)
        width = (.145 if not REVISION else .17) + .025 * math.sin(2.1 * k + .4)
        width += .025 * math.sin(math.pi * u)
        if abs(wrap(theta - center)) <= width:
            return True
    return False


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
    shell = LIB["material"]("satin_pewter_blades", (.59, .62, .60) if not REVISION else (.69, .70, .65), roughness=.67)
    section = LIB["material"]("chalk_cut_sections", (.34, .37, .35), roughness=.87)
    shade = LIB["build_shade"](SLUG, HEIGHT, radius, solid, shell, section)
    if REVISION:
        # Tilt the open crown as one connected collar, without moving the foot.
        for vertex in shade.data.vertices:
            z = vertex.co.z
            if z > 135:
                t = min(1.0, (z - 135) / (HEIGHT - 135))
                t = t * t * (3 - 2 * t)
                theta = math.atan2(vertex.co.y, vertex.co.x)
                vertex.co.z += 8.0 * t * math.sin(theta + .45)
    scene = LIB["setup_scene"](SLUG, HEIGHT, (310, -300, 230) if not REVISION else (390, -110, 195), 270 if not REVISION else 258)
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 960, 1080
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.016, .019, .020, 1)
    scene.view_settings.exposure = 2.45 if not REVISION else 2.65
    bpy.ops.object.light_add(type="AREA", location=(-120, -185, 115) if not REVISION else (260, -190, 150))
    fill = bpy.context.object
    fill.data.energy = 52000 if not REVISION else 110000
    fill.data.color = (1, .98, .91)
    fill.data.size = 155
    LIB["add_led"]((0, 0, 54))
    if REVISION:
        export_mesh(shade)
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}-preview.png" if REVISION else f"{SLUG}-initial-preview.png"))
    bpy.ops.render.render(write_still=True)
    if REVISION:
        scene.render.film_transparent = True
        scene.render.filepath = str(ROOT / "renders" / f"{SLUG}.png")
        bpy.ops.render.render(write_still=True)
        target = ROOT / "designs/lanterns/2026-11-05" / f"{SLUG}.blend"
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))


if __name__ == "__main__":
    main()
