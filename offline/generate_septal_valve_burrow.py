"""Generate Septal Valve Burrow assets in Blender.

Mac mini workflow:
npm run job:septal
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "septal-valve-burrow"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 156
V_SEGMENTS = 82


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def slit_field(u: float, v: float) -> float:
    theta = u * math.tau
    front = smoothstep(0.12, 0.98, 0.5 + 0.5 * math.sin(theta - 0.18))
    vertical = math.exp(-((v - 0.5) / 0.24) ** 2)
    return front * vertical


def fold_field(u: float, v: float) -> float:
    theta = u * math.tau
    slit = slit_field(u, v)
    valve = 0.0
    centers = (0.08 + 0.11 * math.sin(v * math.tau), 0.39 + 0.08 * v, 0.72 - 0.1 * v)
    for center in centers:
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        valve += max(0.0, 1.0 - distance / 0.055) ** 2.6
    damp = 0.68 + 0.32 * math.sin(theta * 2.0 + v * math.tau)
    return min(1.0, valve * 0.45 + slit * 0.36 + damp * 0.16)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + (0.018 + v * 0.964) * math.pi
    dome = max(0.0, math.cos(phi))
    slit = slit_field(u, v)
    fold = fold_field(u, v)
    left_pressure = math.exp(-(((u - 0.18 + 0.5) % 1.0 - 0.5) / 0.1) ** 2) * math.exp(-((v - 0.6) / 0.22) ** 2)
    right_pressure = math.exp(-(((u - 0.82 + 0.5) % 1.0 - 0.5) / 0.12) ** 2) * math.exp(-((v - 0.38) / 0.2) ** 2)
    rx = 46.0 * (1.0 + 0.08 * math.sin(theta * 2.0)) + fold * 7.5 - slit * 20.0
    ry = 31.0 * (1.0 + 0.16 * math.cos(phi * 1.2)) - slit * 17.0
    rz = 57.0 * (1.0 + 0.07 * math.cos(theta - 0.4))
    x = math.cos(theta) * dome * rx + (left_pressure - right_pressure) * 8.0
    y = math.sin(theta) * dome * ry - slit * 24.0
    z = math.sin(phi) * rz + dome * math.sin(theta * 3.0 + v * math.tau) * 4.8
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    slit = slit_field(u, v)
    fold = fold_field(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 3.0 - v * math.tau * 1.4)
    base = (0.66 + wet * 0.12, 0.105 + wet * 0.04, 0.16 + wet * 0.045)
    dark = (0.035, 0.0, 0.009)
    crease = min(0.92, slit * 0.58 + fold * 0.48)
    return tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3)) + (1.0,)


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
    mesh = bpy.data.meshes.new("septal_valve_burrow_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="septal_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Septal Valve Burrow Body", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.modifiers.new("septal_weighted_normals", "WEIGHTED_NORMAL")
    obj.select_set(False)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("wet_septal_valve_skin")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "septal_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.14
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.1, 0.0, 0.02, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.05
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
    curve.resolution_u = 22
    curve.bevel_depth = bevel
    curve.bevel_resolution = 10
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coords in zip(spline.bezier_points, points):
        point.co = coords
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_valve_parts(dark_material: bpy.types.Material, pad_material: bpy.types.Material, root_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=90, ring_count=32, radius=1, location=(0, -36, 2))
    socket = bpy.context.object
    socket.name = "septal_deep_black_burrow"
    socket.scale = (14, 8, 32)
    socket.rotation_euler = (math.radians(0), math.radians(0), math.radians(4))
    socket.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(socket)

    cusp_specs = [
        ((-18, -36, 10), (18, 3.8, 24), -22, 7),
        ((16, -37, -4), (17, 3.6, 22), 20, -6),
        ((0, -38, -20), (15, 3.4, 16), 0, -13),
        ((2, -39, 27), (13, 3.0, 16), 4, 11),
    ]
    for index, (location, scale, angle_z, angle_x) in enumerate(cusp_specs):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=20, radius=1, location=location)
        cusp = bpy.context.object
        cusp.name = f"pressed_septal_valve_cusp_{index + 1}"
        cusp.scale = scale
        cusp.rotation_euler = (math.radians(angle_x), 0, math.radians(angle_z))
        cusp.data.materials.append(pad_material)
        bpy.ops.object.shade_smooth()
        objects.append(cusp)

    roots = [
        ("septal_left_structural_root", [(-13, -36, 5), (-30, -46, 8), (-47, -50, 10), (-62, -47, 12)], 6.4),
        ("septal_lower_structural_root", [(6, -36, -13), (18, -47, -31), (25, -49, -46), (29, -45, -61)], 5.7),
    ]
    for name, points, bevel in roots:
        objects.append(make_tube(name, points, bevel, root_material))
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
    scene.view_settings.exposure = 1.45
    scene.view_settings.gamma = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-8))
        obj.rotation_euler.rotate_axis("X", math.radians(17))
        obj.location.z += 74
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -22, 76))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(-18, -252, 138), rotation=(math.radians(62), 0, math.radians(-4)))
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
    key.data.color = (1.0, 0.42, 0.41)
    key.data.size = 145
    bpy.ops.object.light_add(type="POINT", location=(120, 72, 136))
    rim = bpy.context.object
    rim.data.energy = 2300
    rim.data.color = (0.72, 0.0, 0.08)
    rim.data.shadow_soft_size = 90
    bpy.ops.object.light_add(type="AREA", location=(0, -196, 112))
    fill = bpy.context.object
    fill.data.energy = 680
    fill.data.color = (1.0, 0.62, 0.58)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("septal_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "septal_preview_dark_backdrop"
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
    body = create_body(material_from_attribute())
    dark_material = make_material("near_black_septal_burrow", (0.004, 0.0, 0.003, 1.0), 0.68)
    pad_material = make_material("wet_pressed_valve_cusps", (0.76, 0.13, 0.19, 1.0), 0.15, 0.05)
    root_material = make_material("dark_crimson_structural_roots", (0.43, 0.012, 0.05, 1.0), 0.17, 0.05)
    objects = [body]
    objects.extend(add_valve_parts(dark_material, pad_material, root_material))
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
