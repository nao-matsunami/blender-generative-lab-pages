"""Generate Biliary Duct Cleft assets in Blender.

Mac mini workflow:
npm run job:biliary
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "biliary-duct-cleft"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 152
V_SEGMENTS = 82


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def fold_field(u: float, v: float) -> float:
    theta = u * math.tau
    hilum = math.exp(-((v - 0.46) / 0.2) ** 2) * smoothstep(0.2, 0.98, 0.5 + 0.5 * math.sin(theta - 0.25))
    pleat = 0.0
    for index in range(9):
        center = (index / 9.0 + 0.18 * v + 0.025 * math.sin(v * math.tau)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        pleat += max(0.0, 1.0 - distance / 0.04) ** 2.2
    return min(1.0, hilum * 0.66 + pleat * 0.26)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + (0.012 + v * 0.976) * math.pi
    dome = max(0.0, math.cos(phi))
    fold = fold_field(u, v)
    front_cleft = math.exp(-((v - 0.43) / 0.18) ** 2) * smoothstep(0.2, 0.98, 0.5 + 0.5 * math.sin(theta - 0.25))
    kidney_bend = 1.0 + 0.18 * math.sin(theta + 0.7) - 0.08 * math.cos(phi * 2.0)
    rx = 54.0 * kidney_bend * (1.0 - 0.22 * front_cleft) + fold * 4.0
    ry = 34.0 * (1.0 + 0.08 * math.cos(theta * 2.0)) - front_cleft * 18.0
    rz = 50.0 * (1.0 + 0.1 * math.sin(theta - 0.5))
    x = math.cos(theta) * dome * rx + 10.0 * math.sin(phi * 1.4)
    y = math.sin(theta) * dome * ry - front_cleft * 13.0
    z = math.sin(phi) * rz + dome * math.sin(theta * 2.0) * 5.0
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = fold_field(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 2.6 + v * math.tau * 2.2)
    base = (0.62 + wet * 0.12, 0.12 + wet * 0.05, 0.18 + wet * 0.04)
    dark = (0.08, 0.001, 0.018)
    crease = min(0.86, fold * 0.8)
    return tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3)) + (1.0,)


def create_organ_mesh(material: bpy.types.Material) -> bpy.types.Object:
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
    mesh = bpy.data.meshes.new("biliary_folded_organ_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="biliary_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Biliary Folded Organ", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    weighted = obj.modifiers.new("biliary_weighted_normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    obj.select_set(False)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("wet_biliary_organ")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "biliary_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.17
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.11, 0.002, 0.025, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.06
    return material


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


def make_tube(name: str, points: list[tuple[float, float, float]], bevel: float, material: bpy.types.Material) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 18
    curve.bevel_depth = bevel
    curve.bevel_resolution = 8
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coords in zip(spline.points, points):
        point.co = (coords[0], coords[1], coords[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_cleft_parts(dark_material: bpy.types.Material, duct_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=28, radius=1, location=(0, -33, -2))
    pocket = bpy.context.object
    pocket.name = "biliary_dark_embedded_pocket"
    pocket.scale = (19, 8, 28)
    pocket.rotation_euler = (math.radians(6), 0, math.radians(-10))
    pocket.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(pocket)

    duct_a = make_tube("biliary_left_thick_duct", [(-42, -22, -16), (-26, -31, -8), (-11, -34, 0), (4, -33, 4)], 4.2, duct_material)
    duct_b = make_tube("biliary_right_thick_duct", [(36, -20, 26), (25, -30, 18), (12, -35, 8), (0, -33, 2)], 4.8, duct_material)
    duct_c = make_tube("biliary_lower_pressed_duct", [(-8, -28, -42), (-3, -35, -25), (1, -34, -8), (5, -32, 5)], 5.0, duct_material)
    objects.extend([duct_a, duct_b, duct_c])
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
    scene.view_settings.exposure = 1.48
    scene.view_settings.gamma = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-10))
        obj.rotation_euler.rotate_axis("X", math.radians(20))
        obj.location.z += 74
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -14, 72))
    target = bpy.context.object
    target.name = "biliary_camera_target"
    bpy.ops.object.camera_add(location=(-18, -242, 124), rotation=(math.radians(62), 0, math.radians(-5)))
    camera = bpy.context.object
    camera.data.lens = 54
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-126, -130, 190))
    key = bpy.context.object
    key.data.energy = 6500
    key.data.color = (1.0, 0.50, 0.46)
    key.data.size = 150
    bpy.ops.object.light_add(type="POINT", location=(124, 72, 132))
    rim = bpy.context.object
    rim.data.energy = 2200
    rim.data.color = (0.78, 0.02, 0.12)
    rim.data.shadow_soft_size = 86
    bpy.ops.object.light_add(type="AREA", location=(0, -190, 96))
    fill = bpy.context.object
    fill.data.energy = 700
    fill.data.color = (1.0, 0.62, 0.58)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("biliary_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "biliary_preview_dark_backdrop"
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
    organ = create_organ_mesh(material_from_attribute())
    dark_material = make_material("near_black_biliary_pocket", (0.005, 0.0, 0.003, 1.0), 0.62)
    duct_material = make_material("thick_dark_crimson_ducts", (0.50, 0.035, 0.09, 1.0), 0.18, 0.04)
    objects = [organ]
    objects.extend(add_cleft_parts(dark_material, duct_material))
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
