"""Generate Arterial Fold Nest assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:arterial

Outputs:
- exports/stl/arterial-fold-nest.stl
- exports/glb/arterial-fold-nest.glb
- renders/arterial-fold-nest.png
- renders/arterial-fold-nest-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "arterial-fold-nest.stl"
GLB_PATH = ROOT / "exports" / "glb" / "arterial-fold-nest.glb"
RENDER_PATH = ROOT / "renders" / "arterial-fold-nest.png"
PREVIEW_PATH = ROOT / "renders" / "arterial-fold-nest-preview.png"

U_SEGMENTS = 176
V_SEGMENTS = 104


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def arterial_field(u: float, v: float) -> float:
    field = 0.0
    for offset, phase, weight in (
        (0.08, 0.15, 1.0),
        (0.27, 0.61, 0.7),
        (0.48, 0.36, 0.82),
        (0.72, 0.83, 0.9),
    ):
        center = (offset + 0.16 * math.sin(v * math.tau * 0.72 + phase)) % 1.0
        distance = abs(((u - center + 0.5) % 1.0) - 0.5)
        ridge = max(0.0, 1.0 - distance / 0.055) ** 2.2
        field += ridge * weight
    return min(1.0, field)


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    waist = 1.0 - 0.18 * math.sin(v * math.pi * 2.0 + 0.5)
    lobes = 1.0 + 0.16 * math.sin(u * math.tau * 4.0 + v * math.tau * 0.7)
    folds = 1.0 + 0.095 * math.sin(u * math.tau * 12.0 - v * math.tau * 2.5)
    artery = arterial_field(u, v)
    mouth = smoothstep(0.0, 0.18, v) * (1.0 - smoothstep(0.84, 1.0, v))
    base = 15.0 + 42.0 * (profile ** 0.62)
    return (base * waist * lobes * folds + artery * 11.0 * (profile ** 0.95)) * (0.78 + mouth * 0.22)


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    artery = arterial_field(u, v)
    fold_shadow = 0.5 + 0.5 * math.sin(u * math.tau * 12.0 - v * math.tau * 2.5)
    wet = 0.5 + 0.5 * math.sin(u * math.tau * 3.0 + v * math.tau * 1.8)
    base = (0.76 + wet * 0.16, 0.22 + wet * 0.06, 0.29 + wet * 0.05)
    dark = (0.2, 0.022, 0.065)
    pale = (1.0, 0.52, 0.46)
    shade = smoothstep(0.56, 1.0, 1.0 - fold_shadow)
    blush = smoothstep(0.0, 0.22, v) * (1.0 - smoothstep(0.78, 1.0, v))
    mix_dark = min(0.82, artery * 0.68 + shade * 0.28)
    color = (
        base[0] * (1.0 - mix_dark) + dark[0] * mix_dark,
        base[1] * (1.0 - mix_dark) + dark[1] * mix_dark,
        base[2] * (1.0 - mix_dark) + dark[2] * mix_dark,
    )
    return (
        color[0] * (1.0 - blush * 0.18) + pale[0] * blush * 0.18,
        color[1] * (1.0 - blush * 0.18) + pale[1] * blush * 0.18,
        color[2] * (1.0 - blush * 0.18) + pale[2] * blush * 0.18,
        1.0,
    )


def create_nest_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        z = (v - 0.5) * 124.0
        profile = math.sin(v * math.pi)
        twist = v * math.tau * 0.18 + math.sin(v * math.pi * 1.2) * 0.38
        pinch = 1.0 - 0.16 * math.cos(v * math.tau)
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            angle = u * math.tau + twist
            radius = radius_at(u, v)
            artery = arterial_field(u, v)
            sag = math.sin(u * math.tau * 2.0 + v * math.tau * 0.35) * 4.4 * (profile ** 1.2)
            x = math.cos(angle) * (radius + sag) * (0.9 + 0.08 * artery)
            y = math.sin(angle) * radius * (0.9 + 0.04 * math.sin(v * math.tau * 2.0)) * pinch
            vertices.append((x, y, z))
            colors.append(color_at(u, v))

    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("arterial_fold_nest_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="arterial_fold_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Arterial Fold Nest", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("arterial_fold_wet_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf = node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "arterial_fold_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.24
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.16, 0.018, 0.055, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()
    smooth = obj.modifiers.new("soften_fold_surface", "SUBSURF")
    smooth.levels = 1
    smooth.render_levels = 1
    solidify = obj.modifiers.new("printable_membrane_wall", "SOLIDIFY")
    solidify.thickness = 2.0
    solidify.offset = 0.0
    solidify.use_quality_normals = True
    bevel = obj.modifiers.new("soft_fold_edges", "BEVEL")
    bevel.width = 0.22
    bevel.segments = 2
    weighted = obj.modifiers.new("weighted_fold_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.42
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 82
    obj.rotation_euler[0] = math.radians(8)
    obj.rotation_euler[1] = math.radians(-7)
    obj.rotation_euler[2] = math.radians(24)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 82))
    target = bpy.context.object
    target.name = "arterial_fold_target"

    bpy.ops.object.camera_add(location=(0, -324, 122), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "arterial_fold_camera"
    camera.data.lens = 50
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-140, -122, 178))
    key = bpy.context.object
    key.name = "arterial_rose_key"
    key.data.energy = 4300
    key.data.color = (1.0, 0.5, 0.52)
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(120, 82, 132))
    rim = bpy.context.object
    rim.name = "arterial_dark_rim"
    rim.data.color = (0.78, 0.08, 0.18)
    rim.data.energy = 1600
    rim.data.shadow_soft_size = 75

    bpy.ops.object.light_add(type="AREA", location=(0, -225, 118))
    front = bpy.context.object
    front.name = "arterial_soft_fill"
    front.data.energy = 980
    front.data.color = (1.0, 0.7, 0.66)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("arterial_preview_dark_backdrop")
    material.diffuse_color = (0.01, 0.002, 0.006, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.01, 0.002, 0.006, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.94
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 82), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "arterial_preview_dark_backdrop"
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
    nest = create_nest_mesh()
    nest.data.materials.append(create_material())
    prepare_object(nest)
    setup_scene(nest)
    export_stl(nest)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
