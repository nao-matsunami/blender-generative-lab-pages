"""Generate Ossuary Reef Lattice assets in Blender.

Mac mini workflow:
npm run job:ossuary
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "ossuary-reef-lattice"
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


def shade(obj: bpy.types.Object) -> bpy.types.Object:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    obj.modifiers.new(obj.name + "_weighted_normals", "WEIGHTED_NORMAL")
    return obj


def add_torus(name: str, loc: tuple[float, float, float], major: float, minor: float, scale: tuple[float, float, float], rot: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_segments=128, minor_segments=18, major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return shade(obj)


def add_sphere(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=18, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return shade(obj)


def add_cylinder_between(name: str, start: tuple[float, float, float], end: tuple[float, float, float], radius: float, material: bpy.types.Material) -> bpy.types.Object:
    a = Vector(start)
    b = Vector(end)
    mid = (a + b) * 0.5
    direction = b - a
    length = direction.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return shade(obj)


def ring_point(level: int, angle: float) -> tuple[float, float, float]:
    z = -46 + level * 18
    radius_x = 34 + math.sin(level * 1.3) * 6
    radius_y = 22 + math.cos(level * 1.7) * 5
    twist = level * 0.38
    return (
        math.cos(angle + twist) * radius_x,
        math.sin(angle + twist) * radius_y,
        z,
    )


def add_parts() -> list[bpy.types.Object]:
    bone = make_material("warm_bone_calcified_lattice", (0.78, 0.66, 0.49, 1.0), 0.52, 0.015)
    ochre = make_material("ochre_fossil_rib_edges", (0.58, 0.38, 0.18, 1.0), 0.58, 0.01)
    dark = make_material("violet_black_inner_voids", (0.035, 0.018, 0.026, 1.0), 0.8)
    crimson = make_material("deep_crimson_shadow_marrow", (0.28, 0.02, 0.035, 1.0), 0.42, 0.03)

    objects: list[bpy.types.Object] = []
    for level in range(6):
        z = -46 + level * 18
        major = 27 + math.sin(level * 1.1) * 4
        minor = 2.2 + (level % 2) * 0.45
        rot = (math.radians(5 + level * 4), math.radians(-8 + level * 3), math.radians(level * 23))
        scale = (1.18 + math.sin(level) * 0.13, 0.76 + math.cos(level * 0.7) * 0.08, 1)
        objects.append(add_torus(f"ossuary_open_elliptic_bone_ring_{level + 1}", (0, 0, z), major, minor, scale, rot, bone if level % 2 else ochre))

    angles = [math.radians(a) for a in range(0, 360, 40)]
    for level in range(5):
        for index, angle in enumerate(angles):
            if (index + level) % 3 == 1:
                continue
            objects.append(add_cylinder_between(f"ossuary_bridge_rib_{level + 1}_{index + 1}", ring_point(level, angle), ring_point(level + 1, angle + 0.24), 1.65, bone))

    for index, angle in enumerate(angles):
        if index % 2 == 0:
            objects.append(add_cylinder_between(f"ossuary_diagonal_fossil_strut_{index + 1}", ring_point(0, angle), ring_point(5, angle + 0.72), 1.15, ochre))

    for level in range(6):
        for index, angle in enumerate((0.4, 1.8, 3.2, 4.6)):
            x, y, z = ring_point(level, angle + level * 0.19)
            material = dark if index % 2 == 0 else crimson
            objects.append(add_sphere(f"ossuary_dark_pore_shadow_{level + 1}_{index + 1}", (x * 0.74, y * 0.74, z + math.sin(angle) * 3), (3.4, 1.4, 2.4), material))

    objects.append(add_sphere("ossuary_deep_recessed_core_shadow", (0, 0, 0), (14, 10, 42), dark))
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
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.15
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0, 0, 0)
    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-17))
        obj.rotation_euler.rotate_axis("X", math.radians(12))
        obj.location.z += 72
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 72))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(-78, -228, 140), rotation=(math.radians(62), 0, math.radians(-16)))
    camera = bpy.context.object
    camera.data.lens = 62
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target
    bpy.ops.object.light_add(type="AREA", location=(-130, -150, 230))
    key = bpy.context.object
    key.data.energy = 6200
    key.data.color = (1.0, 0.72, 0.48)
    key.data.size = 145
    bpy.ops.object.light_add(type="POINT", location=(115, 92, 150))
    rim = bpy.context.object
    rim.data.energy = 2100
    rim.data.color = (0.55, 0.05, 0.08)
    rim.data.shadow_soft_size = 80
    bpy.ops.object.light_add(type="AREA", location=(0, -190, 95))
    fill = bpy.context.object
    fill.data.energy = 430
    fill.data.color = (0.85, 0.62, 0.42)
    fill.data.size = 260


def add_preview_backdrop() -> None:
    mat = make_material("ossuary_preview_coal_backdrop", (0.006, 0.005, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 160, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "ossuary_preview_coal_backdrop"
    backdrop.dimensions = (920, 920, 1)
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
