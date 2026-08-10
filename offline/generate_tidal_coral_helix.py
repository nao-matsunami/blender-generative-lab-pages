"""Generate Tidal Coral Helix assets in Blender.

Run from this project root:
blender --background --python offline/generate_tidal_coral_helix.py

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:coral

Outputs:
- exports/stl/tidal-coral-helix.stl
- exports/glb/tidal-coral-helix.glb
- renders/tidal-coral-helix.png
- renders/tidal-coral-helix-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "tidal-coral-helix.stl"
GLB_PATH = ROOT / "exports" / "glb" / "tidal-coral-helix.glb"
RENDER_PATH = ROOT / "renders" / "tidal-coral-helix.png"
PREVIEW_PATH = ROOT / "renders" / "tidal-coral-helix-preview.png"

RADIAL_SEGMENTS = 168
HEIGHT_SEGMENTS = 132
HEIGHT_MM = 172.0
WALL_THICKNESS_MM = 2.4


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi) ** 0.58
    waist = 26.0 + 42.0 * profile
    taper = -10.0 * math.exp(-((v - 0.92) / 0.08) ** 2) - 8.0 * math.exp(-((v - 0.06) / 0.06) ** 2)
    helix = math.sin(u * math.tau * 5.0 + v * math.tau * 2.35) * 5.5
    coral = math.sin(u * math.tau * 17.0 - v * 11.0) * 2.1
    tide = math.cos(u * math.tau * 9.0 + v * 18.0) * 1.6
    return waist + taper + (helix + coral + tide) * profile


def create_coral_mesh() -> bpy.types.Object:
    vertices = []
    faces = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        z = (v - 0.5) * HEIGHT_MM
        twist = v * math.tau * 0.82
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau + twist
            radius = radius_at(u, v)
            oval = 0.82 + 0.08 * math.sin(v * math.tau * 3.0)
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius * oval, z))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("tidal_coral_helix_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Tidal Coral Helix", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_shell_material() -> bpy.types.Material:
    material = bpy.data.materials.new("tidal_coral_porcelain")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.88, 0.34, 0.42, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.34
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.32
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.18, 0.04, 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.1
    return material


def create_ridge_material() -> bpy.types.Material:
    material = bpy.data.materials.new("tidal_cyan_ridges")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.38, 0.95, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.15, 0.78, 1.0, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.55
    return material


def add_helix_ridges(material: bpy.types.Material) -> None:
    for ridge_index in range(18):
        curve = bpy.data.curves.new(f"tidal_helix_ridge_{ridge_index:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = 0.42
        curve.bevel_resolution = 3
        spline = curve.splines.new("POLY")
        steps = 136
        spline.points.add(steps)
        lane = ridge_index / 18.0
        for point_index in range(steps + 1):
            v = 0.05 + point_index / steps * 0.9
            u = (lane - v * 0.34 + math.sin(v * math.tau * 2.0 + ridge_index) * 0.018) % 1.0
            angle = u * math.tau + v * math.tau * 0.82
            radius = radius_at(u, v) + 1.2
            oval = 0.82 + 0.08 * math.sin(v * math.tau * 3.0)
            spline.points[point_index].co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * oval,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )
        obj = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material)


def add_coral_nodes(material: bpy.types.Material) -> None:
    for node_index in range(42):
        v = 0.08 + ((node_index * 0.237 + 0.04 * math.sin(node_index)) % 0.84)
        u = (node_index * 0.61803398875 + v * 0.11) % 1.0
        angle = u * math.tau + v * math.tau * 0.82
        radius = radius_at(u, v) + 1.7
        oval = 0.82 + 0.08 * math.sin(v * math.tau * 3.0)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=18,
            ring_count=9,
            radius=1.3 + 1.2 * (0.5 + 0.5 * math.sin(node_index * 1.7)),
            location=(math.cos(angle) * radius, math.sin(angle) * radius * oval, (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5),
        )
        node = bpy.context.object
        node.name = f"tidal_coral_node_{node_index:02d}"
        node.scale.z = 0.42
        node.data.materials.append(material)


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_coral_edges", "BEVEL")
    bevel.width = 0.48
    bevel.segments = 3

    weighted = obj.modifiers.new("weighted_coral_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 0.36
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = HEIGHT_MM * 0.5

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.56))
    target = bpy.context.object
    target.name = "tidal_render_target"

    bpy.ops.object.camera_add(location=(0, -365, HEIGHT_MM * 0.62), rotation=(math.radians(75), 0, 0))
    camera = bpy.context.object
    camera.name = "tidal_render_camera"
    camera.data.lens = 50
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="POINT", location=(0, 0, 58))
    core = bpy.context.object
    core.name = "tidal_inner_glow"
    core.data.energy = 520
    core.data.color = (0.25, 0.88, 1.0)
    core.data.shadow_soft_size = 100

    bpy.ops.object.light_add(type="AREA", location=(-130, -145, 170))
    key = bpy.context.object
    key.name = "tidal_warm_key"
    key.data.energy = 900
    key.data.color = (1.0, 0.54, 0.48)
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(125, 80, 135))
    rim = bpy.context.object
    rim.name = "tidal_cyan_rim"
    rim.data.color = (0.45, 0.92, 1.0)
    rim.data.energy = 500
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
        world.color = (0.72, 0.78, 0.82)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    coral = create_coral_mesh()
    coral.data.materials.append(create_shell_material())
    prepare_for_print(coral)
    setup_scene(coral)
    ridge_material = create_ridge_material()
    add_helix_ridges(ridge_material)
    add_coral_nodes(ridge_material)
    export_stl(coral)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
