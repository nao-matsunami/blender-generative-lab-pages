"""Generate Pericardial Root Adhesion assets in Blender.

Mac mini workflow:
npm run job:pericardial
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "pericardial-root-adhesion"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 160
V_SEGMENTS = 84


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def root_field(u: float, v: float) -> float:
    theta = u * math.tau
    front = smoothstep(0.0, 0.95, 0.5 + 0.5 * math.sin(theta - 0.05))
    belt = math.exp(-((v - 0.5) / 0.2) ** 2)
    return front * belt


def fold_field(u: float, v: float) -> float:
    theta = u * math.tau
    root = root_field(u, v)
    rib = 0.0
    for index in range(13):
        center = (index / 13.0 + 0.18 * v + 0.02 * math.sin(v * math.tau * 1.5)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        rib += max(0.0, 1.0 - distance / 0.03) ** 2.2
    broad = 0.5 + 0.5 * math.sin(theta * 2.0 - v * math.tau * 1.4)
    return min(1.0, root * 0.52 + rib * 0.28 + broad * 0.13)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + (0.012 + v * 0.976) * math.pi
    dome = max(0.0, math.cos(phi))
    root = root_field(u, v)
    fold = fold_field(u, v)
    asym = 1.0 + 0.12 * math.sin(theta + 0.4) + 0.09 * math.cos(phi * 1.6)
    rx = 51.0 * asym * (1.0 - 0.28 * root) + fold * 5.0
    ry = 36.0 * (1.0 + 0.08 * math.cos(theta * 2.0)) - root * 19.0
    rz = 55.0 * (1.0 + 0.08 * math.sin(theta - 0.35))
    x = math.cos(theta) * dome * rx + 4.0 * math.sin(phi * 1.5)
    y = math.sin(theta) * dome * ry - root * 16.0
    z = math.sin(phi) * rz + dome * math.sin(theta * 2.0 - 0.75) * 5.0
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = fold_field(u, v)
    root = root_field(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 2.8 + v * math.tau * 2.0)
    base = (0.67 + wet * 0.13, 0.13 + wet * 0.055, 0.19 + wet * 0.05)
    dark = (0.065, 0.001, 0.014)
    crease = min(0.9, fold * 0.72 + root * 0.22)
    return tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3)) + (1.0,)


def create_chamber_mesh(material: bpy.types.Material) -> bpy.types.Object:
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
    mesh = bpy.data.meshes.new("pericardial_adhesion_chamber_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="pericardial_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Pericardial Root Adhesion Chamber", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    weighted = obj.modifiers.new("pericardial_weighted_normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    obj.select_set(False)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("wet_pericardial_chamber")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "pericardial_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.16
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.12, 0.002, 0.025, 1.0)
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
    curve.resolution_u = 24
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


def add_root_parts(dark_material: bpy.types.Material, tube_material: bpy.types.Material, adhesion_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=80, ring_count=30, radius=1, location=(0, -36, 2))
    socket = bpy.context.object
    socket.name = "pericardial_black_socket"
    socket.scale = (25, 10, 25)
    socket.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(socket)

    tube_specs = [
        ("pericardial_upper_root", [(-8, -36, 5), (-4, -49, 24), (2, -57, 43), (5, -62, 57)], 7.2),
        ("pericardial_left_root", [(-7, -36, 1), (-22, -45, 8), (-34, -49, 11), (-45, -49, 10)], 6.2),
        ("pericardial_right_root", [(7, -36, 0), (21, -45, -4), (34, -49, -8), (45, -49, -11)], 6.0),
    ]
    for name, points, bevel in tube_specs:
        objects.append(make_tube(name, points, bevel, tube_material))

    pads = [
        ((-15, -36, 3), (14, 4, 10), -24),
        ((14, -36, -1), (14, 4, 10), 18),
        ((0, -39, 17), (13, 4, 10), 78),
        ((-1, -38, -13), (12, 3.5, 8), -3),
    ]
    for index, (location, scale, angle) in enumerate(pads):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=18, radius=1, location=location)
        pad = bpy.context.object
        pad.name = f"pericardial_pressed_adhesion_pad_{index + 1}"
        pad.scale = scale
        pad.rotation_euler = (math.radians(4), 0, math.radians(angle))
        pad.data.materials.append(adhesion_material)
        bpy.ops.object.shade_smooth()
        objects.append(pad)
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
    scene.view_settings.gamma = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-12))
        obj.rotation_euler.rotate_axis("X", math.radians(21))
        obj.location.z += 73
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -20, 76))
    target = bpy.context.object
    target.name = "pericardial_camera_target"
    bpy.ops.object.camera_add(location=(-20, -256, 136), rotation=(math.radians(62), 0, math.radians(-5)))
    camera = bpy.context.object
    camera.data.lens = 55
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-128, -132, 196))
    key = bpy.context.object
    key.data.energy = 6800
    key.data.color = (1.0, 0.48, 0.45)
    key.data.size = 150
    bpy.ops.object.light_add(type="POINT", location=(128, 74, 136))
    rim = bpy.context.object
    rim.data.energy = 2350
    rim.data.color = (0.82, 0.02, 0.12)
    rim.data.shadow_soft_size = 86
    bpy.ops.object.light_add(type="AREA", location=(0, -198, 106))
    fill = bpy.context.object
    fill.data.energy = 700
    fill.data.color = (1.0, 0.62, 0.58)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("pericardial_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "pericardial_preview_dark_backdrop"
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
    chamber = create_chamber_mesh(material_from_attribute())
    dark_material = make_material("near_black_pericardial_socket", (0.005, 0.0, 0.003, 1.0), 0.62)
    tube_material = make_material("thick_dark_crimson_adhered_roots", (0.46, 0.024, 0.07, 1.0), 0.17, 0.05)
    adhesion_material = make_material("compressed_pink_adhesion_pads", (0.75, 0.14, 0.20, 1.0), 0.18, 0.04)
    objects = [chamber]
    objects.extend(add_root_parts(dark_material, tube_material, adhesion_material))
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
