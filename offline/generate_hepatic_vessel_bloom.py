"""Generate Hepatic Vessel Bloom assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:hepatic

Outputs:
- exports/stl/hepatic-vessel-bloom.stl
- exports/glb/hepatic-vessel-bloom.glb
- renders/hepatic-vessel-bloom.png
- renders/hepatic-vessel-bloom-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "hepatic-vessel-bloom.stl"
GLB_PATH = ROOT / "exports" / "glb" / "hepatic-vessel-bloom.glb"
RENDER_PATH = ROOT / "renders" / "hepatic-vessel-bloom.png"
PREVIEW_PATH = ROOT / "renders" / "hepatic-vessel-bloom-preview.png"

U_SEGMENTS = 168
V_SEGMENTS = 92


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def vessel_field(u: float, v: float) -> float:
    field = 0.0
    branches = (
        (0.16, 0.24, 0.18, 0.74, 1.0),
        (0.38, 0.32, 0.56, 0.88, 0.72),
        (0.58, 0.22, 0.5, 0.76, 0.86),
        (0.78, 0.36, 0.3, 0.82, 0.65),
        (0.26, 0.58, 0.76, 0.7, 0.55),
    )
    for u0, v0, drift, length, weight in branches:
        center = (u0 + drift * (v - v0) + 0.08 * math.sin(v * math.tau * 1.7)) % 1.0
        along = smoothstep(v0 - 0.08, v0 + length, v) * (1.0 - smoothstep(v0 + length * 0.72, v0 + length, v))
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        width = 0.038 + 0.02 * (1.0 - along)
        ridge = max(0.0, 1.0 - distance / width) ** 1.7
        field += ridge * along * weight
    return min(1.0, field)


def organ_radius(u: float, v: float) -> tuple[float, float, float]:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = math.cos(phi)
    asym = 1.0 + 0.18 * math.sin(theta * 2.0 + 0.4) * (dome ** 0.8)
    left_lobe = 1.0 + 0.28 * smoothstep(-0.95, -0.2, math.cos(theta)) * smoothstep(0.08, 0.75, v)
    notch = 1.0 - 0.22 * smoothstep(0.08, 0.55, math.sin(theta + 0.7)) * smoothstep(0.18, 0.72, v)
    vessel = vessel_field(u, v)
    wrinkle = 1.0 + 0.04 * math.sin(theta * 9.0 + v * math.tau * 2.0)
    rx = 58.0 * asym * left_lobe * notch * wrinkle + vessel * 9.5 * (dome ** 0.7)
    ry = 40.0 * (1.0 + 0.14 * math.sin(theta * 3.0 - 0.9) * dome) * notch + vessel * 6.2
    rz = 32.0 * (1.0 + 0.12 * math.sin(theta * 2.0 + 1.4) * dome)
    return rx, ry, rz


def surface_point(u: float, v: float, lift: float = 0.0) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = math.cos(phi)
    rx, ry, rz = organ_radius(u, v)
    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    z += 5.0 * math.sin(theta * 2.0 - 0.4) * (dome ** 1.2)
    x += 9.0 * smoothstep(0.18, 0.74, v) * math.sin(theta - 1.2)
    point = Vector((x, y, z))
    outward = point.normalized() if point.length > 0.001 else Vector((0.0, 0.0, 1.0))
    return point + outward * lift


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    vessel = vessel_field(u, v)
    theta = u * math.tau
    wet = 0.5 + 0.5 * math.sin(theta * 3.0 + v * math.tau * 2.0)
    bruise = 0.5 + 0.5 * math.sin(theta * 7.0 - v * math.tau * 3.0)
    base = (0.66 + wet * 0.16, 0.16 + wet * 0.06, 0.23 + wet * 0.06)
    dark = (0.11, 0.006, 0.035)
    vein = (0.24, 0.008, 0.035)
    pale = (0.98, 0.42, 0.38)
    vessel_mix = min(0.96, vessel * 1.08)
    bruise_mix = max(0.0, bruise - 0.68) / 0.32 * 0.2
    mixed = (
        base[0] * (1.0 - bruise_mix) + dark[0] * bruise_mix,
        base[1] * (1.0 - bruise_mix) + dark[1] * bruise_mix,
        base[2] * (1.0 - bruise_mix) + dark[2] * bruise_mix,
    )
    color = (
        mixed[0] * (1.0 - vessel_mix) + vein[0] * vessel_mix,
        mixed[1] * (1.0 - vessel_mix) + vein[1] * vessel_mix,
        mixed[2] * (1.0 - vessel_mix) + vein[2] * vessel_mix,
    )
    highlight = smoothstep(0.72, 1.0, math.sin(theta - 0.8)) * smoothstep(0.18, 0.84, v) * 0.1
    return (
        color[0] * (1.0 - highlight) + pale[0] * highlight,
        color[1] * (1.0 - highlight) + pale[1] * highlight,
        color[2] * (1.0 - highlight) + pale[2] * highlight,
        1.0,
    )


def create_organ_mesh() -> bpy.types.Object:
    vertices = []
    colors = []
    faces = []

    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        phi = -math.pi / 2.0 + v * math.pi
        dome = math.cos(phi)
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            theta = u * math.tau
            rx, ry, rz = organ_radius(u, v)
            vertices.append(tuple(surface_point(u, v)))
            colors.append(color_at(u, v))

    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("hepatic_vessel_bloom_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="hepatic_vessel_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Hepatic Vessel Bloom", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_vessel_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    paths = (
        (0.12, 0.28, 0.27, 0.76, 0.28, 2.6),
        (0.23, 0.24, 0.58, 0.82, -0.18, 2.1),
        (0.38, 0.34, 0.72, 0.7, 0.14, 1.8),
        (0.55, 0.22, 0.86, 0.78, -0.22, 2.2),
        (0.72, 0.38, 0.34, 0.75, 0.2, 1.7),
    )
    sides = 12
    samples = 76
    for u0, v0, u1, v1, sway, tube_radius_value in paths:
        start_index = len(vertices)
        points = []
        for i in range(samples):
            t = i / (samples - 1)
            ease = smoothstep(0.0, 1.0, t)
            u = (u0 * (1.0 - ease) + u1 * ease + sway * math.sin(t * math.pi) * 0.08) % 1.0
            v = v0 * (1.0 - ease) + v1 * ease
            points.append(surface_point(u, v, lift=3.0))
        for i, point in enumerate(points):
            prev_point = points[max(0, i - 1)]
            next_point = points[min(samples - 1, i + 1)]
            tangent = (next_point - prev_point).normalized()
            outward = point.normalized() if point.length > 0.001 else Vector((0.0, 0.0, 1.0))
            side_axis = tangent.cross(outward)
            if side_axis.length < 0.001:
                side_axis = Vector((1.0, 0.0, 0.0))
            side_axis.normalize()
            up_axis = side_axis.cross(tangent).normalized()
            taper = 0.55 + 0.45 * math.sin(t * math.pi)
            radius = tube_radius_value * taper
            for j in range(sides):
                angle = j / sides * math.tau
                vertices.append(tuple(point + (side_axis * math.cos(angle) + up_axis * math.sin(angle)) * radius))
        for i in range(samples - 1):
            for j in range(sides):
                a = start_index + i * sides + j
                b = start_index + i * sides + ((j + 1) % sides)
                c = start_index + (i + 1) * sides + ((j + 1) % sides)
                d = start_index + (i + 1) * sides + j
                faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("hepatic_raised_vessel_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Hepatic Raised Vessels", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("hepatic_vessel_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "hepatic_vessel_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.13, 0.01, 0.04, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def create_vessel_material() -> bpy.types.Material:
    material = bpy.data.materials.new("hepatic_raised_vessel_dark")
    material.diffuse_color = (0.22, 0.006, 0.03, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.22, 0.006, 0.03, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.2
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.08, 0.0, 0.02, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.06
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    weighted = obj.modifiers.new("weighted_hepatic_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.38
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 74
    obj.rotation_euler[0] = math.radians(18)
    obj.rotation_euler[1] = math.radians(-12)
    obj.rotation_euler[2] = math.radians(-22)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 74))
    target = bpy.context.object
    target.name = "hepatic_vessel_target"

    bpy.ops.object.camera_add(location=(0, -275, 122), rotation=(math.radians(70), 0, 0))
    camera = bpy.context.object
    camera.name = "hepatic_vessel_camera"
    camera.data.lens = 54
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-132, -130, 178))
    key = bpy.context.object
    key.name = "hepatic_warm_key"
    key.data.energy = 4300
    key.data.color = (1.0, 0.5, 0.5)
    key.data.size = 145

    bpy.ops.object.light_add(type="POINT", location=(132, 80, 128))
    rim = bpy.context.object
    rim.name = "hepatic_dark_red_rim"
    rim.data.color = (0.72, 0.04, 0.14)
    rim.data.energy = 1450
    rim.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(0, -218, 110))
    front = bpy.context.object
    front.name = "hepatic_soft_fill"
    front.data.energy = 760
    front.data.color = (1.0, 0.68, 0.62)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("hepatic_preview_dark_backdrop")
    material.diffuse_color = (0.008, 0.001, 0.004, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.008, 0.001, 0.004, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "hepatic_preview_dark_backdrop"
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
        world.color = (0.008, 0.001, 0.004)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    organ = create_organ_mesh()
    organ.data.materials.append(create_material())
    vessels = create_vessel_mesh()
    vessels.data.materials.append(create_vessel_material())
    prepare_object(organ)
    prepare_object(vessels)
    setup_scene(organ)
    vessels.location = organ.location.copy()
    vessels.rotation_euler = organ.rotation_euler.copy()
    export_stl([organ, vessels])
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
