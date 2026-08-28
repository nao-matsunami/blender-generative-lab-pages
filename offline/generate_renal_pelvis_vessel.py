"""Generate Renal Pelvis Vessel assets in Blender.

Mac mini workflow:
npm run job:renal

Outputs:
- exports/stl/renal-pelvis-vessel.stl
- exports/glb/renal-pelvis-vessel.glb
- renders/renal-pelvis-vessel.png
- renders/renal-pelvis-vessel-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "renal-pelvis-vessel"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 160
V_SEGMENTS = 88


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def groove_field(u: float, v: float) -> float:
    theta = u * math.tau
    waist = math.exp(-((v - 0.53) / 0.2) ** 2)
    hilum = math.exp(-(((math.cos(theta) + 1.0) / 0.34) ** 2 + ((v - 0.5) / 0.36) ** 2))
    radial = 0.0
    for offset, weight in ((0.2, 1.0), (0.38, 0.8), (0.57, 0.7), (0.76, 0.6)):
        center = (offset + 0.08 * math.sin(v * math.tau * 1.8)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        radial += max(0.0, 1.0 - distance / 0.035) ** 2.2 * weight * smoothstep(0.12, 0.72, v)
    return clamp(hilum * 1.25 + radial * 0.42 + waist * 0.18, 0.0, 1.0)


def surface_point(u: float, v: float, lift: float = 0.0) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2 + v * math.pi
    dome = max(0.0, math.cos(phi))
    rx = 48.0 * (1.0 + 0.08 * math.sin(theta * 3.0 + v * 2.0))
    ry = 30.0 * (1.0 + 0.12 * math.sin(theta * 2.0 - 0.8))
    rz = 66.0 * (1.0 + 0.04 * math.sin(theta * 4.0))

    hilum_bite = math.exp(-(((math.cos(theta) + 1.0) / 0.42) ** 2 + ((v - 0.52) / 0.28) ** 2))
    groove = groove_field(u, v)
    rx *= 1.0 - hilum_bite * 0.42 - groove * 0.035
    ry *= 1.0 - hilum_bite * 0.72 - groove * 0.055

    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    z += 6.0 * math.sin(theta + 0.4) * dome
    point = Vector((x, y, z))
    outward = point.normalized() if point.length > 0.001 else Vector((0, 0, 1))
    return point + outward * lift


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    groove = groove_field(u, v)
    theta = u * math.tau
    wet = 0.5 + 0.5 * math.sin(theta * 2.0 + v * math.tau * 2.6)
    bruise = 0.5 + 0.5 * math.sin(theta * 7.0 - v * math.tau * 2.0)
    base = (0.72 + wet * 0.14, 0.24 + wet * 0.08, 0.31 + wet * 0.08)
    dark = (0.12, 0.008, 0.035)
    vessel = (0.28, 0.012, 0.055)
    bruise_mix = max(0.0, bruise - 0.7) / 0.3 * 0.18
    groove_mix = min(0.88, groove * 0.95)
    mixed = tuple(base[i] * (1.0 - bruise_mix) + dark[i] * bruise_mix for i in range(3))
    final = tuple(mixed[i] * (1.0 - groove_mix) + vessel[i] * groove_mix for i in range(3))
    return final[0], final[1], final[2], 1.0


def create_kidney_mesh() -> bpy.types.Object:
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
    mesh = bpy.data.meshes.new("renal_pelvis_vessel_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="renal_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Renal Pelvis Vessel", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("renal_wet_skin")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = material.node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "renal_skin_color"
        material.node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.2
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.10, 0.006, 0.03, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.06
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
            bsdf.inputs["Emission Color"].default_value = (color[0] * 0.18, color[1] * 0.08, color[2] * 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def create_tube(start: Vector, end: Vector, radius: float, material: bpy.types.Material, name: str, lift: float = 0.0) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 22
    curve.bevel_depth = radius
    curve.bevel_resolution = 7
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(2)
    mid = (start + end) * 0.5 + Vector((0.0, 8.0 + lift, 6.0 * math.sin(end.z * 0.03)))
    for point, co in zip(spline.bezier_points, (start, mid, end)):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_renal_pelvis(vessel_material: bpy.types.Material, dark_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=24, radius=1, location=(-39, -6, 0))
    pelvis = bpy.context.object
    pelvis.name = "renal_dark_pelvis_cavity"
    pelvis.scale = (8.5, 3.2, 19)
    pelvis.rotation_euler = (math.radians(0), math.radians(-8), math.radians(0))
    pelvis.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(pelvis)

    root = Vector((-64, -22, -5))
    fork = Vector((-40, -13, -2))
    objects.append(create_tube(root, fork, 4.8, vessel_material, "renal_artery_root", lift=-5.0))
    targets = [
        Vector((-22, -16, 42)),
        Vector((-14, -18, 22)),
        Vector((-12, -18, -2)),
        Vector((-18, -16, -28)),
        Vector((-30, -14, -48)),
    ]
    for index, target in enumerate(targets):
        objects.append(create_tube(fork, target, 2.6 - index * 0.18, vessel_material, f"renal_branch_{index:02d}", lift=-3.0 + index * 0.6))
    return objects


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "MESH":
        bpy.ops.object.shade_smooth()
        weighted = obj.modifiers.new("renal_weighted_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.42
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(12))
        obj.rotation_euler.rotate_axis("X", math.radians(10))
        obj.location.z += 72

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-14, -2, 72))
    target = bpy.context.object
    target.name = "renal_camera_target"

    bpy.ops.object.camera_add(location=(-118, -212, 112), rotation=(math.radians(66), 0, math.radians(-18)))
    camera = bpy.context.object
    camera.name = "renal_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-128, -120, 184))
    key = bpy.context.object
    key.name = "renal_warm_key"
    key.data.energy = 5200
    key.data.color = (1.0, 0.56, 0.52)
    key.data.size = 160

    bpy.ops.object.light_add(type="POINT", location=(108, 86, 132))
    rim = bpy.context.object
    rim.name = "renal_dark_red_rim"
    rim.data.energy = 1650
    rim.data.color = (0.72, 0.03, 0.12)
    rim.data.shadow_soft_size = 92

    bpy.ops.object.light_add(type="AREA", location=(0, -180, 96))
    fill = bpy.context.object
    fill.name = "renal_soft_front"
    fill.data.energy = 720
    fill.data.color = (1.0, 0.64, 0.62)
    fill.data.size = 220


def add_preview_backdrop() -> None:
    material = make_material("renal_preview_dark_backdrop", (0.007, 0.001, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "renal_preview_dark_backdrop"
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
    skin_material = material_from_attribute()
    vessel_material = make_material("renal_raised_vessels", (0.34, 0.014, 0.06, 1.0), 0.19)
    dark_material = make_material("renal_internal_dark", (0.018, 0.001, 0.008, 1.0), 0.5)
    kidney = create_kidney_mesh()
    kidney.data.materials.append(skin_material)
    objects = [kidney]
    objects.extend(add_renal_pelvis(vessel_material, dark_material))
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
