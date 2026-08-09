"""Generate Organic Growth Vessel assets in Blender.

Run from this project root:
blender --background --python offline/generate_organic_growth_vessel.py

Outputs:
- exports/stl/organic-growth-vessel.stl
- exports/glb/organic-growth-vessel.glb
- renders/organic-growth-vessel.png

The first generated form is a design study. Check wall thickness, manifold
status, overhangs, and scale in a slicer before printing.
"""

import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in __import__("os").environ:
    ROOT = Path(__import__("os").environ["BLENDER_LAB_ROOT"]).resolve()
STL_PATH = ROOT / "exports" / "stl" / "organic-growth-vessel.stl"
GLB_PATH = ROOT / "exports" / "glb" / "organic-growth-vessel.glb"
RENDER_PATH = ROOT / "renders" / "organic-growth-vessel.png"
PREVIEW_PATH = ROOT / "renders" / "organic-growth-vessel-preview.png"

RADIAL_SEGMENTS = 160
HEIGHT_SEGMENTS = 92
HEIGHT_MM = 160.0
WALL_THICKNESS_MM = 2.4


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    waist = 26.0 + profile * 31.0
    shoulder = 14.0 * math.exp(-((v - 0.68) / 0.16) ** 2)
    neck_cut = -13.0 * math.exp(-((v - 0.91) / 0.08) ** 2)
    lip = 19.0 * math.exp(-((v - 0.985) / 0.035) ** 2)
    foot = 15.0 * math.exp(-((v - 0.055) / 0.045) ** 2)
    vertical_pulse = math.sin(v * math.pi * 3.0 + 0.6) * 2.5
    growth = (
        math.sin(u * math.tau * 5.0 + v * 8.5) * 5.8
        + math.sin(u * math.tau * 9.0 - v * 15.0) * 2.8
        + math.cos(u * math.tau * 2.0 + v * 5.0) * 3.6
    )
    rib_wave = math.sin(u * math.tau * 18.0 + v * 10.0)
    rib = (max(0.0, rib_wave) ** 6) * 9.5
    flute = -((max(0.0, -rib_wave)) ** 4) * 4.5
    return waist + shoulder + neck_cut + lip + foot + vertical_pulse + (growth + rib + flute) * profile


def create_vessel_mesh() -> bpy.types.Object:
    vertices = []
    faces = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        y = (v - 0.5) * HEIGHT_MM
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau
            radius = radius_at(u, v)
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius * 0.84, y))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, -HEIGHT_MM * 0.5))
    for x_index in range(RADIAL_SEGMENTS):
        a = x_index
        b = (x_index + 1) % RADIAL_SEGMENTS
        faces.append((bottom_center, b, a))

    mesh = bpy.data.meshes.new("organic_growth_vessel_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Organic Growth Vessel", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("burnished_coral_ceramic")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.92, 0.48, 0.30, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.38
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.42
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.18, 0.055, 0.025, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.05
    return material


def create_line_material() -> bpy.types.Material:
    material = bpy.data.materials.new("pale_ridge_read_lines")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 0.78, 0.54, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.32
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.36, 0.14, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.22
    return material


def add_growth_read_lines(material: bpy.types.Material) -> None:
    for rib_index in range(18):
        curve = bpy.data.curves.new(f"raised_growth_line_{rib_index:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = 0.34
        curve.bevel_resolution = 2
        spline = curve.splines.new("POLY")
        steps = 96
        spline.points.add(steps)
        seed = rib_index / 18.0
        for point_index in range(steps + 1):
            v = 0.08 + point_index / steps * 0.82
            u = (seed + 0.038 * math.sin(v * math.tau * 2.4 + rib_index) + v * 0.055) % 1.0
            angle = u * math.tau
            radius = radius_at(u, v) + 1.15
            point = spline.points[point_index]
            point.co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * 0.84,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )
        line = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(line)
        line.data.materials.append(material)


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_lip_and_foot", "BEVEL")
    bevel.width = 0.7
    bevel.segments = 3

    weighted = obj.modifiers.new("weighted_print_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 0.35
    scene.view_settings.gamma = 1.0

    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 64

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = HEIGHT_MM * 0.5

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.54))
    target = bpy.context.object
    target.name = "render_target"

    bpy.ops.object.camera_add(location=(0, -330, HEIGHT_MM * 0.58), rotation=(math.radians(76), 0, 0))
    camera = bpy.context.object
    camera.name = "render_camera"
    camera.data.lens = 48
    bpy.context.scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-90, -120, 170))
    key = bpy.context.object
    key.name = "large_softbox_key"
    key.data.energy = 950
    key.data.size = 150

    bpy.ops.object.light_add(type="AREA", location=(95, -70, 95))
    fill = bpy.context.object
    fill.name = "warm_low_fill"
    fill.data.color = (1.0, 0.62, 0.36)
    fill.data.energy = 260
    fill.data.size = 95

    bpy.ops.object.light_add(type="POINT", location=(110, 70, 130))
    rim = bpy.context.object
    rim.name = "cool_rim_light"
    rim.data.color = (0.48, 0.84, 1.0)
    rim.data.energy = 420
    rim.data.shadow_soft_size = 80


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
        world.color = (0.82, 0.86, 0.9)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    vessel = create_vessel_mesh()
    vessel.data.materials.append(create_material())
    prepare_for_print(vessel)
    setup_scene(vessel)
    add_growth_read_lines(create_line_material())
    export_stl(vessel)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
