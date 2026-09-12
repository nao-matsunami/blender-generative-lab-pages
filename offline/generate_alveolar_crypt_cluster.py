"""Generate Alveolar Crypt Cluster assets in Blender.

Mac mini workflow:
npm run job:alveolarcrypt
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "alveolar-crypt-cluster"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float], roughness: float, emission: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return material


def add_sac(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=30, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    obj.modifiers.new(name + "_weighted_normals", "WEIGHTED_NORMAL")
    return obj


def add_lip(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], angle: float, material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=18, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = (math.radians(5), 0, math.radians(angle))
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def make_tube(name: str, points: list[tuple[float, float, float]], bevel: float, material: bpy.types.Material) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = bevel
    curve.bevel_resolution = 10
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coords in zip(spline.bezier_points, points):
        point.co = coords
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_parts() -> list[bpy.types.Object]:
    sac_material = make_material("wet_pale_alveolar_sac_membrane", (0.72, 0.19, 0.23, 1.0), 0.16, 0.04)
    dark_material = make_material("near_black_bronchial_crypt", (0.004, 0.0, 0.003, 1.0), 0.72)
    lip_material = make_material("compressed_dark_pink_alveolar_rims", (0.58, 0.055, 0.10, 1.0), 0.15, 0.05)
    root_material = make_material("dark_crimson_bronchial_stem", (0.34, 0.012, 0.04, 1.0), 0.18, 0.05)
    objects: list[bpy.types.Object] = []
    placements = [
        (-24, -23, 14, 28, 12, 24, -18),
        (6, -29, 21, 31, 13, 27, 5),
        (28, -22, -4, 24, 11, 25, 24),
        (-18, -29, -18, 26, 12, 22, -36),
        (12, -34, -23, 28, 11, 21, 18),
        (0, -18, 0, 33, 14, 31, 0),
    ]
    for index, (x, y, z, sx, sy, sz, angle) in enumerate(placements):
        objects.append(add_sac(f"alveolar_pressed_sac_{index + 1}", (x, y, z), (sx, sy, sz), sac_material))
        objects.append(add_lip(f"alveolar_contact_rim_{index + 1}", (x * 0.75, y - 9, z * 0.75), (sx * 0.48, 2.6, sz * 0.42), angle, lip_material))
    objects.append(add_sac("alveolar_deep_shared_crypt", (0, -42, 0), (21, 8, 28), dark_material))
    objects.append(make_tube("alveolar_structural_bronchial_stem", [(0, -42, -6), (0, -57, -18), (-4, -66, -35), (-8, -61, -54)], 6.0, root_material))
    return objects


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
    scene.view_settings.exposure = 1.48
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-8))
        obj.rotation_euler.rotate_axis("X", math.radians(19))
        obj.location.z += 74
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -24, 74))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(-18, -252, 136), rotation=(math.radians(62), 0, math.radians(-4)))
    camera = bpy.context.object
    camera.data.lens = 56
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-128, -136, 202))
    key = bpy.context.object
    key.data.energy = 7300
    key.data.color = (1.0, 0.45, 0.43)
    key.data.size = 150
    bpy.ops.object.light_add(type="POINT", location=(120, 72, 136))
    rim = bpy.context.object
    rim.data.energy = 2300
    rim.data.color = (0.72, 0.0, 0.08)
    rim.data.shadow_soft_size = 90
    bpy.ops.object.light_add(type="AREA", location=(0, -196, 112))
    fill = bpy.context.object
    fill.data.energy = 650
    fill.data.color = (1.0, 0.58, 0.58)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("alveolar_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 74), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "alveolar_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(mat)


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


def export_glb(objects: list[bpy.types.Object]) -> None:
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_selection=True)


def render_outputs() -> None:
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(RENDER_PATH)
    bpy.context.scene.render.film_transparent = True
    bpy.ops.render.render(write_still=True)
    add_preview_backdrop()
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.context.scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main() -> None:
    clear_scene()
    objects = add_parts()
    setup_scene(objects)
    export_stl(objects)
    export_glb(objects)
    render_outputs()
    print(f"Generated {STL_PATH}")
    print(f"Generated {GLB_PATH}")
    print(f"Generated {RENDER_PATH}")
    print(f"Generated {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
