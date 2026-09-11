"""Generate Splenic Pulp Lacuna assets in Blender.

Mac mini workflow:
npm run job:splenicpulp
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "splenic-pulp-lacuna"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 150
V_SEGMENTS = 80
PITS = ((0.10, 0.36, 0.95), (0.23, 0.63, 0.8), (0.43, 0.48, 1.1), (0.62, 0.66, 0.75), (0.78, 0.39, 0.9))


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def pit_at(u: float, v: float) -> float:
    value = 0.0
    for center_u, center_v, weight in PITS:
        du = abs(((u - center_u + 0.5) % 1.0) - 0.5)
        dv = v - center_v
        value += weight * math.exp(-((du / 0.065) ** 2 + (dv / 0.11) ** 2))
    return min(1.0, value)


def ridge_at(u: float, v: float) -> float:
    theta = u * math.tau
    pulp = 0.0
    for index in range(9):
        center = index / 9.0 + 0.035 * math.sin(v * math.tau * 1.7)
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        pulp += max(0.0, 1.0 - distance / 0.07) ** 2.2
    broad = 0.5 + 0.5 * math.sin(theta * 2.0 - v * math.tau)
    return min(1.0, pulp * 0.3 + pit_at(u, v) * 0.48 + broad * 0.13)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + (0.015 + v * 0.97) * math.pi
    dome = max(0.0, math.cos(phi))
    pit = pit_at(u, v)
    ridge = ridge_at(u, v)
    rx = 51.0 * (1.0 + 0.11 * math.sin(theta - 0.4)) + ridge * 5.5 - pit * 15.0
    ry = 28.0 * (1.0 + 0.1 * math.cos(phi * 1.2)) - pit * 18.0
    rz = 47.0 * (1.0 + 0.12 * math.cos(theta + 0.2))
    x = math.cos(theta) * dome * rx + 9.0 * math.sin(phi * 1.2)
    y = math.sin(theta) * dome * ry - pit * 15.0
    z = math.sin(phi) * rz + dome * math.sin(theta * 2.8 + v * math.tau) * 3.5
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    pit = pit_at(u, v)
    ridge = ridge_at(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 3.1 + v * math.tau * 1.8)
    base = (0.58 + wet * 0.14, 0.045 + wet * 0.035, 0.12 + wet * 0.055)
    dark = (0.025, 0.0, 0.007)
    crease = min(0.94, pit * 0.72 + ridge * 0.32)
    return tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3)) + (1.0,)


def make_material(name: str, color: tuple[float, float, float, float], roughness: float, emission: float = 0.0) -> bpy.types.Material:
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
            bsdf.inputs["Emission Color"].default_value = color
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return material


def attribute_material() -> bpy.types.Material:
    material = bpy.data.materials.new("wet_splenic_pulp_skin")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "splenic_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.14
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.09, 0.0, 0.02, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.05
    return material


def create_body(material: bpy.types.Material) -> bpy.types.Object:
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
    mesh = bpy.data.meshes.new("splenic_pulp_lacuna_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="splenic_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Splenic Pulp Lacuna Body", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.modifiers.new("splenic_weighted_normals", "WEIGHTED_NORMAL")
    obj.select_set(False)
    return obj


def add_lacuna_parts(dark_material: bpy.types.Material, lip_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    placements = [(-27, -31, -8, 11, 4, 15), (-13, -35, 18, 10, 4, 12), (8, -37, -1, 13, 5, 18), (24, -33, 19, 9, 4, 12), (31, -31, -18, 10, 4, 14)]
    for index, (x, y, z, sx, sy, sz) in enumerate(placements):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=54, ring_count=18, radius=1, location=(x, y, z))
        pit = bpy.context.object
        pit.name = f"splenic_deep_lacuna_{index + 1}"
        pit.scale = (sx, sy, sz)
        pit.data.materials.append(dark_material)
        bpy.ops.object.shade_smooth()
        objects.append(pit)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=18, radius=1, location=(x * 0.98, y + 1.2, z))
        lip = bpy.context.object
        lip.name = f"splenic_compressed_lacuna_lip_{index + 1}"
        lip.scale = (sx * 1.35, 2.3, sz * 1.18)
        lip.rotation_euler = (math.radians(4), 0, math.radians(index * 17 - 28))
        lip.data.materials.append(lip_material)
        bpy.ops.object.shade_smooth()
        objects.append(lip)
    return objects


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
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-10))
        obj.rotation_euler.rotate_axis("X", math.radians(18))
        obj.location.z += 72
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -18, 74))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(-18, -250, 134), rotation=(math.radians(62), 0, math.radians(-4)))
    camera = bpy.context.object
    camera.data.lens = 56
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-128, -136, 202))
    key = bpy.context.object
    key.data.energy = 7200
    key.data.color = (1.0, 0.38, 0.42)
    key.data.size = 145
    bpy.ops.object.light_add(type="POINT", location=(120, 72, 136))
    rim = bpy.context.object
    rim.data.energy = 2300
    rim.data.color = (0.72, 0.0, 0.08)
    rim.data.shadow_soft_size = 90
    bpy.ops.object.light_add(type="AREA", location=(0, -196, 112))
    fill = bpy.context.object
    fill.data.energy = 650
    fill.data.color = (1.0, 0.56, 0.58)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("splenic_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "splenic_preview_dark_backdrop"
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
    body = create_body(attribute_material())
    dark_material = make_material("near_black_splenic_lacuna", (0.004, 0.0, 0.003, 1.0), 0.7)
    lip_material = make_material("compressed_splenic_pulp_lips", (0.68, 0.055, 0.12, 1.0), 0.15, 0.05)
    objects = [body]
    objects.extend(add_lacuna_parts(dark_material, lip_material))
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
