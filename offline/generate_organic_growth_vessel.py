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

RADIAL_SEGMENTS = 160
HEIGHT_SEGMENTS = 92
HEIGHT_MM = 160.0
WALL_THICKNESS_MM = 2.4


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    waist = 31.0 + profile * 34.0
    lip = 16.0 * (v ** 4)
    foot = 13.0 * ((1.0 - v) ** 5)
    growth = (
        math.sin(u * math.tau * 5.0 + v * 8.5) * 3.4
        + math.sin(u * math.tau * 9.0 - v * 15.0) * 1.7
        + math.cos(u * math.tau * 2.0 + v * 5.0) * 2.2
    )
    rib = ((0.5 + 0.5 * math.sin(u * math.tau * 14.0 + v * 4.0)) ** 5) * 4.6
    return waist + lip + foot + (growth + rib) * profile


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
    material = bpy.data.materials.new("warm_clay_growth")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.42, 0.24, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.48
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.18
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.06, 0.02, 0.01, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


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

    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 64

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 18))
    target = bpy.context.object
    target.name = "render_target"

    bpy.ops.object.camera_add(location=(0, -250, 68), rotation=(math.radians(76), 0, 0))
    camera = bpy.context.object
    camera.name = "render_camera"
    camera.data.lens = 72
    bpy.context.scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-90, -120, 170))
    key = bpy.context.object
    key.name = "large_softbox_key"
    key.data.energy = 520
    key.data.size = 120

    bpy.ops.object.light_add(type="POINT", location=(110, 70, 130))
    rim = bpy.context.object
    rim.name = "cool_rim_light"
    rim.data.color = (0.48, 0.84, 1.0)
    rim.data.energy = 260
    rim.data.shadow_soft_size = 80

    obj.location.z = HEIGHT_MM * 0.5


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
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    vessel = create_vessel_mesh()
    vessel.data.materials.append(create_material())
    prepare_for_print(vessel)
    setup_scene(vessel)
    export_stl(vessel)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
