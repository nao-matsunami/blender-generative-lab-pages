"""Generate Renal Hilum Cleft assets in Blender.

Mac mini workflow:
npm run job:renalhilum
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "renal-hilum-cleft"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"
U_SEGMENTS = 152
V_SEGMENTS = 80


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def cleft_field(u: float, v: float) -> float:
    theta = u * math.tau
    front = smoothstep(0.08, 0.96, 0.5 + 0.5 * math.sin(theta - 0.1))
    middle = math.exp(-((v - 0.5) / 0.23) ** 2)
    return front * middle


def ridge_field(u: float, v: float) -> float:
    theta = u * math.tau
    cleft = cleft_field(u, v)
    lobes = 0.0
    for index in range(7):
        center = index / 7.0 + 0.045 * math.sin(v * math.tau * 2.0)
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        lobes += max(0.0, 1.0 - distance / 0.075) ** 2.4
    wet = 0.5 + 0.5 * math.sin(theta * 3.0 + v * math.tau * 1.5)
    return min(1.0, lobes * 0.36 + cleft * 0.42 + wet * 0.12)


def surface_point(u: float, v: float) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + (0.018 + v * 0.964) * math.pi
    dome = max(0.0, math.cos(phi))
    cleft = cleft_field(u, v)
    ridge = ridge_field(u, v)
    notch = math.exp(-((v - 0.5) / 0.16) ** 2) * (0.5 + 0.5 * math.sin(theta - 0.18))
    rx = 44.0 * (1.0 + 0.15 * math.sin(theta + 0.7)) + ridge * 6.5 - cleft * 19.0
    ry = 29.0 * (1.0 + 0.08 * math.cos(phi * 1.4)) - cleft * 21.0
    rz = 60.0 * (1.0 + 0.08 * math.cos(theta * 2.0))
    x = math.cos(theta) * dome * rx + 6.0 * math.sin(phi * 1.7)
    y = math.sin(theta) * dome * ry - notch * 22.0
    z = math.sin(phi) * rz + dome * math.sin(theta * 2.0 - 0.4) * 4.0
    return Vector((x, y, z))


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    cleft = cleft_field(u, v)
    ridge = ridge_field(u, v)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 2.4 + v * math.tau * 2.2)
    base = (0.7 + wet * 0.1, 0.12 + wet * 0.05, 0.18 + wet * 0.045)
    dark = (0.035, 0.0, 0.01)
    crease = min(0.9, cleft * 0.62 + ridge * 0.38)
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


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("wet_renal_lobe_skin")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attr = material.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "renal_skin_color"
        material.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.15
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.1, 0.0, 0.02, 1.0)
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
    mesh = bpy.data.meshes.new("renal_hilum_cleft_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="renal_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Renal Hilum Cleft Body", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.modifiers.new("renal_weighted_normals", "WEIGHTED_NORMAL")
    obj.select_set(False)
    return obj


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


def add_hilum_parts(dark_material: bpy.types.Material, lip_material: bpy.types.Material, tube_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=80, ring_count=28, radius=1, location=(0, -35, 1))
    socket = bpy.context.object
    socket.name = "renal_black_hilum_socket"
    socket.scale = (18, 8, 30)
    socket.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(socket)
    pads = [
        ((-16, -35, 10), (17, 3.6, 17), -18),
        ((17, -36, -8), (16, 3.4, 19), 20),
        ((0, -38, 26), (13, 3.0, 13), 5),
        ((-2, -38, -25), (13, 3.0, 14), -5),
    ]
    for index, (location, scale, angle) in enumerate(pads):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=18, radius=1, location=location)
        pad = bpy.context.object
        pad.name = f"renal_compressed_hilum_lip_{index + 1}"
        pad.scale = scale
        pad.rotation_euler = (math.radians(4), 0, math.radians(angle))
        pad.data.materials.append(lip_material)
        bpy.ops.object.shade_smooth()
        objects.append(pad)
    objects.append(make_tube("renal_structural_ureter_root", [(5, -35, -17), (14, -49, -35), (19, -54, -51), (23, -49, -67)], 5.8, tube_material))
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
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-11))
        obj.rotation_euler.rotate_axis("X", math.radians(18))
        obj.location.z += 74
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -20, 76))
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
    mat = make_material("renal_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "renal_preview_dark_backdrop"
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
    dark_material = make_material("near_black_renal_hilum", (0.004, 0.0, 0.003, 1.0), 0.68)
    lip_material = make_material("compressed_renal_hilum_lips", (0.76, 0.13, 0.19, 1.0), 0.15, 0.05)
    tube_material = make_material("dark_crimson_ureter_root", (0.42, 0.012, 0.05, 1.0), 0.17, 0.05)
    objects = [body]
    objects.extend(add_hilum_parts(dark_material, lip_material, tube_material))
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
