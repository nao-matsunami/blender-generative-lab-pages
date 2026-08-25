"""Generate Adhesion Gut Wreath assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:adhesion

Outputs:
- exports/stl/adhesion-gut-wreath.stl
- exports/glb/adhesion-gut-wreath.glb
- renders/adhesion-gut-wreath.png
- renders/adhesion-gut-wreath-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "adhesion-gut-wreath.stl"
GLB_PATH = ROOT / "exports" / "glb" / "adhesion-gut-wreath.glb"
RENDER_PATH = ROOT / "renders" / "adhesion-gut-wreath.png"
PREVIEW_PATH = ROOT / "renders" / "adhesion-gut-wreath-preview.png"

RINGS = 248
SIDES = 30


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def center_at(t: float) -> Vector:
    angle = t * math.tau
    orbit = 35.0 + 7.5 * math.sin(angle * 3.0 + 0.6) + 4.0 * math.sin(angle * 6.0 - 0.4)
    x = math.cos(angle) * orbit + 7.0 * math.sin(angle * 2.0)
    y = math.sin(angle) * orbit * 0.76 + 5.0 * math.sin(angle * 4.0 + 1.2)
    z = 15.0 * math.sin(angle * 2.0 + 0.8) + 8.0 * math.sin(angle * 5.0 - 0.5)
    return Vector((x, y, z))


def contact_field(t: float, s: float) -> float:
    angle = t * math.tau
    inner_side = max(0.0, math.cos(s * math.tau + 0.1))
    belt = 0.5 + 0.5 * math.sin(angle * 6.0 - 0.9)
    pressure = max(0.0, belt - 0.42) / 0.58
    return min(1.0, inner_side ** 2.4 * pressure)


def tube_radius(t: float, s: float) -> float:
    angle = t * math.tau
    pulse = 0.5 + 0.5 * math.sin(angle * 8.0 + 0.4)
    fold = 0.5 + 0.5 * math.sin(s * math.tau * 4.0 - angle * 5.0)
    wrinkle = 0.5 + 0.5 * math.sin(s * math.tau * 9.0 + angle * 13.0)
    contact = contact_field(t, s)
    radius = 9.2 + 2.8 * pulse + 1.05 * fold + 0.42 * wrinkle
    return radius * (1.0 - 0.2 * contact)


def color_at(t: float, s: float) -> tuple[float, float, float, float]:
    angle = t * math.tau
    pulse = 0.5 + 0.5 * math.sin(angle * 8.0 + 0.4)
    vein = 0.5 + 0.5 * math.sin(s * math.tau * 6.0 - angle * 7.0)
    groove = max(0.0, vein - 0.58) / 0.42
    contact = contact_field(t, s)
    wet = 0.5 + 0.5 * math.sin(angle * 3.0 + s * math.tau * 2.0)
    base = (0.7 + pulse * 0.18, 0.18 + wet * 0.07, 0.25 + wet * 0.06)
    dark = (0.09, 0.006, 0.03)
    bruise = (0.24, 0.02, 0.07)
    pale = (1.0, 0.5, 0.42)
    dark_mix = min(0.92, groove * 0.38 + contact * 0.72)
    bruise_mix = min(0.45, (1.0 - contact) * groove * 0.28)
    mixed = (
        base[0] * (1.0 - bruise_mix) + bruise[0] * bruise_mix,
        base[1] * (1.0 - bruise_mix) + bruise[1] * bruise_mix,
        base[2] * (1.0 - bruise_mix) + bruise[2] * bruise_mix,
    )
    rim = max(0.0, math.sin(s * math.tau - 1.1)) * (1.0 - contact)
    color = (
        mixed[0] * (1.0 - dark_mix) + dark[0] * dark_mix,
        mixed[1] * (1.0 - dark_mix) + dark[1] * dark_mix,
        mixed[2] * (1.0 - dark_mix) + dark[2] * dark_mix,
    )
    return (
        color[0] * (1.0 - rim * 0.11) + pale[0] * rim * 0.11,
        color[1] * (1.0 - rim * 0.11) + pale[1] * rim * 0.11,
        color[2] * (1.0 - rim * 0.11) + pale[2] * rim * 0.11,
        1.0,
    )


def create_wreath_mesh() -> bpy.types.Object:
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
        inward = -radial.normalized()
        binormal = tangent.cross(inward).normalized()
        normal = binormal.cross(tangent).normalized()
        for j in range(SIDES):
            s = j / SIDES
            tube_angle = s * math.tau
            contact = contact_field(t, s)
            radius = tube_radius(t, s)
            oval = 1.0 - 0.22 * contact
            local = (normal * math.cos(tube_angle) * oval) + (binormal * math.sin(tube_angle))
            point = center + local * radius
            point += inward * (contact * 3.6)
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

    mesh = bpy.data.meshes.new("adhesion_gut_wreath_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="adhesion_gut_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Adhesion Gut Wreath", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("adhesion_gut_wet_material")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "adhesion_gut_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.2
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.13, 0.01, 0.04, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.09
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new("soft_wet_skin_edges", "BEVEL")
    bevel.width = 0.1
    bevel.segments = 1
    weighted = obj.modifiers.new("weighted_adhesion_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.45
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 72
    obj.rotation_euler[0] = math.radians(58)
    obj.rotation_euler[1] = math.radians(-9)
    obj.rotation_euler[2] = math.radians(18)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 72))
    target = bpy.context.object
    target.name = "adhesion_gut_target"

    bpy.ops.object.camera_add(location=(0, -258, 140), rotation=(math.radians(66), 0, 0))
    camera = bpy.context.object
    camera.name = "adhesion_gut_camera"
    camera.data.lens = 58
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-132, -126, 184))
    key = bpy.context.object
    key.name = "adhesion_gut_warm_key"
    key.data.energy = 4700
    key.data.color = (1.0, 0.5, 0.5)
    key.data.size = 130

    bpy.ops.object.light_add(type="POINT", location=(130, 70, 132))
    rim = bpy.context.object
    rim.name = "adhesion_gut_dark_red_rim"
    rim.data.color = (0.72, 0.04, 0.14)
    rim.data.energy = 1650
    rim.data.shadow_soft_size = 82

    bpy.ops.object.light_add(type="AREA", location=(0, -216, 112))
    front = bpy.context.object
    front.name = "adhesion_gut_soft_fill"
    front.data.energy = 700
    front.data.color = (1.0, 0.68, 0.62)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("adhesion_gut_preview_dark_backdrop")
    material.diffuse_color = (0.008, 0.001, 0.004, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.008, 0.001, 0.004, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "adhesion_gut_preview_dark_backdrop"
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
        world.color = (0.008, 0.001, 0.004)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    wreath = create_wreath_mesh()
    wreath.data.materials.append(create_material())
    prepare_object(wreath)
    setup_scene(wreath)
    export_stl(wreath)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
