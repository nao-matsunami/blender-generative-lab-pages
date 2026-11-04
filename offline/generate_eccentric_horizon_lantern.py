"""Eccentric Horizon Lantern: broad phase-shifted horizon apertures, millimetres."""

import math
import os
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "eccentric-horizon-lantern"
HEIGHT = 164.0
TAU = 2 * math.pi
REVISION = int(os.environ.get("HORIZON_REVISION", "0"))


def wrap(a):
    return (a + math.pi) % TAU - math.pi


def radius(theta, z):
    u = z / HEIGHT
    # A narrow waist between a level 69 mm foot and a broad, offset upper mouth.
    base = 69 + 22 * u - 22 * math.sin(math.pi * u) ** 1.7
    wave = 4.0 * math.sin(3 * theta + 1.1 * u) * math.sin(math.pi * u) ** 2
    drift = 7.0 * u * math.cos(theta + .6)
    return base + wave + drift


def solid(theta, z):
    if z < 19 or z > 149:
        return True
    # Five long, closed horizontal windows sweep around different sectors.
    # Their phase follows a slow beat, so no vertical/diagonal grid is repeated.
    for k, center_z in enumerate((37.0, 63.0, 89.0, 115.0, 139.0)):
        center_theta = (-2.35 + .71 * k + .28 * math.sin(1.7 * k)
                        if not REVISION else -2.2 + .85 * math.sin(2.2 * k))
        angular = wrap(theta - center_theta - .075 * math.sin((z - center_z) / 13))
        halfspan = 1.12 + .16 * math.sin(1.9 * k + .3)
        height = (7.2 if not REVISION else 8.0) + 1.0 * math.sin(1.4 * k)
        # Elliptic ends make each opening a single smoothly bounded void.
        if (angular / halfspan) ** 2 + ((z - center_z) / height) ** 2 < 1:
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
    body_color = (.54, .61, .63) if not REVISION else (.73, .78, .77)
    outer = LIB["material"]("matte_mineral_bluegray", body_color, roughness=.79)
    inner = LIB["material"]("soft_graphite_sections", (.27, .32, .33), roughness=.88)
    shade = LIB["build_shade"](SLUG, HEIGHT, radius, solid, outer, inner)
    camera = (-315, -250, 192) if not REVISION else (-350, -220, 164)
    scene = LIB["setup_scene"](SLUG, HEIGHT, camera, 288 if not REVISION else 280)
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 960, 1080
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.014, .019, .023, 1)
    scene.view_settings.exposure = 2.35 if not REVISION else 2.55
    bpy.ops.object.light_add(type="AREA", location=(-90, -150, 125))
    fill = bpy.context.object
    fill.data.energy = 35000 if not REVISION else 78000
    fill.data.color = (1.0, .96, .89)
    fill.data.size = 155
    LIB["add_led"]((0, 0, 58))
    if REVISION:
        export_mesh(shade)
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}-preview.png" if REVISION else f"{SLUG}-initial-preview.png"))
    bpy.ops.render.render(write_still=True)
    if REVISION:
        scene.render.film_transparent = True
        scene.render.filepath = str(ROOT / "renders" / f"{SLUG}.png")
        bpy.ops.render.render(write_still=True)
        target = ROOT / "designs/lanterns/2026-11-04" / f"{SLUG}.blend"
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))


if __name__ == "__main__":
    main()
