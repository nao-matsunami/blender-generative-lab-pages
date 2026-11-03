"""Tessellated Drift Lantern: graded hexagonal cells on a tapered nine-face shade, mm."""

import math
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "tessellated-drift-lantern"
HEIGHT = 158.0
SIDES = 9
TAU = 2 * math.pi
REVISION = 1


def wrap(a):
    return (a + math.pi) % TAU - math.pi


def radius(theta, z):
    u = z / HEIGHT
    face = wrap(theta + math.pi / SIDES) % (TAU / SIDES) - math.pi / SIDES
    apothem = 78.0 - 17.0 * u + 2.0 * math.sin(math.pi * u)
    # The polygon tapers inward but its axis drifts to one side.
    return apothem / math.cos(face) + 4.0 * u * math.cos(theta - .8)


def solid(theta, z):
    if z < 19 or z > 140:
        return True
    for row, center_z in enumerate((40.0, 79.0, 118.0)):
        for col in range(10):
            phase = (.25 if row == 1 else 0.0) + .065 * row
            center_theta = TAU * (col + phase) / 10
            x = (72.0 - 13.0 * z / HEIGHT) * wrap(theta - center_theta)
            y = z - center_z - 2.5 * math.sin(1.7 * col + row)
            size = 12.5 + 1.1 * math.sin(.9 * col + 1.4 * row)
            if max(abs(x), abs(.5 * x + .8660254 * y), abs(.5 * x - .8660254 * y)) < size:
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
    shell = LIB["material"]("matte_limestone_cells", (.82, .80, .72), roughness=.83)
    section = LIB["material"]("charcoal_cut_sections", (.23, .26, .27), roughness=.92)
    shade = LIB["build_shade"](SLUG, HEIGHT, radius, solid, shell, section)
    scene = LIB["setup_scene"](SLUG, HEIGHT, (340, -250, 184), 268)
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 960, 1080
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.013, .019, .022, 1)
    scene.view_settings.exposure = 2.65
    bpy.ops.object.light_add(type="AREA", location=(90, -170, 120))
    fill = bpy.context.object
    fill.data.energy = 76000
    fill.data.color = (.97, .95, .88)
    fill.data.size = 145
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
        target = ROOT / "designs/lanterns/2026-11-03" / f"{SLUG}.blend"
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))


if __name__ == "__main__":
    main()
