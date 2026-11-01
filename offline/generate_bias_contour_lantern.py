"""Bias Contour Lantern — one-piece contour lamella shade, dimensions in mm."""

import math
import os
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "bias-contour-lantern"
HEIGHT = 168.0
TAU = 2 * math.pi
REVISION = int(os.environ.get("BIAS_CONTOUR_REVISION", "0"))


def radius(theta, z):
    u = z / HEIGHT
    # Each contour expands and shifts relative to the grounded base ring.
    # The angular terms make a displaced, faceted stack rather than a round vase.
    facet = (theta - .17 + math.pi / 10) % (TAU / 5) - math.pi / 10
    apothem = 47.5 + 18.5 * u + 4.2 * math.sin(math.pi * u)
    offset = 12.0 * u * math.cos(theta - .30) + 5.0 * u * math.sin(theta + .65)
    return apothem / math.cos(facet) + offset


def solid(theta, z):
    if z < 14.0 or z > 158.0:
        return True
    # Uneven contour spacing follows a quadratic height rule. The band width
    # stays above 6 mm, while gaps open up toward the mouth.
    centers = (23.0, 36.5, 51.0, 66.6, 83.4, 101.3, 120.5, 141.0, 155.0)
    band = any(abs(z - c) < (3.5 if c < 120 else 3.9) for c in centers)
    # Four wide load bridges tie every lamella to the base and top. Their
    # angular drift gives an asymmetric rhythm without diagonal crosshatching.
    u = z / HEIGHT
    bridges = ((-.44, .105), (1.22, .092), (2.85, .105), (4.52, .095))
    for phase, half_width in bridges:
        center = phase + .12 * u * u
        difference = (theta - center + math.pi) % TAU - math.pi
        if abs(difference) < half_width:
            return True
    return band


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
    matte = LIB["material"]("chalk_white_contour", (.79, .80, .75), roughness=.79)
    section = LIB["material"]("pale_graphite_section", (.48, .51, .49), roughness=.84)
    shade = LIB["build_shade"](SLUG, HEIGHT, radius, solid, matte, section)
    scene = LIB["setup_scene"](SLUG, HEIGHT,
                               (225, -295, 225) if REVISION == 0 else (320, -185, 242),
                               280 if REVISION == 0 else 305)
    scene.cycles.samples = 20
    scene.render.resolution_x = 960
    scene.render.resolution_y = 1120
    scene.view_settings.exposure = 2.2 if REVISION == 0 else 2.5
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.013, .016, .017, 1)
    # Cool neutral fill separates the rear bridge from the inner contour walls.
    bpy.ops.object.light_add(type="AREA", location=(110, -170, 140))
    fill = bpy.context.object
    fill.name = "neutral_front_fill"
    fill.data.energy = 15000 if REVISION == 0 else 35000
    fill.data.color = (.88, .94, 1)
    fill.data.size = 145
    LIB["add_led"]((0, 0, 74))
    if REVISION:
        export_mesh(shade)
    scene.render.film_transparent = True
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}.png" if REVISION else f"{SLUG}-initial-alpha.png"))
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / "renders" / (f"{SLUG}-preview.png" if REVISION else f"{SLUG}-initial-preview.png"))
    bpy.ops.render.render(write_still=True)
    if REVISION:
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "designs/lanterns/2026-11-01" / f"{SLUG}.blend"))


if __name__ == "__main__":
    main()
