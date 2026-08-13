"""Generate Manta Bloom Shell assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:bloom

Outputs:
- exports/stl/manta-bloom-shell.stl
- exports/glb/manta-bloom-shell.glb
- renders/manta-bloom-shell.png
- renders/manta-bloom-shell-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "manta-bloom-shell.stl"
GLB_PATH = ROOT / "exports" / "glb" / "manta-bloom-shell.glb"
RENDER_PATH = ROOT / "renders" / "manta-bloom-shell.png"
PREVIEW_PATH = ROOT / "renders" / "manta-bloom-shell-preview.png"

RADIAL_SEGMENTS = 176
HEIGHT_SEGMENTS = 118
HEIGHT_MM = 148.0
WALL_THICKNESS_MM = 2.2


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    angle = u * math.tau + math.sin(v * math.pi) * 0.52
    wing = 1.0 + 0.28 * math.cos(angle * 2.0)
    base = 18.0 + 45.0 * (profile ** 0.56)
    taper = -8.0 * math.exp(-(((v - 0.93) / 0.08) ** 2)) - 6.0 * math.exp(-(((v - 0.06) / 0.06) ** 2))
    ripple = math.sin(u * math.tau * 8.0 + v * math.tau * 2.0) * 3.2 * profile
    petal = math.sin(u * math.tau * 4.0 - v * 7.5) * 4.6 * profile
    return (base + taper) * wing + ripple + petal


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    profile = math.sin(v * math.pi)
    vein = 0.5 + 0.5 * math.sin(u * math.tau * 8.0 + v * math.tau * 2.0)
    petal = 0.5 + 0.5 * math.sin(u * math.tau * 4.0 - v * 7.5)
    light = 0.68 + vein * 0.16 + petal * 0.09 + profile * 0.08
    return (min(1.0, 0.82 * light + 0.12), min(1.0, 0.24 * light + 0.07), min(1.0, 0.18 * light + 0.08), 1.0)


def create_shell_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        z = (v - 0.5) * HEIGHT_MM
        twist = math.sin(v * math.pi) * 0.52
        profile = math.sin(v * math.pi)
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau + twist
            radius = radius_at(u, v)
            oval = 0.58 + 0.16 * profile
            y_offset = math.cos(u * math.tau * 2.0) * 7.0 * profile
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius * oval, z + y_offset))
            colors.append(color_at(u, v))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("manta_bloom_shell_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="manta_bloom_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Manta Bloom Shell", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("manta_bloom_ceramic")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "manta_bloom_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.38
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.18, 0.04, 0.03, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.16
    return material


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_bloom_edges", "BEVEL")
    bevel.width = 0.42
    bevel.segments = 3

    weighted = obj.modifiers.new("weighted_bloom_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 0.62
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = HEIGHT_MM * 0.5
    obj.rotation_euler[2] = math.radians(-18)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.52))
    target = bpy.context.object
    target.name = "manta_render_target"

    bpy.ops.object.camera_add(location=(0, -405, HEIGHT_MM * 0.57), rotation=(math.radians(76), 0, 0))
    camera = bpy.context.object
    camera.name = "manta_render_camera"
    camera.data.lens = 46
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-125, -145, 160))
    key = bpy.context.object
    key.name = "manta_warm_key"
    key.data.energy = 1420
    key.data.color = (1.0, 0.58, 0.42)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(120, 80, 130))
    rim = bpy.context.object
    rim.name = "manta_cool_rim"
    rim.data.color = (0.55, 0.9, 1.0)
    rim.data.energy = 720
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
        world.color = (0.08, 0.1, 0.11)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    shell = create_shell_mesh()
    shell.data.materials.append(create_material())
    prepare_for_print(shell)
    setup_scene(shell)
    export_stl(shell)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
