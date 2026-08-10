"""Generate Luminous Seed Vessel assets in Blender.

Run from this project root:
blender --background --python offline/generate_luminous_seed_vessel.py

Outputs:
- exports/stl/luminous-seed-vessel.stl
- exports/glb/luminous-seed-vessel.glb
- renders/luminous-seed-vessel.png
- renders/luminous-seed-vessel-preview.png

This is part of Organic Motion Objects. Treat the first STL as a design study
until a slicer confirms wall thickness, manifold status, and support needs.
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "luminous-seed-vessel.stl"
GLB_PATH = ROOT / "exports" / "glb" / "luminous-seed-vessel.glb"
RENDER_PATH = ROOT / "renders" / "luminous-seed-vessel.png"
PREVIEW_PATH = ROOT / "renders" / "luminous-seed-vessel-preview.png"

RADIAL_SEGMENTS = 184
HEIGHT_SEGMENTS = 116
HEIGHT_MM = 158.0
WALL_THICKNESS_MM = 2.6


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    belly = 22.0 + profile * 48.0
    shoulder = 12.0 * math.exp(-((v - 0.62) / 0.19) ** 2)
    neck = -13.0 * math.exp(-((v - 0.94) / 0.08) ** 2)
    tail = -8.0 * math.exp(-((v - 0.05) / 0.06) ** 2)
    rib_wave = math.sin(u * math.tau * 9.0 + v * 8.0)
    crease = ((0.5 + 0.5 * math.sin(u * math.tau * 18.0 + v * 12.0)) ** 4) * 4.3
    drift = math.sin(u * math.tau * 3.0 - v * 6.0) * 3.1 + math.cos(u * math.tau * 5.0 + v * 9.5) * 2.6
    return belly + shoulder + neck + tail + (drift + crease + rib_wave * 1.7) * profile


def create_seed_mesh() -> bpy.types.Object:
    vertices = []
    faces = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        z = (v - 0.5) * HEIGHT_MM
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau
            radius = radius_at(u, v)
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius * 0.78, z))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("luminous_seed_vessel_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Luminous Seed Vessel", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_shell_material() -> bpy.types.Material:
    material = bpy.data.materials.new("luminous_seed_ceramic")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.46, 0.22, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.36
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.42
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.24, 0.08, 0.02, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.12
    return material


def create_vein_material() -> bpy.types.Material:
    material = bpy.data.materials.new("warm_luminous_veins")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 0.72, 0.38, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.28
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.42, 0.12, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.38
    return material


def create_window_material() -> bpy.types.Material:
    material = bpy.data.materials.new("cool_seed_window_rims")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.55, 0.9, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.22, 0.72, 1.0, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.85
    return material


def add_vein_lines(material: bpy.types.Material) -> None:
    for rib_index in range(24):
        curve = bpy.data.curves.new(f"seed_luminous_vein_{rib_index:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = 0.3
        curve.bevel_resolution = 2
        spline = curve.splines.new("POLY")
        steps = 112
        spline.points.add(steps)
        seed = rib_index / 24.0
        for point_index in range(steps + 1):
            v = 0.07 + point_index / steps * 0.86
            u = (seed + math.sin(v * math.tau * 2.0 + rib_index * 0.73) * 0.026 + v * 0.07) % 1.0
            angle = u * math.tau
            radius = radius_at(u, v) + 1.1
            spline.points[point_index].co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * 0.78,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )
        obj = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material)


def add_window_rims(material: bpy.types.Material) -> None:
    for cell in range(32):
        center_u = (cell * 0.61803398875 + 0.04 * math.sin(cell)) % 1.0
        center_v = 0.13 + ((cell * 0.271 + 0.03 * math.cos(cell * 1.7)) % 0.72)
        width = 0.018 + 0.012 * (0.5 + 0.5 * math.sin(cell * 2.1))
        height = 0.024 + 0.018 * (0.5 + 0.5 * math.cos(cell * 1.4))
        twist = cell * 0.57

        curve = bpy.data.curves.new(f"seed_window_rim_{cell:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 3
        curve.bevel_depth = 0.5
        curve.bevel_resolution = 3
        spline = curve.splines.new("POLY")
        points = 40
        spline.points.add(points)

        for index in range(points + 1):
            t = index / points * math.tau
            du = math.cos(t) * width
            dv = math.sin(t) * height
            u = (center_u + du * math.cos(twist) - dv * math.sin(twist) * 0.42) % 1.0
            v = min(0.94, max(0.06, center_v + du * math.sin(twist) + dv * math.cos(twist)))
            angle = u * math.tau
            radius = radius_at(u, v) + 1.55
            spline.points[index].co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * 0.78,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )

        obj = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material)


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_seed_edges", "BEVEL")
    bevel.width = 0.55
    bevel.segments = 3

    weighted = obj.modifiers.new("weighted_seed_normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True


def setup_scene(obj: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.filepath = str(RENDER_PATH)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.42
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = HEIGHT_MM * 0.5

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.55))
    target = bpy.context.object
    target.name = "seed_render_target"

    bpy.ops.object.camera_add(location=(0, -340, HEIGHT_MM * 0.58), rotation=(math.radians(76), 0, 0))
    camera = bpy.context.object
    camera.name = "seed_render_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="POINT", location=(0, 0, 42))
    core = bpy.context.object
    core.name = "warm_seed_core"
    core.data.energy = 640
    core.data.color = (1.0, 0.48, 0.2)
    core.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(-105, -130, 160))
    key = bpy.context.object
    key.name = "seed_large_key"
    key.data.energy = 920
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(120, 70, 130))
    rim = bpy.context.object
    rim.name = "seed_cool_rim"
    rim.data.color = (0.58, 0.9, 1.0)
    rim.data.energy = 440
    rim.data.shadow_soft_size = 75


def export_stl(obj: bpy.types.Object) -> None:
    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.wm.stl_export(filepath=str(STL_PATH), export_selected_objects=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=str(STL_PATH), use_selection=True)


def export_glb() -> None:
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB")


def render_still() -> None:
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.ops.render.render(write_still=True)

    world = bpy.context.scene.world
    if world:
        world.color = (0.8, 0.83, 0.86)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    seed = create_seed_mesh()
    seed.data.materials.append(create_shell_material())
    prepare_for_print(seed)
    setup_scene(seed)
    add_vein_lines(create_vein_material())
    add_window_rims(create_window_material())
    export_stl(seed)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
