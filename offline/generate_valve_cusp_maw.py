"""Generate Valve Cusp Maw assets in Blender.

Mac mini workflow:
npm run job:valvecusp
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "valve-cusp-maw"
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


def create_cusp_mesh(index: int, material: bpy.types.Material) -> bpy.types.Object:
    center_angle = index * math.tau / 3.0 + math.radians(18)
    angle_span = math.radians(118)
    radial_segments = 28
    angle_segments = 56
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []

    for r_index in range(radial_segments + 1):
        t = r_index / radial_segments
        for a_index in range(angle_segments + 1):
            side = (a_index / angle_segments - 0.5) * 2.0
            edge_falloff = max(0.0, 1.0 - abs(side) ** 2.8)
            theta = center_angle + side * angle_span * 0.5
            inner_radius = 18.0 + 3.0 * math.sin(index + side * math.pi)
            outer_radius = 62.0 + 4.0 * math.sin(index * 1.7 + side * 2.1)
            radius = inner_radius + (outer_radius - inner_radius) * t
            fold = math.sin(t * math.pi) * edge_falloff
            crease = math.sin(side * math.pi * 2.0 + index * 0.8) * (1.0 - t) * 5.0
            x = math.cos(theta) * (radius + fold * 4.0)
            z = math.sin(theta) * (radius * 0.82 + fold * 7.0)
            y = -18.0 * (1.0 - t) ** 1.7 - 4.0 * fold + crease
            y += math.sin(theta * 3.0 + t * 2.0) * 2.4
            vertices.append((x, y, z))

    for r_index in range(radial_segments):
        for a_index in range(angle_segments):
            row = angle_segments + 1
            a = r_index * row + a_index
            b = a + 1
            c = (r_index + 1) * row + a_index + 1
            d = (r_index + 1) * row + a_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(f"valve_cusp_{index}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"Valve Cusp {index + 1}", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    solidify = obj.modifiers.new("cusp_print_thickness", "SOLIDIFY")
    solidify.thickness = 3.2
    solidify.offset = 0.0
    weighted = obj.modifiers.new("cusp_weighted_normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    obj.select_set(False)
    return obj


def add_annulus(material: bpy.types.Material, dark_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    bpy.ops.mesh.primitive_torus_add(major_radius=39, minor_radius=8.6, major_segments=160, minor_segments=24, location=(0, 1, 0))
    annulus = bpy.context.object
    annulus.name = "valve_cusp_thick_annulus"
    annulus.rotation_euler = (math.radians(90), 0, 0)
    annulus.scale = (1.08, 1.0, 0.8)
    annulus.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    objects.append(annulus)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=32, radius=1, location=(0, -22, 0))
    cavity = bpy.context.object
    cavity.name = "valve_cusp_dark_inner_chamber"
    cavity.scale = (22, 8, 16)
    cavity.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(cavity)
    return objects


def add_compression_lobes(material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for index in range(3):
        theta = index * math.tau / 3.0 + math.radians(44)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=24, radius=1, location=(math.cos(theta) * 43, 5, math.sin(theta) * 34))
        lobe = bpy.context.object
        lobe.name = f"valve_cusp_pressed_outer_lobe_{index + 1}"
        lobe.scale = (18, 7, 13)
        lobe.rotation_euler = (0, math.radians(0), theta)
        lobe.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        objects.append(lobe)
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
    scene.view_settings.exposure = 1.45
    scene.view_settings.gamma = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0, 0, 0)

    for obj in objects:
        obj.rotation_euler.rotate_axis("X", math.radians(16))
        obj.rotation_euler.rotate_axis("Z", math.radians(-10))
        obj.location.z += 72

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -5, 72))
    target = bpy.context.object
    target.name = "valve_cusp_camera_target"
    bpy.ops.object.camera_add(location=(-22, -242, 124), rotation=(math.radians(61), 0, math.radians(-6)))
    camera = bpy.context.object
    camera.data.lens = 50
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-124, -128, 180))
    key = bpy.context.object
    key.data.energy = 6200
    key.data.color = (1.0, 0.48, 0.42)
    key.data.size = 135
    bpy.ops.object.light_add(type="POINT", location=(112, 70, 132))
    rim = bpy.context.object
    rim.data.energy = 2100
    rim.data.color = (0.78, 0.02, 0.10)
    rim.data.shadow_soft_size = 84
    bpy.ops.object.light_add(type="AREA", location=(0, -184, 92))
    fill = bpy.context.object
    fill.data.energy = 640
    fill.data.color = (1.0, 0.62, 0.57)
    fill.data.size = 210


def add_preview_backdrop() -> None:
    mat = make_material("valve_cusp_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "valve_cusp_preview_dark_backdrop"
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
    cusp_material = make_material("wet_dark_crimson_cusps", (0.58, 0.08, 0.16, 1.0), 0.16, 0.06)
    annulus_material = make_material("thick_pink_annulus", (0.86, 0.30, 0.34, 1.0), 0.2, 0.04)
    lobe_material = make_material("pressed_flesh_lobes", (0.68, 0.18, 0.24, 1.0), 0.24, 0.03)
    dark_material = make_material("near_black_inner_chamber", (0.006, 0.0, 0.003, 1.0), 0.62)
    objects: list[bpy.types.Object] = []
    objects.extend(add_annulus(annulus_material, dark_material))
    objects.extend(add_compression_lobes(lobe_material))
    for index in range(3):
        objects.append(create_cusp_mesh(index, cusp_material))
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
