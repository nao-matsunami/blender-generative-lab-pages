"""Generate Neural Gut Bloom assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:neural

Outputs:
- exports/stl/neural-gut-bloom.stl
- exports/glb/neural-gut-bloom.glb
- renders/neural-gut-bloom.png
- renders/neural-gut-bloom-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "neural-gut-bloom.stl"
GLB_PATH = ROOT / "exports" / "glb" / "neural-gut-bloom.glb"
RENDER_PATH = ROOT / "renders" / "neural-gut-bloom.png"
PREVIEW_PATH = ROOT / "renders" / "neural-gut-bloom-preview.png"

CORE_U = 96
CORE_V = 48
PATH_SEGMENTS = 168
TUBE_SEGMENTS = 30


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, scale: float):
    return (a[0] * scale, a[1] * scale, a[2] * scale)


def length(a) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def norm(a):
    size = length(a)
    if size < 0.00001:
        return (1.0, 0.0, 0.0)
    return (a[0] / size, a[1] / size, a[2] / size)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def color_at(u: float, v: float, layer: float) -> tuple[float, float, float, float]:
    vein = smoothstep(0.62, 0.98, 0.5 + 0.5 * math.sin(u * math.tau * 12.0 + v * math.tau * 1.7))
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 5.0 - layer * 0.8)
    base = (0.74 + wet * 0.16, 0.22 + layer * 0.055, 0.31 + wet * 0.08)
    nerve = (0.28, 0.055, 0.16)
    return (
        base[0] * (1.0 - vein) + nerve[0] * vein,
        base[1] * (1.0 - vein) + nerve[1] * vein,
        base[2] * (1.0 - vein) + nerve[2] * vein,
        1.0,
    )


def append_core(vertices, faces, colors) -> None:
    start = len(vertices)
    for y_index in range(CORE_V + 1):
        v = y_index / CORE_V
        phi = -math.pi / 2.0 + v * math.pi
        for x_index in range(CORE_U):
            u = x_index / CORE_U
            theta = u * math.tau
            lobe = 1.0 + 0.12 * math.sin(theta * 5.0 + phi * 1.3) + 0.09 * math.sin(theta * 9.0 - phi * 2.0)
            rib = 1.0 + 0.08 * math.sin(theta * 14.0 + v * math.tau * 1.8)
            rx = 34.0 * lobe * rib
            ry = 28.0 * lobe
            rz = 24.0 * (1.0 + 0.08 * math.sin(theta * 4.0))
            vertices.append((
                math.cos(phi) * math.cos(theta) * rx,
                math.cos(phi) * math.sin(theta) * ry,
                math.sin(phi) * rz,
            ))
            colors.append(color_at(u, v, 0.2))

    for y_index in range(CORE_V):
        for x_index in range(CORE_U):
            a = start + y_index * CORE_U + x_index
            b = start + y_index * CORE_U + ((x_index + 1) % CORE_U)
            c = start + (y_index + 1) * CORE_U + ((x_index + 1) % CORE_U)
            d = start + (y_index + 1) * CORE_U + x_index
            faces.append((a, b, c, d))


def tendril_center(layer: int, t: float):
    angle = t * math.tau
    phase = layer * 0.92
    orbit = 42.0 + 7.5 * math.sin(angle * 3.0 + phase)
    z = 18.0 * math.sin(angle * 2.0 + phase) + 9.0 * math.sin(angle * 5.0 - phase)
    return (
        math.cos(angle + phase * 0.16) * orbit + math.sin(angle * 4.0 + phase) * 8.0,
        math.sin(angle + phase * 0.16) * orbit * 0.74 + math.cos(angle * 3.0 - phase) * 7.0,
        z,
    )


def append_tendril(vertices, faces, colors, layer: int) -> None:
    start = len(vertices)
    for path_index in range(PATH_SEGMENTS):
        u = path_index / PATH_SEGMENTS
        center = tendril_center(layer, u)
        prev_center = tendril_center(layer, (u - 1.0 / PATH_SEGMENTS) % 1.0)
        next_center = tendril_center(layer, (u + 1.0 / PATH_SEGMENTS) % 1.0)
        tangent = norm(sub(next_center, prev_center))
        normal = norm(cross(tangent, (0.0, 0.0, 1.0)))
        if length(normal) < 0.001:
            normal = (1.0, 0.0, 0.0)
        binormal = norm(cross(normal, tangent))
        twist = math.sin(u * math.tau * (2.0 + layer * 0.2)) * 0.48 + u * math.tau

        for tube_index in range(TUBE_SEGMENTS):
            v = tube_index / TUBE_SEGMENTS
            angle = v * math.tau + twist
            fold = math.sin(u * math.tau * (8.0 + layer) + v * math.tau * 2.0)
            radius = 5.9 + math.copysign(abs(fold) ** 1.6, fold) * 1.4
            radius += math.sin(u * math.tau * 5.0 - layer) * 0.9
            oval = 1.0 + 0.22 * max(0.0, math.sin(angle + layer)) ** 1.7
            cross_section = add(
                mul(normal, math.cos(angle) * radius * oval),
                mul(binormal, math.sin(angle) * radius * 0.86),
            )
            vertices.append(add(center, cross_section))
            colors.append(color_at(u, v, 0.45 + layer * 0.08))

    for path_index in range(PATH_SEGMENTS):
        for tube_index in range(TUBE_SEGMENTS):
            a = start + path_index * TUBE_SEGMENTS + tube_index
            b = start + path_index * TUBE_SEGMENTS + ((tube_index + 1) % TUBE_SEGMENTS)
            c = start + ((path_index + 1) % PATH_SEGMENTS) * TUBE_SEGMENTS + ((tube_index + 1) % TUBE_SEGMENTS)
            d = start + ((path_index + 1) % PATH_SEGMENTS) * TUBE_SEGMENTS + tube_index
            faces.append((a, b, c, d))


def create_bloom_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []
    append_core(vertices, faces, colors)
    for layer in range(5):
        append_tendril(vertices, faces, colors, layer)

    mesh = bpy.data.meshes.new("neural_gut_bloom_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="neural_gut_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Neural Gut Bloom", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("neural_gut_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "neural_gut_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.26
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.2, 0.04, 0.12, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.14
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new("soft_neural_edges", "BEVEL")
    bevel.width = 0.16
    bevel.segments = 2
    weighted = obj.modifiers.new("weighted_neural_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.24
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 72
    obj.rotation_euler[0] = math.radians(54)
    obj.rotation_euler[1] = math.radians(-10)
    obj.rotation_euler[2] = math.radians(-16)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 70))
    target = bpy.context.object
    target.name = "neural_render_target"

    bpy.ops.object.camera_add(location=(0, -345, 112), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "neural_render_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-130, -135, 175))
    key = bpy.context.object
    key.name = "neural_warm_key"
    key.data.energy = 3200
    key.data.color = (1.0, 0.55, 0.68)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(150, 85, 130))
    rim = bpy.context.object
    rim.name = "neural_bruise_rim"
    rim.data.color = (0.72, 0.12, 0.28)
    rim.data.energy = 1200
    rim.data.shadow_soft_size = 80

    bpy.ops.object.light_add(type="AREA", location=(0, -225, 112))
    front = bpy.context.object
    front.name = "neural_front_fill"
    front.data.energy = 720
    front.data.color = (1.0, 0.74, 0.82)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("neural_preview_dark_backdrop")
    material.diffuse_color = (0.01, 0.004, 0.01, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.01, 0.004, 0.01, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 160, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "neural_preview_dark_backdrop"
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
        world.color = (0.01, 0.004, 0.01)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    bloom = create_bloom_mesh()
    bloom.data.materials.append(create_material())
    prepare_object(bloom)
    setup_scene(bloom)
    export_stl(bloom)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
