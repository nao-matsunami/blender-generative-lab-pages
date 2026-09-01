"""Generate Inverted Membrane Cavity assets in Blender.

Mac mini workflow:
npm run job:cavity
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "inverted-membrane-cavity"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 176
V_SEGMENTS = 92


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def fold_field(u: float, v: float) -> float:
    theta = u * math.tau
    collar = math.exp(-1.0 * ((v - 0.52) / 0.16) ** 2)
    pleats = 0.0
    for i in range(10):
        center = (i / 10.0 + 0.18 * v + 0.025 * math.sin(v * math.tau * 2.0)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        pleats += max(0.0, 1.0 - distance / 0.034) ** 2.1
    asym = 0.5 + 0.5 * math.sin(theta * 2.0 - 0.8)
    return min(1.0, collar * 0.64 + pleats * 0.34 + asym * 0.12)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = max(0.0, math.cos(phi))
    fold = fold_field(u, v)
    mouth = math.exp(-1.0 * ((v - 0.52) / 0.18) ** 2)
    pinch = 1.0 - 0.42 * mouth
    rx = 58.0 * pinch * (1.0 + 0.1 * math.sin(theta * 3.0 + 0.4)) + fold * 7.0
    ry = 42.0 * pinch * (1.0 + 0.08 * math.cos(theta * 2.0 - 0.3)) + fold * 5.0
    rz = 52.0 * (1.0 + 0.08 * math.sin(theta * 2.0))
    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    z += 7.0 * math.sin(theta - 0.9) * dome
    y -= mouth * 17.0
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = fold_field(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 3.0 + v * math.tau * 2.1)
    base = (0.72 + wet * 0.15, 0.20 + wet * 0.07, 0.30 + wet * 0.07)
    dark = (0.13, 0.004, 0.04)
    crease = min(0.86, fold * 0.84)
    return tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3)) + (1.0,)


def create_membrane_mesh() -> bpy.types.Object:
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
    mesh = bpy.data.meshes.new("inverted_membrane_cavity_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="cavity_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Inverted Membrane Cavity", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("cavity_wet_membrane")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "cavity_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.17
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.11, 0.004, 0.035, 1.0)
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
    return material


def add_dark_cavity(dark_material: bpy.types.Material, lip_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=28, radius=1, location=(0, -28, 0))
    void = bpy.context.object
    void.name = "cavity_dark_interior"
    void.scale = (31, 7, 23)
    void.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(void)

    bpy.ops.mesh.primitive_torus_add(major_radius=33, minor_radius=4.6, major_segments=128, minor_segments=18, location=(0, -24, 0))
    lip = bpy.context.object
    lip.name = "cavity_inverted_lip"
    lip.scale = (1.0, 0.32, 0.72)
    lip.rotation_euler = (math.radians(90), 0, 0)
    lip.data.materials.append(lip_material)
    bpy.ops.object.shade_smooth()
    objects.append(lip)
    return objects


def prepare(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "MESH":
        bpy.ops.object.shade_smooth()
        weighted = obj.modifiers.new("cavity_weighted_normals", "WEIGHTED_NORMAL")
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
    world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-12))
        obj.rotation_euler.rotate_axis("X", math.radians(24))
        obj.location.z += 74
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -4, 74))
    target = bpy.context.object
    target.name = "cavity_camera_target"
    bpy.ops.object.camera_add(location=(-20, -232, 128), rotation=(math.radians(62), 0, math.radians(-5)))
    camera = bpy.context.object
    camera.data.lens = 56
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-132, -126, 190))
    key = bpy.context.object
    key.data.energy = 5900
    key.data.color = (1.0, 0.52, 0.52)
    key.data.size = 150
    bpy.ops.object.light_add(type="POINT", location=(120, 72, 130))
    rim = bpy.context.object
    rim.data.energy = 1900
    rim.data.color = (0.72, 0.03, 0.12)
    rim.data.shadow_soft_size = 90
    bpy.ops.object.light_add(type="AREA", location=(0, -188, 100))
    fill = bpy.context.object
    fill.data.energy = 840
    fill.data.color = (1.0, 0.64, 0.62)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("cavity_preview_dark_backdrop", (0.007, 0.001, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "cavity_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(mat)


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
    dark = make_material("cavity_internal_dark", (0.014, 0.001, 0.007, 1.0), 0.54)
    lip = make_material("cavity_lip_skin", (0.74, 0.15, 0.25, 1.0), 0.17)
    membrane = create_membrane_mesh()
    membrane.data.materials.append(skin)
    objects = [membrane]
    objects.extend(add_dark_cavity(dark, lip))
    for obj in objects:
        prepare(obj)
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
