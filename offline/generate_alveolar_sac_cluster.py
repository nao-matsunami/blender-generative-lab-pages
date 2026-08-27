"""Generate Alveolar Sac Cluster assets in Blender.

On the Mac mini workflow, keep Blender open and submit this through:
npm run job:alveolar

Outputs:
- exports/stl/alveolar-sac-cluster.stl
- exports/glb/alveolar-sac-cluster.glb
- renders/alveolar-sac-cluster.png
- renders/alveolar-sac-cluster-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

STL_PATH = ROOT / "exports" / "stl" / "alveolar-sac-cluster.stl"
GLB_PATH = ROOT / "exports" / "glb" / "alveolar-sac-cluster.glb"
RENDER_PATH = ROOT / "renders" / "alveolar-sac-cluster.png"
PREVIEW_PATH = ROOT / "renders" / "alveolar-sac-cluster-preview.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name: str, color: tuple[float, float, float, float], roughness: float = 0.28) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = color[3]
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (color[0] * 0.16, color[1] * 0.08, color[2] * 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.07
    return material


def sac_positions() -> list[tuple[Vector, tuple[float, float, float]]]:
    data = []
    for i in range(18):
        angle = i / 18 * math.tau
        ring = 32 + 7 * math.sin(i * 1.7)
        z = 12 * math.sin(i * 1.31) + (i % 3 - 1) * 7
        x = math.cos(angle) * ring + 8 * math.sin(i * 0.9)
        y = math.sin(angle) * ring * 0.72 + 5 * math.cos(i * 1.4)
        scale = (
            13 + (i % 4) * 1.4,
            10 + ((i + 2) % 5) * 1.1,
            9 + ((i + 1) % 4) * 1.2,
        )
        data.append((Vector((x, y, z)), scale))
    data.append((Vector((0, 0, -3)), (18, 14, 12)))
    data.append((Vector((12, -7, 13)), (15, 11, 10)))
    return data


def create_sac(center: Vector, scale: tuple[float, float, float], index: int, sac_material: bpy.types.Material, dark_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=center)
    sac = bpy.context.object
    sac.name = f"alveolar_sac_{index:02d}"
    sac.scale = scale
    sac.rotation_euler = (math.radians(index * 17 % 31), math.radians(index * 29 % 23), math.radians(index * 41))
    sac.data.materials.append(sac_material)
    bpy.ops.object.shade_smooth()
    displace = sac.modifiers.new("soft_alveolar_dimples", "DISPLACE")
    texture = bpy.data.textures.new(f"alveolar_dimple_noise_{index:02d}", "VORONOI")
    texture.noise_scale = 1.85
    texture.intensity = 0.24
    displace.texture = texture
    displace.strength = 0.65
    bevel = sac.modifiers.new("soft_sac_skin", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 1
    objects.append(sac)

    inward = (-center).normalized() if center.length > 0.001 else Vector((0, -1, 0))
    hole_center = center + inward * (scale[0] * 0.72)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=hole_center)
    hole = bpy.context.object
    hole.name = f"alveolar_dark_mouth_{index:02d}"
    hole.scale = (scale[0] * 0.22, scale[1] * 0.16, scale[2] * 0.12)
    hole.data.materials.append(dark_material)
    bpy.ops.object.shade_smooth()
    objects.append(hole)
    return objects


def create_tube_between(start: Vector, end: Vector, radius: float, material: bpy.types.Material, name: str) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 18
    curve.bevel_depth = radius
    curve.bevel_resolution = 6
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(2)
    midpoint = (start + end) * 0.5 + Vector((0, 0, 8 * math.sin(start.x * 0.03)))
    for point, co in zip(spline.bezier_points, (start, midpoint, end)):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_cluster() -> list[bpy.types.Object]:
    sac_material = make_material("alveolar_wet_rose_membrane", (0.86, 0.30, 0.37, 1.0), 0.18)
    tube_material = make_material("alveolar_bronchial_dark_red", (0.30, 0.018, 0.06, 1.0), 0.2)
    dark_material = make_material("alveolar_inner_dark_holes", (0.035, 0.002, 0.012, 1.0), 0.44)
    objects = []
    positions = sac_positions()
    for index, (center, scale) in enumerate(positions):
        objects.extend(create_sac(center, scale, index, sac_material, dark_material))
    root = Vector((0, -58, 6))
    branch_a = Vector((-16, -28, 6))
    branch_b = Vector((18, -26, 0))
    objects.append(create_tube_between(root, branch_a, 4.2, tube_material, "alveolar_bronchial_root_a"))
    objects.append(create_tube_between(root, branch_b, 3.8, tube_material, "alveolar_bronchial_root_b"))
    for index, (center, _scale) in enumerate(positions[:18]):
        anchor = branch_a if index % 2 == 0 else branch_b
        objects.append(create_tube_between(anchor, center * 0.72, 1.25 + (index % 3) * 0.2, tube_material, f"alveolar_capillary_branch_{index:02d}"))
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
    scene.view_settings.exposure = 1.55
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    for obj in objects:
        obj.location.z += 72
        obj.rotation_euler.rotate_axis("Z", math.radians(-14))
        obj.rotation_euler.rotate_axis("X", math.radians(38))

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 82))
    target = bpy.context.object
    target.name = "alveolar_cluster_target"

    bpy.ops.object.camera_add(location=(0, -206, 142), rotation=(math.radians(62), 0, 0))
    camera = bpy.context.object
    camera.name = "alveolar_cluster_camera"
    camera.data.lens = 70
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-134, -130, 182))
    key = bpy.context.object
    key.name = "alveolar_warm_key"
    key.data.energy = 5600
    key.data.color = (1.0, 0.52, 0.5)
    key.data.size = 145

    bpy.ops.object.light_add(type="POINT", location=(132, 78, 132))
    rim = bpy.context.object
    rim.name = "alveolar_dark_red_rim"
    rim.data.color = (0.74, 0.04, 0.13)
    rim.data.energy = 1600
    rim.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(0, -220, 112))
    front = bpy.context.object
    front.name = "alveolar_soft_fill"
    front.data.energy = 980
    front.data.color = (1.0, 0.68, 0.62)
    front.data.size = 230


def add_preview_backdrop() -> None:
    material = make_material("alveolar_preview_dark_backdrop", (0.008, 0.001, 0.004, 1.0), 0.94)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "alveolar_preview_dark_backdrop"
    backdrop.dimensions = (900, 900, 1)
    backdrop.data.materials.append(material)


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
    objects = create_cluster()
    setup_scene(objects)
    export_stl(objects)
    export_glb()
    render_still()


if __name__ == "__main__":
    main()
