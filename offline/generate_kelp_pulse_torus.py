"""Generate Kelp Pulse Torus assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:kelp

Outputs:
- exports/stl/kelp-pulse-torus.stl
- exports/glb/kelp-pulse-torus.glb
- renders/kelp-pulse-torus.png
- renders/kelp-pulse-torus-preview.png
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "kelp-pulse-torus.stl"
GLB_PATH = ROOT / "exports" / "glb" / "kelp-pulse-torus.glb"
RENDER_PATH = ROOT / "renders" / "kelp-pulse-torus.png"
PREVIEW_PATH = ROOT / "renders" / "kelp-pulse-torus-preview.png"

MAJOR_SEGMENTS = 192
MINOR_SEGMENTS = 48
MAJOR_RADIUS_MM = 58.0
MINOR_RADIUS_MM = 15.0


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def pulse_at(u: float, v: float) -> float:
    frond = math.sin(u * math.tau * 9.0 + v * math.tau * 1.2)
    slow = math.sin(u * math.tau * 4.0 - v * math.tau * 0.75)
    ridge = math.copysign(abs(frond) ** 1.7, frond)
    return ridge * 4.8 + slow * 2.2


def color_at(u: float, v: float) -> tuple[float, float, float, float]:
    pulse = 0.5 + 0.5 * math.sin(u * math.tau * 9.0 + v * math.tau * 1.2)
    groove = smoothstep(0.55, 0.96, 1.0 - pulse)
    glow = 0.5 + 0.5 * math.sin(u * math.tau * 3.0 - 0.6)
    base = (
        0.18 + 0.16 * glow,
        0.48 + 0.22 * pulse,
        0.42 + 0.18 * glow,
    )
    amber = (0.92, 0.54, 0.22)
    return (
        base[0] * (1.0 - groove) + amber[0] * groove,
        base[1] * (1.0 - groove) + amber[1] * groove,
        base[2] * (1.0 - groove) + amber[2] * groove,
        1.0,
    )


def create_torus_mesh() -> bpy.types.Object:
    vertices = []
    faces = []
    colors = []

    for major_index in range(MAJOR_SEGMENTS):
        u = major_index / MAJOR_SEGMENTS
        twist = math.sin(u * math.tau * 3.0) * 0.28
        major_angle = u * math.tau
        ring_wobble = math.sin(u * math.tau * 5.0) * 5.2 + math.sin(u * math.tau * 2.0 + 0.8) * 3.4
        major_radius = MAJOR_RADIUS_MM + ring_wobble
        vertical_drift = math.sin(u * math.tau * 4.0 - 0.4) * 7.5

        center = (
            math.cos(major_angle) * major_radius * 1.08,
            math.sin(major_angle) * major_radius * 0.86,
            vertical_drift,
        )
        radial = (math.cos(major_angle), math.sin(major_angle), 0.0)
        tangent = (-math.sin(major_angle), math.cos(major_angle), 0.0)

        for minor_index in range(MINOR_SEGMENTS):
            v = minor_index / MINOR_SEGMENTS
            minor_angle = v * math.tau + twist + math.sin(u * math.tau * 2.0) * 0.18
            pulse = pulse_at(u, v)
            tube_radius = MINOR_RADIUS_MM + pulse
            blade = 1.0 + 0.38 * max(0.0, math.sin(minor_angle)) ** 1.9
            cross_x = math.cos(minor_angle) * tube_radius * blade
            cross_z = math.sin(minor_angle) * tube_radius * (0.72 + 0.1 * math.sin(u * math.tau * 6.0))
            lift = math.sin(u * math.tau * 7.0 + v * math.tau * 2.0) * 1.8
            vertices.append((
                center[0] + radial[0] * cross_x + tangent[0] * lift,
                center[1] + radial[1] * cross_x + tangent[1] * lift,
                center[2] + cross_z,
            ))
            colors.append(color_at(u, v))

    for major_index in range(MAJOR_SEGMENTS):
        for minor_index in range(MINOR_SEGMENTS):
            a = major_index * MINOR_SEGMENTS + minor_index
            b = major_index * MINOR_SEGMENTS + ((minor_index + 1) % MINOR_SEGMENTS)
            c = ((major_index + 1) % MAJOR_SEGMENTS) * MINOR_SEGMENTS + ((minor_index + 1) % MINOR_SEGMENTS)
            d = ((major_index + 1) % MAJOR_SEGMENTS) * MINOR_SEGMENTS + minor_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("kelp_pulse_torus_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    color_attribute = mesh.color_attributes.new(name="kelp_pulse_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]

    obj = bpy.data.objects.new("Kelp Pulse Torus", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def create_material() -> bpy.types.Material:
    material = bpy.data.materials.new("kelp_pulse_satin")
    material.use_nodes = True
    node_tree = material.node_tree
    nodes = node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        attribute = nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "kelp_pulse_color"
        node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.38
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.04, 0.18, 0.13, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.12
    return material


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    bevel = obj.modifiers.new("soft_print_edges", "BEVEL")
    bevel.width = 0.28
    bevel.segments = 2

    weighted = obj.modifiers.new("weighted_kelp_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.exposure = 1.08
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = 70
    obj.rotation_euler[0] = math.radians(62)
    obj.rotation_euler[1] = math.radians(0)
    obj.rotation_euler[2] = math.radians(-18)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 66))
    target = bpy.context.object
    target.name = "kelp_render_target"

    bpy.ops.object.camera_add(location=(0, -330, 96), rotation=(math.radians(72), 0, 0))
    camera = bpy.context.object
    camera.name = "kelp_render_camera"
    camera.data.lens = 46
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-130, -135, 170))
    key = bpy.context.object
    key.name = "kelp_green_key"
    key.data.energy = 2400
    key.data.color = (0.62, 1.0, 0.82)
    key.data.size = 150

    bpy.ops.object.light_add(type="POINT", location=(150, 70, 110))
    rim = bpy.context.object
    rim.name = "kelp_amber_rim"
    rim.data.color = (1.0, 0.62, 0.28)
    rim.data.energy = 1100
    rim.data.shadow_soft_size = 80

    bpy.ops.object.light_add(type="AREA", location=(0, -210, 100))
    front = bpy.context.object
    front.name = "kelp_front_fill"
    front.data.energy = 520
    front.data.color = (0.72, 0.95, 1.0)
    front.data.size = 220


def add_preview_backdrop() -> None:
    material = bpy.data.materials.new("kelp_preview_dark_backdrop")
    material.diffuse_color = (0.004, 0.01, 0.012, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.004, 0.01, 0.012, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.92

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 70), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "kelp_preview_dark_backdrop"
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
        world.color = (0.004, 0.01, 0.012)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    torus = create_torus_mesh()
    torus.data.materials.append(create_material())
    prepare_object(torus)
    setup_scene(torus)
    export_stl(torus)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
