"""Generate Adhesive Spleen Fold assets in Blender.

Mac mini workflow:
npm run job:spleen

Outputs:
- exports/stl/adhesive-spleen-fold.stl
- exports/glb/adhesive-spleen-fold.glb
- renders/adhesive-spleen-fold.png
- renders/adhesive-spleen-fold-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "adhesive-spleen-fold"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

U_SEGMENTS = 168
V_SEGMENTS = 86


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def seam_field(u: float, v: float, offset: float) -> float:
    theta = u * math.tau
    band = 0.0
    for index in range(5):
        center = 0.18 + index * 0.16 + 0.045 * math.sin(theta * 1.4 + offset)
        distance = abs(v - center)
        band += max(0.0, 1.0 - distance / 0.045) ** 2.3
    pinch = math.exp(-1.0 * (((math.sin(theta - 0.4) + 1.0) / 0.34) ** 2 + ((v - 0.48) / 0.23) ** 2))
    edge = smoothstep(0.72, 1.0, abs(math.cos(theta)))
    return min(1.0, band * 0.5 + pinch * 0.85 + edge * 0.24)


def lobe_point(u: float, v: float, lobe_index: int, lift: float = 0.0) -> Vector:
    theta = u * math.tau
    phi = -math.pi / 2.0 + v * math.pi
    dome = max(0.0, math.cos(phi))
    offset = lobe_index * 0.9
    seam = seam_field(u, v, offset)
    squash = 1.0 - 0.18 * seam
    rx = 42.0 * squash * (1.0 + 0.06 * math.sin(theta * 3.0 + offset))
    ry = 21.0 * squash * (1.0 + 0.08 * math.cos(theta * 2.0 - offset))
    rz = 46.0 * (1.0 + 0.08 * math.sin(theta * 2.0 + offset))
    x = math.cos(theta) * dome * rx
    y = math.sin(theta) * dome * ry
    z = math.sin(phi) * rz
    x += (lobe_index - 1.0) * 29.0
    y += 5.5 * math.sin((lobe_index + 1) * 0.8)
    z += 4.0 * math.sin(theta - 0.5) * dome
    if lobe_index == 0:
        x -= 7.0 * smoothstep(0.42, 1.0, v)
    if lobe_index == 2:
        x += 9.0 * smoothstep(0.0, 0.58, v)
    point = Vector((x, y, z))
    outward = point.normalized() if point.length > 0.001 else Vector((0, 0, 1))
    return point + outward * lift


def color_at(u: float, v: float, lobe_index: int) -> tuple[float, float, float, float]:
    seam = seam_field(u, v, lobe_index * 0.9)
    theta = u * math.tau
    wet = 0.5 + 0.5 * math.sin(theta * 2.8 + v * math.tau * 2.0 + lobe_index)
    base = (0.68 + wet * 0.13, 0.18 + wet * 0.06, 0.28 + wet * 0.07)
    dark = (0.12, 0.004, 0.042)
    pale = (0.88, 0.34, 0.38)
    seam_mix = min(0.82, seam * 0.86)
    highlight = smoothstep(0.58, 1.0, math.sin(theta - 0.3)) * 0.1
    mixed = tuple(base[i] * (1.0 - seam_mix) + dark[i] * seam_mix for i in range(3))
    return tuple(mixed[i] * (1.0 - highlight) + pale[i] * highlight for i in range(3)) + (1.0,)


def create_lobe(lobe_index: int) -> bpy.types.Object:
    vertices = []
    colors = []
    faces = []
    for y_index in range(V_SEGMENTS + 1):
        v = y_index / V_SEGMENTS
        for x_index in range(U_SEGMENTS):
            u = x_index / U_SEGMENTS
            vertices.append(tuple(lobe_point(u, v, lobe_index)))
            colors.append(color_at(u, v, lobe_index))
    for y_index in range(V_SEGMENTS):
        for x_index in range(U_SEGMENTS):
            a = y_index * U_SEGMENTS + x_index
            b = y_index * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            c = (y_index + 1) * U_SEGMENTS + ((x_index + 1) % U_SEGMENTS)
            d = (y_index + 1) * U_SEGMENTS + x_index
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(f"adhesive_spleen_lobe_{lobe_index}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="spleen_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new(f"Adhesive Spleen Lobe {lobe_index}", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("spleen_wet_membrane")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = material.node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "spleen_skin_color"
        material.node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.19
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.10, 0.004, 0.04, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.07
    return material


def make_material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
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
            bsdf.inputs["Emission Color"].default_value = (color[0] * 0.12, color[1] * 0.05, color[2] * 0.08, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.06
    return material


def add_dark_contact_slits(dark_material: bpy.types.Material, lip_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    slits = [(-15, -15, 8, 21, 3.0, 8), (17, -13, 9, 20, 2.8, 8)]
    for index, (x, y, z, sx, sy, sz) in enumerate(slits):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=56, ring_count=18, radius=1, location=(x, y, z))
        slit = bpy.context.object
        slit.name = f"spleen_dark_adhesion_slit_{index:02d}"
        slit.scale = (sx, sy, sz)
        slit.rotation_euler = (math.radians(0), math.radians(3 + index * 4), math.radians(6 - index * 7))
        slit.data.materials.append(dark_material)
        bpy.ops.object.shade_smooth()
        objects.append(slit)

        bpy.ops.mesh.primitive_torus_add(major_radius=sx * 0.9, minor_radius=1.4, major_segments=96, minor_segments=12, location=(x, y - 0.8, z))
        lip = bpy.context.object
        lip.name = f"spleen_compressed_lip_{index:02d}"
        lip.scale = (1.0, 0.15, max(0.25, sz / sx))
        lip.rotation_euler = (math.radians(90), math.radians(3 + index * 4), math.radians(6 - index * 7))
        lip.data.materials.append(lip_material)
        bpy.ops.object.shade_smooth()
        objects.append(lip)
    return objects


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "MESH":
        bpy.ops.object.shade_smooth()
        weighted = obj.modifiers.new("spleen_weighted_normals", "WEIGHTED_NORMAL")
        if weighted:
            weighted.keep_sharp = True
    obj.select_set(False)


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
    scene.view_settings.gamma = 1.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)

    for obj in objects:
        obj.rotation_euler.rotate_axis("Z", math.radians(-9))
        obj.rotation_euler.rotate_axis("X", math.radians(42))
        obj.location.z += 72

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -2, 72))
    target = bpy.context.object
    target.name = "spleen_camera_target"

    bpy.ops.object.camera_add(location=(-4, -254, 132), rotation=(math.radians(62), 0, math.radians(-1)))
    camera = bpy.context.object
    camera.name = "spleen_camera"
    camera.data.lens = 52
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-128, -130, 188))
    key = bpy.context.object
    key.name = "spleen_warm_key"
    key.data.energy = 5700
    key.data.color = (1.0, 0.52, 0.52)
    key.data.size = 160

    bpy.ops.object.light_add(type="POINT", location=(120, 76, 132))
    rim = bpy.context.object
    rim.name = "spleen_dark_red_rim"
    rim.data.energy = 1800
    rim.data.color = (0.72, 0.03, 0.12)
    rim.data.shadow_soft_size = 88

    bpy.ops.object.light_add(type="AREA", location=(0, -188, 104))
    fill = bpy.context.object
    fill.name = "spleen_soft_front"
    fill.data.energy = 820
    fill.data.color = (1.0, 0.64, 0.62)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    material = make_material("spleen_preview_dark_backdrop", (0.007, 0.001, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 72), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "spleen_preview_dark_backdrop"
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
    skin = material_from_attribute()
    dark = make_material("spleen_internal_dark", (0.016, 0.001, 0.008, 1.0), 0.52)
    lip = make_material("spleen_compressed_lip_skin", (0.72, 0.14, 0.25, 1.0), 0.17)
    objects = []
    for index in range(3):
        lobe = create_lobe(index)
        lobe.data.materials.append(skin)
        objects.append(lobe)
    objects.extend(add_dark_contact_slits(dark, lip))
    for obj in objects:
        prepare_object(obj)
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
