"""Generate Gastric Rugae Maw assets in Blender.

Mac mini workflow:
npm run job:gastric

Outputs:
- exports/stl/gastric-rugae-maw.stl
- exports/glb/gastric-rugae-maw.glb
- renders/gastric-rugae-maw.png
- renders/gastric-rugae-maw-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "gastric-rugae-maw"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 176
V_SEGMENTS = 104


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def fold_field(u: float, v: float) -> float:
    theta = u * math.tau
    body = smoothstep(0.12, 0.32, v) * (1.0 - smoothstep(0.74, 0.93, v))
    diagonal = 0.0
    for i in range(8):
        center = (0.08 + i * 0.118 + 0.26 * v + 0.035 * math.sin(v * math.tau * 2.0)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        diagonal += max(0.0, 1.0 - distance / 0.05) ** 2.4
    collar = max(0.0, 1.0 - abs(v - 0.18) / 0.08) ** 2.0
    lower = max(0.0, 1.0 - abs(v - 0.77) / 0.075) ** 2.0
    pinched = math.exp(-1.0 * (((math.sin(theta + 0.8) + 1.0) / 0.36) ** 2 + ((v - 0.5) / 0.32) ** 2))
    return min(1.0, diagonal * body * 0.78 + collar * 0.78 + lower * 0.55 + pinched * 0.9)


def surface_point(u: float, v: float, lift: float = 0.0) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = max(0.0, math.cos(phi))
    fold = fold_field(u, v)
    pouch = 1.0 + 0.18 * math.sin(theta - 0.7) * smoothstep(0.18, 0.82, v)
    constrict = 1.0 - 0.34 * math.exp(-1.0 * (((math.sin(theta + 0.8) + 1.0) / 0.42) ** 2 + ((v - 0.52) / 0.34) ** 2))
    rx = 42.0 * pouch * constrict + fold * 10.0
    ry = 29.0 * (1.0 + 0.10 * math.sin(theta * 2.0 + 0.3)) * constrict + fold * 7.0
    rz = 70.0 * (1.0 + 0.06 * math.sin(theta * 3.0 - 0.4))
    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    z += 8.0 * math.sin(theta - 1.0) * dome
    point = Vector((x, y, z))
    outward = point.normalized() if point.length > 0.001 else Vector((0.0, 0.0, 1.0))
    return point + outward * lift


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = fold_field(u, v)
    theta = u * math.tau
    wet = 0.5 + 0.5 * math.sin(theta * 3.0 + v * math.tau * 2.2)
    base = (0.74 + wet * 0.16, 0.28 + wet * 0.07, 0.34 + wet * 0.08)
    crease = (0.22, 0.012, 0.055)
    pale = (0.96, 0.48, 0.46)
    fold_mix = min(0.88, fold * 0.88)
    highlight = smoothstep(0.55, 1.0, math.sin(theta - 0.2)) * smoothstep(0.26, 0.78, v) * 0.16
    mixed = tuple(base[i] * (1.0 - fold_mix) + crease[i] * fold_mix for i in range(3))
    return tuple(mixed[i] * (1.0 - highlight) + pale[i] * highlight for i in range(3)) + (1.0,)


def create_body_mesh() -> bpy.types.Object:
    vertices = []
    colors = []
    faces = []
    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            vertices.append(tuple(surface_point(u, v)))
            colors.append(color_at(u, v))
    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("gastric_rugae_maw_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="gastric_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Gastric Rugae Maw", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("gastric_wet_fold_skin")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = material.node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "gastric_skin_color"
        material.node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.18
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.12, 0.006, 0.035, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.07
    return material


def make_material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (color[0] * 0.15, color[1] * 0.06, color[2] * 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.07
    return material


def add_dark_maw(dark_material: bpy.types.Material, lip_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=24, radius=1, location=(-38, -9, 8))
    maw = bpy.context.object
    maw.name = "gastric_dark_internal_maw"
    maw.scale = (9.0, 3.4, 22)
    maw.rotation_euler = (math.radians(4), math.radians(-8), math.radians(-4))
    maw.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(maw)

    bpy.ops.mesh.primitive_torus_add(major_radius=15, minor_radius=3.2, major_segments=96, minor_segments=16, location=(-36, -10, 8))
    lip = bpy.context.object
    lip.name = "gastric_thick_compressed_lip"
    lip.scale = (0.82, 0.22, 1.35)
    lip.rotation_euler = (math.radians(92), math.radians(-8), math.radians(-4))
    lip.data.materials.append(lip_material)
    bpy.ops.object.shade_smooth()
    objects.append(lip)
    return objects


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "MESH":
        bpy.ops.object.shade_smooth()
        weighted = obj.modifiers.new("gastric_weighted_normals", "WEIGHTED_NORMAL")
        if weighted:
            weighted.keep_sharp = True
    obj.select_set(False)


def setup_scene(objects: list[bpy.types.Object]) -> None:
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
    scene.view_settings.exposure = 1.5
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-16))
        obj.rotation_euler.rotate_axis("X", math.radians(12))
        obj.location.z += 76

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-8, -2, 76))
    target = bpy.context.object
    target.name = "gastric_camera_target"

    bpy.ops.object.camera_add(location=(-92, -212, 118), rotation=(math.radians(64), 0, math.radians(-14)))
    camera = bpy.context.object
    camera.name = "gastric_camera"
    camera.data.lens = 54
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-126, -126, 190))
    key = bpy.context.object
    key.name = "gastric_warm_key"
    key.data.energy = 5600
    key.data.color = (1.0, 0.56, 0.52)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(108, 72, 128))
    rim = bpy.context.object
    rim.name = "gastric_dark_red_rim"
    rim.data.energy = 1700
    rim.data.color = (0.72, 0.03, 0.11)
    rim.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(0, -180, 98))
    fill = bpy.context.object
    fill.name = "gastric_soft_front"
    fill.data.energy = 760
    fill.data.color = (1.0, 0.66, 0.62)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    material = make_material("gastric_preview_dark_backdrop", (0.007, 0.001, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "gastric_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(material)


def export_stl(objects: list[bpy.types.Object]) -> None:
    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    try:
        bpy.ops.wm.stl_export(filepath=str(STL_PATH), export_selected_objects=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=str(STL_PATH), use_selection=True)


def export_glb(objects: list[bpy.types.Object]) -> None:
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_selection=True)


def render_outputs() -> None:
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.context.scene.render.film_transparent = True
    bpy.ops.render.render(write_still=True)
    add_preview_backdrop()
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.context.scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    skin = material_from_attribute()
    dark = make_material("gastric_internal_dark", (0.018, 0.001, 0.008, 1.0), 0.52)
    lip = make_material("gastric_compressed_lip", (0.78, 0.20, 0.28, 1.0), 0.16)
    body = create_body_mesh()
    body.data.materials.append(skin)
    objects = [body]
    objects.extend(add_dark_maw(dark, lip))
    for obj in objects:
        prepare_object(obj)
    setup_scene(objects)
    export_stl(objects)
    export_glb(objects)
    render_outputs()
    print(f"Generated {STL_PATH}")
    print(f"Generated {GLB_PATH}")
    print(f"Generated {RENDER_PATH}")
    print(f"Generated {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
