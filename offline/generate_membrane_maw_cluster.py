"""Generate Membrane Maw Cluster assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:maw

Outputs:
- exports/stl/membrane-maw-cluster.stl
- exports/glb/membrane-maw-cluster.glb
- renders/membrane-maw-cluster.png
- renders/membrane-maw-cluster-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "membrane-maw-cluster.stl"
GLB_PATH = ROOT / "exports" / "glb" / "membrane-maw-cluster.glb"
RENDER_PATH = ROOT / "renders" / "membrane-maw-cluster.png"
PREVIEW_PATH = ROOT / "renders" / "membrane-maw-cluster-preview.png"

U_SEGMENTS = 160
V_SEGMENTS = 96


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    throat = 1.0 - smoothstep(0.0, 0.28, v)
    crown = 1.0 - smoothstep(0.72, 1.0, v)
    folds = math.sin(u * math.tau * 9.0 + v * math.tau * 1.6)
    small = math.sin(u * math.tau * 17.0 - v * math.tau * 2.2)
    lobes = 1.0 + 0.34 * math.sin(u * math.tau * 5.0 + 0.45) * profile
    base = 15.0 + 42.0 * (profile ** 0.58)
    mouth_pull = -19.0 * throat - 10.0 * (1.0 - crown)
    return (base + mouth_pull + folds * 4.7 * profile + small * 1.5 * profile) * lobes


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = 0.5 + 0.5 * math.sin(u * math.tau * 9.0 + v * math.tau * 1.6)
    vein = smoothstep(0.58, 0.95, 1.0 - fold)
    wet = 0.5 + 0.5 * math.sin(v * math.tau * 2.0 + u * math.tau * 3.0)
    rim = smoothstep(0.0, 0.18, v) * (1.0 - smoothstep(0.76, 1.0, v))
    base = (0.74 + wet * 0.16, 0.24 + wet * 0.06, 0.31 + wet * 0.06)
    bruise = (0.23, 0.04, 0.13)
    pale = (0.98, 0.52, 0.45)
    color = (
        base[0] * (1.0 - vein) + bruise[0] * vein,
        base[1] * (1.0 - vein) + bruise[1] * vein,
        base[2] * (1.0 - vein) + bruise[2] * vein,
    )
    return (
        color[0] * (1.0 - rim * 0.22) + pale[0] * rim * 0.22,
        color[1] * (1.0 - rim * 0.22) + pale[1] * rim * 0.22,
        color[2] * (1.0 - rim * 0.22) + pale[2] * rim * 0.22,
        1.0,
    )


def create_maw_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        z = (v - 0.5) * 112.0
        profile = math.sin(v * math.pi)
        twist = v * math.tau * 0.26 + math.sin(v * math.pi) * 0.22
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            angle = u * math.tau + twist
            radius = radius_at(u, v)
            pouch = math.sin(u * math.tau * 3.0 - v * math.tau * 0.7) * 7.0 * (profile ** 1.15)
            x = math.cos(angle) * (radius + pouch) * (0.92 + 0.08 * math.sin(v * math.tau * 2.0))
            y = math.sin(angle) * radius * (0.72 + 0.08 * math.cos(v * math.tau * 2.4))
            vertices.append((x, y, z))
            colors.append(color_at(u, v))

    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("membrane_maw_cluster_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="membrane_maw_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Membrane Maw Cluster", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("membrane_maw_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "membrane_maw_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.28
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.18, 0.03, 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.1
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    solidify = obj.modifiers.new("membrane_wall_thickness", "SOLIDIFY")
    solidify.thickness = 2.1
    solidify.offset = 0.0
    solidify.use_quality_normals = True
    bevel = obj.modifiers.new("soft_maw_edges", "BEVEL")
    bevel.width = 0.28
    bevel.segments = 2
    weighted = obj.modifiers.new("weighted_maw_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.22
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 72
    obj.rotation_euler[0] = math.radians(12)
    obj.rotation_euler[1] = math.radians(-6)
    obj.rotation_euler[2] = math.radians(-28)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 72))
    target = bpy.context.object
    target.name = "maw_render_target"

    bpy.ops.object.camera_add(location=(0, -315, 112), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "maw_render_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-125, -130, 178))
    key = bpy.context.object
    key.name = "maw_warm_key"
    key.data.energy = 3200
    key.data.color = (1.0, 0.55, 0.58)
    key.data.size = 145

    bpy.ops.object.light_add(type="POINT", location=(145, 80, 130))
    rim = bpy.context.object
    rim.name = "maw_crimson_rim"
    rim.data.color = (0.72, 0.1, 0.24)
    rim.data.energy = 1250
    rim.data.shadow_soft_size = 80

    bpy.ops.object.light_add(type="AREA", location=(0, -220, 115))
    front = bpy.context.object
    front.name = "maw_front_fill"
    front.data.energy = 680
    front.data.color = (1.0, 0.74, 0.7)
    front.data.size = 220


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("maw_preview_dark_backdrop")
    material.diffuse_color = (0.012, 0.004, 0.008, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.012, 0.004, 0.008, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "maw_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(material)


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
    add_preview_backdrop()
    world = bpy.context.scene.world
    if world:
        world.color = (0.012, 0.004, 0.008)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    maw = create_maw_mesh()
    maw.data.materials.append(create_material())
    prepare_object(maw)
    setup_scene(maw)
    export_stl(maw)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
