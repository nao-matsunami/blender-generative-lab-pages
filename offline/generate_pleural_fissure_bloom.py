"""Generate Pleural Fissure Bloom assets in Blender.

Mac mini workflow:
npm run job:pleural
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "pleural-fissure-bloom"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 104
V_SEGMENTS = 58


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


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


def create_lobe_mesh(side: float, material: bpy.types.Material) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    for v_index in range(V_SEGMENTS + 1):
        v = v_index / V_SEGMENTS
        phi = -math.pi / 2.0 + v * math.pi
        dome = max(0.0, math.cos(phi))
        for u_index in range(U_SEGMENTS):
            u = u_index / U_SEGMENTS
            theta = u * math.tau
            front = 0.5 + 0.5 * math.sin(theta)
            inner = 0.5 + 0.5 * (-side * math.cos(theta))
            fissure = smoothstep(0.32, 0.88, inner) * math.exp(-((v - 0.53) / 0.25) ** 2)
            pleat = 0.0
            for i in range(7):
                center = (i / 7.0 + 0.13 * v + 0.04 * side) % 1.0
                distance = abs(((u - center + 0.5) % 1.0) - 0.5)
                pleat += max(0.0, 1.0 - distance / 0.045) ** 2.0
            rx = 34.0 * (1.0 - 0.2 * fissure) + pleat * 1.7
            ry = 20.0 * (1.0 + 0.12 * front) - fissure * 6.0
            rz = 56.0 * (1.0 - 0.08 * abs(math.sin(theta * 1.5)))
            x = side * 27.0 + math.cos(theta) * dome * rx
            y = math.sin(theta) * dome * ry - fissure * 11.0
            z = math.sin(phi) * rz + dome * math.sin(theta * 2.0 + side) * 4.2
            z += fissure * math.sin(v * math.pi) * 7.0
            vertices.append((x, y, z))

    for v_index in range(V_SEGMENTS):
        for u_index in range(U_SEGMENTS):
            a = v_index * U_SEGMENTS + u_index
            b = v_index * U_SEGMENTS + ((u_index + 1) % U_SEGMENTS)
            c = (v_index + 1) * U_SEGMENTS + ((u_index + 1) % U_SEGMENTS)
            d = (v_index + 1) * U_SEGMENTS + u_index
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(f"pleural_lobe_{side}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Left Pleural Lobe" if side < 0 else "Right Pleural Lobe", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    weighted = obj.modifiers.new("pleural_weighted_normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    obj.select_set(False)
    return obj


def add_dark_fissure(material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    specs = [
        ((0, -18, 0), (12, 5, 36), (0, 0, 0)),
        ((-17, -18, 19), (8, 4, 29), (math.radians(25), 0, math.radians(-18))),
        ((17, -18, 19), (8, 4, 29), (math.radians(25), 0, math.radians(18))),
    ]
    for index, (location, scale, rotation) in enumerate(specs):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=24, radius=1, location=location, rotation=rotation)
        cleft = bpy.context.object
        cleft.name = f"pleural_dark_bronchial_cleft_{index + 1}"
        cleft.scale = scale
        cleft.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        objects.append(cleft)
    return objects


def add_contact_ridge(material: bpy.types.Material) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=18, radius=1, location=(side * 9, -16, 3))
        ridge = bpy.context.object
        ridge.name = "pleural_thick_contact_ridge"
        ridge.scale = (9, 4, 32)
        ridge.rotation_euler = (math.radians(8), 0, math.radians(side * 8))
        ridge.data.materials.append(material)
        bpy.ops.object.shade_smooth()
        objects.append(ridge)
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
    scene.view_settings.exposure = 1.5
    scene.view_settings.gamma = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0, 0, 0)

    for obj in objects:
        obj.rotation_euler.rotate_axis("X", math.radians(17))
        obj.rotation_euler.rotate_axis("Z", math.radians(-8))
        obj.location.z += 72

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -10, 75))
    target = bpy.context.object
    target.name = "pleural_camera_target"
    bpy.ops.object.camera_add(location=(-24, -248, 128), rotation=(math.radians(62), 0, math.radians(-6)))
    camera = bpy.context.object
    camera.data.lens = 52
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-122, -130, 194))
    key = bpy.context.object
    key.data.energy = 6400
    key.data.color = (1.0, 0.55, 0.52)
    key.data.size = 150
    bpy.ops.object.light_add(type="POINT", location=(128, 74, 138))
    rim = bpy.context.object
    rim.data.energy = 2100
    rim.data.color = (0.78, 0.02, 0.12)
    rim.data.shadow_soft_size = 88
    bpy.ops.object.light_add(type="AREA", location=(0, -190, 96))
    fill = bpy.context.object
    fill.data.energy = 760
    fill.data.color = (1.0, 0.64, 0.61)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    mat = make_material("pleural_preview_dark_backdrop", (0.006, 0.001, 0.003, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "pleural_preview_dark_backdrop"
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
    lobe_material = make_material("wet_pleural_lobe", (0.78, 0.24, 0.34, 1.0), 0.18, 0.05)
    ridge_material = make_material("pressed_pink_contact_ridge", (0.9, 0.36, 0.40, 1.0), 0.16, 0.04)
    dark_material = make_material("near_black_bronchial_fissure", (0.005, 0.0, 0.003, 1.0), 0.62)
    objects: list[bpy.types.Object] = [
        create_lobe_mesh(-1.0, lobe_material),
        create_lobe_mesh(1.0, lobe_material),
    ]
    objects.extend(add_contact_ridge(ridge_material))
    objects.extend(add_dark_fissure(dark_material))
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
