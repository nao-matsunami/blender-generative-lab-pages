"""Generate Peristaltic Coil Womb assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:coilwomb

Outputs:
- exports/stl/peristaltic-coil-womb.stl
- exports/glb/peristaltic-coil-womb.glb
- renders/peristaltic-coil-womb.png
- renders/peristaltic-coil-womb-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "peristaltic-coil-womb.stl"
GLB_PATH = ROOT / "exports" / "glb" / "peristaltic-coil-womb.glb"
RENDER_PATH = ROOT / "renders" / "peristaltic-coil-womb.png"
PREVIEW_PATH = ROOT / "renders" / "peristaltic-coil-womb-preview.png"

RINGS = 220
SIDES = 26


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def center_at(t: float) -> Vector:
    angle = t * math.tau
    orbit = 37.0 + 6.0 * math.sin(angle * 3.0 + 0.8) + 3.5 * math.sin(angle * 7.0)
    x = math.cos(angle) * orbit
    y = math.sin(angle) * orbit * 0.82
    z = 18.0 * math.sin(angle * 2.0 + 0.4) + 7.0 * math.sin(angle * 5.0)
    return Vector((x, y, z))


def tube_radius(t: float, s: float) -> float:
    angle = t * math.tau
    pulse = 0.5 + 0.5 * math.sin(angle * 9.0 + 0.7)
    lobe = 0.5 + 0.5 * math.sin(s * math.tau * 3.0 + angle * 2.4)
    vein = 0.5 + 0.5 * math.sin(s * math.tau * 7.0 - angle * 4.0)
    return 9.0 + 2.7 * pulse + 0.9 * lobe + 0.5 * vein


def color_at(t: float, s: float) -> tuple[float, float, float, float]:
    angle = t * math.tau
    pulse = 0.5 + 0.5 * math.sin(angle * 9.0 + 0.7)
    stripe = 0.5 + 0.5 * math.sin(s * math.tau * 5.0 - angle * 6.0)
    bruise = max(0.0, stripe - 0.62) / 0.38
    base = (0.72 + pulse * 0.15, 0.2 + pulse * 0.05, 0.27 + pulse * 0.04)
    dark = (0.18, 0.018, 0.06)
    pale = (1.0, 0.48, 0.42)
    rim = max(0.0, math.sin(s * math.tau + 0.35))
    mixed = (
        base[0] * (1.0 - bruise) + dark[0] * bruise,
        base[1] * (1.0 - bruise) + dark[1] * bruise,
        base[2] * (1.0 - bruise) + dark[2] * bruise,
    )
    return (
        mixed[0] * (1.0 - rim * 0.12) + pale[0] * rim * 0.12,
        mixed[1] * (1.0 - rim * 0.12) + pale[1] * rim * 0.12,
        mixed[2] * (1.0 - rim * 0.12) + pale[2] * rim * 0.12,
        1.0,
    )


def create_coil_mesh() -> bpy.types.Object:
    centers = [center_at(i / RINGS) for i in range(RINGS)]
    vertices = []
    colors = []
    faces = []

    for i, center in enumerate(centers):
        t = i / RINGS
        prev_center = centers[(i - 1) % RINGS]
        next_center = centers[(i + 1) % RINGS]
        tangent = (next_center - prev_center).normalized()
        radial = Vector((center.x, center.y, 0.0))
        if radial.length < 0.001:
            radial = Vector((1.0, 0.0, 0.0))
        normal = radial.normalized()
        binormal = tangent.cross(normal).normalized()
        normal = binormal.cross(tangent).normalized()
        for j in range(SIDES):
            s = j / SIDES
            tube_angle = s * math.tau
            radius = tube_radius(t, s)
            wrinkle = 1.0 + 0.035 * math.sin(t * math.tau * 29.0 + s * math.tau * 3.0)
            point = center + (normal * math.cos(tube_angle) + binormal * math.sin(tube_angle)) * radius * wrinkle
            vertices.append(tuple(point))
            colors.append(color_at(t, s))

    for i in range(RINGS):
        next_i = (i + 1) % RINGS
        for j in range(SIDES):
            a = i * SIDES + j
            b = i * SIDES + ((j + 1) % SIDES)
            c = next_i * SIDES + ((j + 1) % SIDES)
            d = next_i * SIDES + j
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("peristaltic_coil_womb_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="coil_womb_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Peristaltic Coil Womb", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("coil_womb_wet_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "coil_womb_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.22
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.14, 0.014, 0.045, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new("soft_peristaltic_skin", "BEVEL")
    bevel.width = 0.12
    bevel.segments = 1
    weighted = obj.modifiers.new("weighted_coil_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.36
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 74
    obj.rotation_euler[0] = math.radians(56)
    obj.rotation_euler[1] = math.radians(-8)
    obj.rotation_euler[2] = math.radians(-28)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 74))
    target = bpy.context.object
    target.name = "coil_womb_target"

    bpy.ops.object.camera_add(location=(0, -265, 142), rotation=(math.radians(66), 0, 0))
    camera = bpy.context.object
    camera.name = "coil_womb_camera"
    camera.data.lens = 58
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-124, -128, 178))
    key = bpy.context.object
    key.name = "coil_womb_rose_key"
    key.data.energy = 4100
    key.data.color = (1.0, 0.5, 0.52)
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(130, 72, 132))
    rim = bpy.context.object
    rim.name = "coil_womb_blood_rim"
    rim.data.color = (0.78, 0.06, 0.18)
    rim.data.energy = 1700
    rim.data.shadow_soft_size = 85

    bpy.ops.object.light_add(type="AREA", location=(0, -210, 112))
    front = bpy.context.object
    front.name = "coil_womb_soft_fill"
    front.data.energy = 820
    front.data.color = (1.0, 0.7, 0.66)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("coil_womb_preview_dark_backdrop")
    material.diffuse_color = (0.01, 0.002, 0.006, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.01, 0.002, 0.006, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "coil_womb_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(material)


def export_stl(obj: bpy.types.Object) -> None:
    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
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
        world.color = (0.01, 0.002, 0.006)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    coil = create_coil_mesh()
    coil.data.materials.append(create_material())
    prepare_object(coil)
    setup_scene(coil)
    export_stl(coil)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
