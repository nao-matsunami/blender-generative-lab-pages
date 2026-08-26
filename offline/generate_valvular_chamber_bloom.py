"""Generate Valvular Chamber Bloom assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:valvular

Outputs:
- exports/stl/valvular-chamber-bloom.stl
- exports/glb/valvular-chamber-bloom.glb
- renders/valvular-chamber-bloom.png
- renders/valvular-chamber-bloom-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "valvular-chamber-bloom.stl"
GLB_PATH = ROOT / "exports" / "glb" / "valvular-chamber-bloom.glb"
RENDER_PATH = ROOT / "renders" / "valvular-chamber-bloom.png"
PREVIEW_PATH = ROOT / "renders" / "valvular-chamber-bloom-preview.png"

U_SEGMENTS = 156
V_SEGMENTS = 92


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def valve_field(u: float, v: float) -> float:
    theta = u * math.tau
    ring = smoothstep(0.47, 0.58, v) * (1.0 - smoothstep(0.72, 0.88, v))
    lobes = max(0.0, math.cos(theta * 4.0 - 0.45)) ** 4.0
    split = max(0.0, math.cos(theta * 8.0 + 0.2)) ** 2.0
    return min(1.0, ring * (lobes * 0.9 + split * 0.22))


def vessel_groove(u: float, v: float) -> float:
    field = 0.0
    for u0, v0, drift, length, width, weight in (
        (0.08, 0.08, 0.22, 0.68, 0.038, 1.0),
        (0.36, 0.12, -0.16, 0.76, 0.034, 0.8),
        (0.6, 0.18, 0.34, 0.62, 0.032, 0.85),
        (0.82, 0.1, -0.28, 0.7, 0.036, 0.72),
    ):
        center = (u0 + drift * (v - v0) + 0.055 * math.sin(v * math.tau * 1.6)) % 1.0
        along = smoothstep(v0, v0 + 0.16, v) * (1.0 - smoothstep(v0 + length * 0.72, v0 + length, v))
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        field += max(0.0, 1.0 - distance / width) ** 2.0 * along * weight
    return min(1.0, field)


def chamber_point(u: float, v: float, lift: float = 0.0) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = max(0.0, math.cos(phi))
    lower = 1.0 - smoothstep(0.0, 0.24, v)
    upper = smoothstep(0.58, 0.96, v)
    side_bulge = 1.0 + 0.2 * math.sin(theta * 2.0 - 0.7) * (dome ** 0.9)
    cleft = 1.0 - 0.22 * max(0.0, math.cos(theta - 1.2)) ** 3.0 * smoothstep(0.18, 0.72, v)
    valve = valve_field(u, v)
    groove = vessel_groove(u, v)
    rx = 43.0 * side_bulge * cleft + valve * 10.0 - groove * 3.2
    ry = 34.0 * (1.0 + 0.16 * math.sin(theta * 3.0 + 0.4) * dome) + valve * 5.5 - groove * 2.0
    rz = 50.0 * (1.0 - lower * 0.28 + upper * 0.1)
    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    z += valve * 5.8 - lower * 10.0
    x += 8.0 * smoothstep(0.15, 0.72, v) * math.sin(theta + 0.7)
    point = Vector((x, y, z))
    outward = point.normalized() if point.length > 0.001 else Vector((0.0, 0.0, 1.0))
    return point + outward * lift


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    theta = u * math.tau
    valve = valve_field(u, v)
    groove = vessel_groove(u, v)
    wet = 0.5 + 0.5 * math.sin(theta * 3.0 + v * math.tau * 1.7)
    base = (0.68 + wet * 0.18, 0.17 + wet * 0.06, 0.24 + wet * 0.05)
    dark = (0.08, 0.004, 0.025)
    valve_pale = (0.96, 0.42, 0.38)
    groove_dark = min(0.88, groove * 0.74)
    valve_mix = valve * 0.34
    mixed = (
        base[0] * (1.0 - valve_mix) + valve_pale[0] * valve_mix,
        base[1] * (1.0 - valve_mix) + valve_pale[1] * valve_mix,
        base[2] * (1.0 - valve_mix) + valve_pale[2] * valve_mix,
    )
    return (
        mixed[0] * (1.0 - groove_dark) + dark[0] * groove_dark,
        mixed[1] * (1.0 - groove_dark) + dark[1] * groove_dark,
        mixed[2] * (1.0 - groove_dark) + dark[2] * groove_dark,
        1.0,
    )


def create_chamber_mesh() -> bpy.types.Object:
    vertices = []
    colors = []
    faces = []
    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            vertices.append(tuple(chamber_point(u, v)))
            colors.append(color_at(u, v))

    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("valvular_chamber_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="valvular_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Valvular Chamber Bloom", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_root_vessels() -> bpy.types.Object:
    vertices = []
    faces = []
    paths = (
        ((0, -6, 42), (-18, -18, 66), (-32, -34, 74), 4.4),
        ((0, -4, 43), (17, -14, 65), (32, -30, 72), 4.0),
        ((-5, 2, 40), (-10, 22, 60), (-24, 36, 66), 3.2),
    )
    sides = 14
    samples = 58
    for start, mid, end, radius_value in paths:
        start_index = len(vertices)
        p0 = Vector(start)
        p1 = Vector(mid)
        p2 = Vector(end)
        for i in range(samples):
            t = i / (samples - 1)
            point = p0 * ((1.0 - t) ** 2) + p1 * (2.0 * (1.0 - t) * t) + p2 * (t ** 2)
            tangent = (p1 - p0) * (2.0 * (1.0 - t)) + (p2 - p1) * (2.0 * t)
            tangent.normalize()
            side_axis = tangent.cross(Vector((0.0, 0.0, 1.0)))
            if side_axis.length < 0.001:
                side_axis = Vector((1.0, 0.0, 0.0))
            side_axis.normalize()
            up_axis = side_axis.cross(tangent).normalized()
            taper = 0.62 + 0.38 * math.sin(t * math.pi)
            radius = radius_value * taper
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
    mesh = bpy.data.meshes.new("valvular_root_vessels_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Valvular Root Vessels", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_valve_petals() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []
    radial_steps = 16
    width_steps = 9
    for petal in range(4):
        base_angle = petal / 4.0 * math.tau + 0.34
        start_index = len(vertices)
        for i in range(radial_steps + 1):
            r = i / radial_steps
            for j in range(width_steps):
                w = (j / (width_steps - 1) - 0.5)
                angle = base_angle + w * (0.58 - r * 0.22)
                length = 8.0 + r * 29.0
                curl = math.sin(r * math.pi) * 6.0
                x = math.cos(angle) * length
                y = math.sin(angle) * length * 0.78 - 4.0
                z = 35.0 + r * 13.0 - curl
                vertices.append((x, y, z))
                edge = abs(w) * 2.0
                dark = smoothstep(0.0, 0.7, r) * (1.0 - edge * 0.3)
                colors.append((0.9 - dark * 0.42, 0.28 - dark * 0.22, 0.31 - dark * 0.24, 1.0))
        for i in range(radial_steps):
            for j in range(width_steps - 1):
                a = start_index + i * width_steps + j
                b = start_index + i * width_steps + j + 1
                c = start_index + (i + 1) * width_steps + j + 1
                d = start_index + (i + 1) * width_steps + j
                faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("valvular_petal_membrane_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="valvular_petal_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Valvular Petal Membranes", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("valvular_chamber_wet_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "valvular_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.22
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.12, 0.006, 0.035, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def vessel_material() -> bpy.types.Material:
    material = bpy.data.materials.new("valvular_root_vessel_dark")
    material.diffuse_color = (0.18, 0.004, 0.032, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.18, 0.004, 0.032, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.2
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.06, 0.0, 0.018, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.06
    return material


def petal_material() -> bpy.types.Material:
    material = bpy.data.materials.new("valvular_petal_wet_membrane")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "valvular_petal_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.92
    material.blend_method = "BLEND"
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    weighted = obj.modifiers.new("weighted_valvular_normals", "WEIGHTED_NORMAL")
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
        obj.location.z = 66
        obj.rotation_euler[0] = math.radians(18)
        obj.rotation_euler[1] = math.radians(-12)
        obj.rotation_euler[2] = math.radians(18)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 74))
    target = bpy.context.object
    target.name = "valvular_chamber_target"

    bpy.ops.object.camera_add(location=(0, -286, 126), rotation=(math.radians(69), 0, 0))
    camera = bpy.context.object
    camera.name = "valvular_chamber_camera"
    camera.data.lens = 54
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-136, -130, 182))
    key = bpy.context.object
    key.name = "valvular_warm_key"
    key.data.energy = 4550
    key.data.color = (1.0, 0.5, 0.5)
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(132, 74, 132))
    rim = bpy.context.object
    rim.name = "valvular_dark_red_rim"
    rim.data.color = (0.72, 0.04, 0.14)
    rim.data.energy = 1600
    rim.data.shadow_soft_size = 85

    bpy.ops.object.light_add(type="AREA", location=(0, -220, 112))
    front = bpy.context.object
    front.name = "valvular_soft_fill"
    front.data.energy = 780
    front.data.color = (1.0, 0.68, 0.62)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("valvular_preview_dark_backdrop")
    material.diffuse_color = (0.008, 0.001, 0.004, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.008, 0.001, 0.004, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "valvular_preview_dark_backdrop"
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
    chamber = create_chamber_mesh()
    petals = create_valve_petals()
    vessels = create_root_vessels()
    chamber.data.materials.append(material_from_attribute())
    petals.data.materials.append(petal_material())
    vessels.data.materials.append(vessel_material())
    prepare_object(chamber)
    prepare_object(petals)
    prepare_object(vessels)
    objects = [chamber, petals, vessels]
    setup_scene(objects)
    export_stl(objects)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
