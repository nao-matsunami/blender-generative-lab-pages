"""Generate Voronoi Light Shell assets in Blender.

Run from this project root:
blender --background --python offline/generate_voronoi_light_shell.py

Outputs:
- exports/stl/voronoi-light-shell.stl
- exports/glb/voronoi-light-shell.glb
- renders/voronoi-light-shell.png

This first version creates a perforation-inspired shell with raised ribs and
indentations. Treat it as a design study until a slicer confirms printability.
"""

import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in __import__("os").environ:
    ROOT = Path(__import__("os").environ["BLENDER_LAB_ROOT"]).resolve()
STL_PATH = ROOT / "exports" / "stl" / "voronoi-light-shell.stl"
GLB_PATH = ROOT / "exports" / "glb" / "voronoi-light-shell.glb"
RENDER_PATH = ROOT / "renders" / "voronoi-light-shell.png"
PREVIEW_PATH = ROOT / "renders" / "voronoi-light-shell-preview.png"

RADIAL_SEGMENTS = 240
HEIGHT_SEGMENTS = 144
HEIGHT_MM = 150.0
WALL_THICKNESS_MM = 2.8


def cell_windows():
    windows = []
    for cell in range(46):
        windows.append(
            {
                "u": (cell * 0.61803398875 + 0.08 * math.sin(cell * 2.17)) % 1.0,
                "v": 0.12 + ((cell * 0.379 + 0.04 * math.cos(cell * 1.31)) % 0.76),
                "w": 0.018 + 0.014 * (0.5 + 0.5 * math.sin(cell * 1.83)),
                "h": 0.018 + 0.018 * (0.5 + 0.5 * math.cos(cell * 2.21)),
                "twist": cell * 0.73,
            }
        )
    return windows


CELL_WINDOWS = cell_windows()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def shell_radius(u: float, v: float) -> float:
    profile = math.sin(v * math.pi)
    dome = 20.0 + profile * 42.0
    shoulder = 16.0 * math.exp(-((v - 0.62) / 0.18) ** 2)
    crown_taper = -10.0 * math.exp(-((v - 0.96) / 0.07) ** 2)
    foot_taper = -6.0 * math.exp(-((v - 0.04) / 0.06) ** 2)
    macro = math.sin(u * math.tau * 4.0 + v * 9.0) * 4.2
    micro = math.cos(u * math.tau * 7.0 - v * 13.0) * 3.1
    cellular = math.sin(u * math.tau * 11.0 + math.sin(v * 11.0) * 2.0) * 2.8
    rib = ((0.5 + 0.5 * math.sin(u * math.tau * 16.0 + v * 6.0)) ** 4) * 4.6
    return dome + shoulder + crown_taper + foot_taper + (macro + micro + cellular + rib) * profile


def create_shell_mesh() -> bpy.types.Object:
    vertices = []
    faces = []

    for y_index in range(HEIGHT_SEGMENTS + 1):
        v = y_index / HEIGHT_SEGMENTS
        y = (v - 0.5) * HEIGHT_MM
        for x_index in range(RADIAL_SEGMENTS):
            u = x_index / RADIAL_SEGMENTS
            angle = u * math.tau
            radius = shell_radius(u, v)
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius * 0.84, y))

    for y_index in range(HEIGHT_SEGMENTS):
        for x_index in range(RADIAL_SEGMENTS):
            center_u = (x_index + 0.5) / RADIAL_SEGMENTS
            center_v = (y_index + 0.5) / HEIGHT_SEGMENTS
            if is_inside_cell_window(center_u, center_v):
                continue
            a = y_index * RADIAL_SEGMENTS + x_index
            b = y_index * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            c = (y_index + 1) * RADIAL_SEGMENTS + ((x_index + 1) % RADIAL_SEGMENTS)
            d = (y_index + 1) * RADIAL_SEGMENTS + x_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new("voronoi_light_shell_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Voronoi Light Shell", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def wrapped_delta(a: float, b: float) -> float:
    delta = a - b
    if delta > 0.5:
        delta -= 1.0
    if delta < -0.5:
        delta += 1.0
    return delta


def is_inside_cell_window(u: float, v: float) -> bool:
    for window in CELL_WINDOWS:
        du = wrapped_delta(u, window["u"])
        dv = v - window["v"]
        twist = -window["twist"]
        local_u = du * math.cos(twist) - dv * math.sin(twist) * 0.42
        local_v = du * math.sin(twist) + dv * math.cos(twist)
        wobble = 1.0 + 0.18 * math.sin((u + v) * math.tau * 8.0)
        if (local_u / (window["w"] * wobble)) ** 2 + (local_v / window["h"]) ** 2 < 1.0:
            return True
    return False


def create_shell_material() -> bpy.types.Material:
    material = bpy.data.materials.new("amber_porcelain_shell")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.96, 0.64, 0.36, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.46
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.94
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.28
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.38, 0.13, 0.04, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.18
    return material


def create_rib_material() -> bpy.types.Material:
    material = bpy.data.materials.new("cyan_window_edges")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.38, 0.9, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.3
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.12, 0.5, 1.0, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.78
    return material


def add_rib_curves(parent: bpy.types.Object, material: bpy.types.Material) -> None:
    for band in range(9):
        v = 0.12 + band / 8.0 * 0.76
        curve = bpy.data.curves.new(f"light_rib_band_{band:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = 0.36
        curve.bevel_resolution = 3
        spline = curve.splines.new("POLY")
        spline.points.add(RADIAL_SEGMENTS)
        for index in range(RADIAL_SEGMENTS + 1):
            u = index / RADIAL_SEGMENTS
            wave = math.sin(u * math.tau * (5 + band % 3) + band * 1.7)
            angle = u * math.tau + band * 0.18
            radius = shell_radius(u, v) + 1.0 + max(0.0, wave) * 0.6
            point = spline.points[index]
            point.co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * 0.84,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )
        obj = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(material)


def add_cell_window_rims(material: bpy.types.Material) -> None:
    for cell, window in enumerate(CELL_WINDOWS):
        center_u = window["u"]
        center_v = window["v"]
        width = window["w"]
        height = window["h"]
        twist = window["twist"]
        curve = bpy.data.curves.new(f"cellular_window_rim_{cell:02d}", "CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 3
        curve.bevel_depth = 0.55
        curve.bevel_resolution = 3
        spline = curve.splines.new("POLY")
        points = 32
        spline.points.add(points)

        for index in range(points + 1):
            t = index / points * math.tau
            du = math.cos(t) * width * (1.0 + 0.22 * math.sin(t * 3.0 + cell))
            dv = math.sin(t) * height
            u = (center_u + du * math.cos(twist) - dv * math.sin(twist) * 0.42) % 1.0
            v = min(0.94, max(0.06, center_v + du * math.sin(twist) + dv * math.cos(twist)))
            angle = u * math.tau
            radius = shell_radius(u, v) + 1.85
            point = spline.points[index]
            point.co = (
                math.cos(angle) * radius,
                math.sin(angle) * radius * 0.84,
                (v - 0.5) * HEIGHT_MM + HEIGHT_MM * 0.5,
                1.0,
            )

        rim = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(rim)
        rim.data.materials.append(material)


def prepare_for_print(obj: bpy.types.Object) -> None:
    bpy.ops.object.shade_smooth()

    solidify = obj.modifiers.new("print_wall_thickness", "SOLIDIFY")
    solidify.thickness = WALL_THICKNESS_MM
    solidify.offset = 0.0
    solidify.use_quality_normals = True

    bevel = obj.modifiers.new("soft_shell_edges", "BEVEL")
    bevel.width = 0.5
    bevel.segments = 2

    weighted = obj.modifiers.new("weighted_shell_normals", "WEIGHTED_NORMAL")
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
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.45
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    obj.location.z = HEIGHT_MM * 0.5

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, HEIGHT_MM * 0.54))
    target = bpy.context.object
    target.name = "shell_render_target"

    bpy.ops.object.camera_add(location=(0, -325, HEIGHT_MM * 0.58), rotation=(math.radians(76), 0, 0))
    camera = bpy.context.object
    camera.name = "shell_render_camera"
    camera.data.lens = 48
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="POINT", location=(0, 0, 32))
    core = bpy.context.object
    core.name = "warm_inner_light"
    core.data.energy = 620
    core.data.color = (1.0, 0.58, 0.28)
    core.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(-95, -120, 150))
    key = bpy.context.object
    key.name = "large_shell_key"
    key.data.energy = 900
    key.data.size = 140

    bpy.ops.object.light_add(type="POINT", location=(115, 70, 120))
    rim = bpy.context.object
    rim.name = "cool_shell_rim"
    rim.data.color = (0.5, 0.86, 1.0)
    rim.data.energy = 520
    rim.data.shadow_soft_size = 70


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

    world = bpy.context.scene.world
    if world:
        world.color = (0.78, 0.82, 0.86)
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    shell = create_shell_mesh()
    shell.data.materials.append(create_shell_material())
    prepare_for_print(shell)
    setup_scene(shell)
    rim_material = create_rib_material()
    add_rib_curves(shell, rim_material)
    add_cell_window_rims(rim_material)
    export_stl(shell)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
