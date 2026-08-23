"""Generate Visceral Tide Knot assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:viscera

Outputs:
- exports/stl/visceral-tide-knot.stl
- exports/glb/visceral-tide-knot.glb
- renders/visceral-tide-knot.png
- renders/visceral-tide-knot-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "visceral-tide-knot.stl"
GLB_PATH = ROOT / "exports" / "glb" / "visceral-tide-knot.glb"
RENDER_PATH = ROOT / "renders" / "visceral-tide-knot.png"
PREVIEW_PATH = ROOT / "renders" / "visceral-tide-knot-preview.png"

PATH_SEGMENTS = 224
TUBE_SEGMENTS = 42


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_mul(a, scale: float):
    return (a[0] * scale, a[1] * scale, a[2] * scale)


def vec_len(a) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def vec_norm(a):
    length = vec_len(a)
    if length < 0.00001:
        return (1.0, 0.0, 0.0)
    return (a[0] / length, a[1] / length, a[2] / length)


def vec_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def center_at(t: float):
    angle = t * math.tau
    major = 49.0 + 8.5 * math.sin(angle * 3.0 + 0.35) + 5.5 * math.sin(angle * 7.0 - 0.7)
    x = math.cos(angle) * major + 18.0 * math.sin(angle * 2.0 + 0.4)
    y = math.sin(angle) * major * 0.8 + 10.0 * math.sin(angle * 4.0 - 0.8)
    z = 22.0 * math.sin(angle * 2.0 + 0.7) + 11.0 * math.sin(angle * 5.0)
    return (x, y, z)


def radius_at(u: float, v: float) -> float:
    fold = math.sin(u * math.tau * 11.0 + v * math.tau * 2.2)
    slow = math.sin(u * math.tau * 5.0 - v * math.tau * 0.8)
    membrane = smoothstep(0.62, 0.98, 0.5 + 0.5 * math.sin(v * math.tau + u * math.tau * 3.0))
    return 9.8 + math.copysign(abs(fold) ** 1.65, fold) * 2.9 + slow * 1.7 + membrane * 1.2


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    fold = 0.5 + 0.5 * math.sin(u * math.tau * 11.0 + v * math.tau * 2.2)
    vein = smoothstep(0.62, 0.95, 1.0 - fold)
    tide = 0.5 + 0.5 * math.sin(u * math.tau * 4.0 - 0.5)
    base = (
        0.62 + 0.18 * tide,
        0.22 + 0.08 * fold,
        0.34 + 0.16 * tide,
    )
    bruise = (0.18, 0.12, 0.28)
    gloss = smoothstep(0.72, 1.0, fold)
    color = (
        base[0] * (1.0 - vein) + bruise[0] * vein + gloss * 0.08,
        base[1] * (1.0 - vein) + bruise[1] * vein + gloss * 0.04,
        base[2] * (1.0 - vein) + bruise[2] * vein + gloss * 0.1,
    )
    return (min(1.0, color[0]), min(1.0, color[1]), min(1.0, color[2]), 1.0)


def create_knot_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for path_index in range(PATH_SEGMENTS):
        u = path_index / PATH_SEGMENTS
        center = center_at(u)
        prev_center = center_at((u - 1.0 / PATH_SEGMENTS) % 1.0)
        next_center = center_at((u + 1.0 / PATH_SEGMENTS) % 1.0)
        tangent = vec_norm(vec_sub(next_center, prev_center))
        up = (0.0, 0.0, 1.0)
        normal = vec_norm(vec_cross(tangent, up))
        if vec_len(normal) < 0.001:
            normal = (1.0, 0.0, 0.0)
        binormal = vec_norm(vec_cross(normal, tangent))
        frame_twist = math.sin(u * math.tau * 3.0) * 0.42 + u * math.tau

        for tube_index in range(TUBE_SEGMENTS):
            v = tube_index / TUBE_SEGMENTS
            angle = v * math.tau + frame_twist
            radius = radius_at(u, v)
            oval = 1.0 + 0.22 * max(0.0, math.sin(angle + u * math.tau * 2.0)) ** 1.8
            cross = vec_add(
                vec_mul(normal, math.cos(angle) * radius * oval),
                vec_mul(binormal, math.sin(angle) * radius * (0.82 + 0.08 * math.sin(u * math.tau * 8.0))),
            )
            vertices.append(vec_add(center, cross))
            colors.append(color_at(u, v))

    for path_index in range(PATH_SEGMENTS):
        for tube_index in range(TUBE_SEGMENTS):
            a = path_index * TUBE_SEGMENTS + tube_index
            b = path_index * TUBE_SEGMENTS + ((tube_index + 1) % TUBE_SEGMENTS)
            c = ((path_index + 1) % PATH_SEGMENTS) * TUBE_SEGMENTS + ((tube_index + 1) % TUBE_SEGMENTS)
            d = ((path_index + 1) % PATH_SEGMENTS) * TUBE_SEGMENTS + tube_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("visceral_tide_knot_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="visceral_tide_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Visceral Tide Knot", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("visceral_tide_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "visceral_tide_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.22, 0.05, 0.1, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.1
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    bevel = obj.modifiers.new("soft_visceral_edges", "BEVEL")
    bevel.width = 0.18
    bevel.segments = 2

    weighted = obj.modifiers.new("weighted_visceral_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.18
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 72
    obj.rotation_euler[0] = math.radians(58)
    obj.rotation_euler[1] = math.radians(-8)
    obj.rotation_euler[2] = math.radians(28)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 70))
    target = bpy.context.object
    target.name = "visceral_render_target"

    bpy.ops.object.camera_add(location=(0, -330, 102), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "visceral_render_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-120, -130, 170))
    key = bpy.context.object
    key.name = "visceral_warm_key"
    key.data.energy = 3000
    key.data.color = (1.0, 0.52, 0.52)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(145, 85, 120))
    rim = bpy.context.object
    rim.name = "visceral_cold_rim"
    rim.data.color = (0.5, 0.82, 1.0)
    rim.data.energy = 1450
    rim.data.shadow_soft_size = 78

    bpy.ops.object.light_add(type="AREA", location=(0, -220, 105))
    front = bpy.context.object
    front.name = "visceral_front_fill"
    front.data.energy = 620
    front.data.color = (1.0, 0.72, 0.78)
    front.data.size = 220


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("visceral_preview_dark_backdrop")
    material.diffuse_color = (0.012, 0.006, 0.01, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.012, 0.006, 0.01, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 155, 70), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "visceral_preview_dark_backdrop"
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
        world.color = (0.012, 0.006, 0.01)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    knot = create_knot_mesh()
    knot.data.materials.append(create_material())
    prepare_object(knot)
    setup_scene(knot)
    export_stl(knot)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
