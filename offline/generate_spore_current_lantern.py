"""Generate Spore Current Lantern assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:spore

Outputs:
- exports/stl/spore-current-lantern.stl
- exports/glb/spore-current-lantern.glb
- renders/spore-current-lantern.png
- renders/spore-current-lantern-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "spore-current-lantern.stl"
GLB_PATH = ROOT / "exports" / "glb" / "spore-current-lantern.glb"
RENDER_PATH = ROOT / "renders" / "spore-current-lantern.png"
PREVIEW_PATH = ROOT / "renders" / "spore-current-lantern-preview.png"

RADIAL_SEGMENTS = 192
HEIGHT_SEGMENTS = 132
HEIGHT_MM = 168.0
WALL_THICKNESS_MM = 2.4


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def radius_at(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    angle = u * math.tau
    base = 16.0 + 42.0 * (profile ** 0.66)
    neck = -14.0 * math.exp(-(((v - 0.94) / 0.075) ** 2))
    foot = -10.0 * math.exp(-(((v - 0.055) / 0.07) ** 2))
    current = math.sin(u * math.tau * 7.0 + v * math.tau * 2.1)
    current += 0.45 * math.sin(u * math.tau * 11.0 - v * math.tau * 1.4)
    rib = math.copysign(abs(current) ** 1.55, current) * 6.2 * profile
    chamber = math.sin(u * math.tau * 5.0 - v * math.tau * 1.15) * 4.7 * (profile ** 1.28)
    asymmetry = math.sin(angle * 2.0 + v * math.tau * 0.55) * 3.4 * profile
    return base + neck + foot + rib + chamber + asymmetry


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    profile = math.sin(v * math.pi)
    current = 0.5 + 0.5 * math.sin(u * math.tau * 7.0 + v * math.tau * 2.1)
    groove = 1.0 - current
    flow_line = smoothstep(0.66, 0.96, groove) * profile
    warm = 0.82 + 0.2 * current + 0.12 * profile
    base = (
        min(1.0, 0.86 * warm + 0.1),
        min(1.0, 0.42 * warm + 0.2),
        min(1.0, 0.22 * warm + 0.16),
    )
    line = (0.2, 0.36, 0.46)
    return (
        base[0] * (1.0 - flow_line) + line[0] * flow_line,
        base[1] * (1.0 - flow_line) + line[1] * flow_line,
        base[2] * (1.0 - flow_line) + line[2] * flow_line,
        1.0,
    )


def create_lantern_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        z = (v - 0.5) * HEIGHT_MM
        profile = math.sin(v * math.pi)
        twist = v * math.tau * 0.38 + math.sin(v * math.pi) * 0.28
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau + twist
            radius = radius_at(u, v)
            oval_x = 0.96 + 0.08 * math.sin(v * math.tau * 2.0)
            oval_y = 0.76 + 0.06 * math.cos(v * math.tau * 2.6)
            pulse = math.sin(u * math.tau * 3.0 - v * math.tau * 0.9) * 6.8 * (profile ** 1.16)
            vertices.append((math.cos(angle) * (radius + pulse) * oval_x, math.sin(angle) * radius * oval_y, z))
            colors.append(color_at(u, v))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("spore_current_lantern_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="spore_current_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Spore Current Lantern", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("spore_current_ceramic")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "spore_current_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.34
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.4, 0.16, 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.08
    return material


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_lantern_rim", "BEVEL")
    bevel.width = 0.36
    bevel.segments = 3

    weighted = obj.modifiers.new("weighted_lantern_normals", "WEIGHTED_NORMAL")
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

    obj.location.z = HEIGHT_MM * 0.5
    obj.rotation_euler[0] = math.radians(8)
    obj.rotation_euler[1] = math.radians(0)
    obj.rotation_euler[2] = math.radians(-24)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.52))
    target = bpy.context.object
    target.name = "spore_render_target"

    bpy.ops.object.camera_add(location=(0, -390, HEIGHT_MM * 0.68), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "spore_render_camera"
    camera.data.lens = 46
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-120, -150, 190))
    key = bpy.context.object
    key.name = "spore_warm_key"
    key.data.energy = 3300
    key.data.color = (1.0, 0.72, 0.46)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(125, 80, 150))
    rim = bpy.context.object
    rim.name = "spore_teal_rim"
    rim.data.color = (0.45, 0.9, 1.0)
    rim.data.energy = 1900
    rim.data.shadow_soft_size = 75

    bpy.ops.object.light_add(type="AREA", location=(0, -230, 130))
    front = bpy.context.object
    front.name = "spore_front_fill"
    front.data.energy = 420
    front.data.color = (1.0, 0.84, 0.66)
    front.data.size = 220


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
        world.color = (0.01, 0.014, 0.015)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("spore_preview_dark_backdrop")
    material.diffuse_color = (0.006, 0.01, 0.011, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.006, 0.01, 0.011, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.92

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 170, HEIGHT_MM * 0.5), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "spore_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(material)


def main() -> None:
    clear_scene()
    lantern = create_lantern_mesh()
    lantern.data.materials.append(create_material())
    prepare_for_print(lantern)
    setup_scene(lantern)
    export_stl(lantern)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
