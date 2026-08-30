"""Generate Pancreatic Membrane Slab assets in Blender.

Mac mini workflow:
npm run job:pancreatic

Outputs:
- exports/stl/pancreatic-membrane-slab.stl
- exports/glb/pancreatic-membrane-slab.glb
- renders/pancreatic-membrane-slab.png
- renders/pancreatic-membrane-slab-preview.png
"""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "pancreatic-membrane-slab"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"

X_SEGMENTS = 154
Y_SEGMENTS = 72


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def slab_width(t: float) -> float:
    head = 1.0 + 0.72 * math.exp(-1.0 * ((t + 0.72) / 0.28) ** 2)
    tail = 1.0 - 0.36 * smoothstep(0.35, 0.95, t)
    waist = 1.0 - 0.22 * math.exp(-1.0 * ((t + 0.08) / 0.18) ** 2)
    return 26.0 * head * tail * waist


def fold_field(t: float, s: float) -> float:
    field = 0.0
    for index in range(9):
        center = -0.82 + index * 0.21 + 0.05 * math.sin(s * math.pi * 2.0)
        distance = abs(t - center)
        field += max(0.0, 1.0 - distance / 0.055) ** 2.2
    edge_grip = max(0.0, abs(s) - 0.62) / 0.38
    cleft = math.exp(-1.0 * (((t + 0.32) / 0.12) ** 2 + (s / 0.28) ** 2))
    return min(1.0, field * 0.45 + edge_grip * 0.48 + cleft * 0.78)


def surface_point(t: float, s: float, side: float, lift: float = 0.0) -> Vector:
    width = slab_width(t)
    edge = max(0.0, abs(s))
    fold = fold_field(t, s)
    x = t * 76.0
    y = s * width
    center_curve = 13.0 * math.sin((t + 0.16) * math.pi * 0.92)
    z_center = center_curve + 4.0 * math.sin(t * math.pi * 4.0) * (1.0 - edge)
    thickness = 7.0 + 5.5 * (1.0 - edge) + fold * 5.5
    z = z_center + side * thickness
    y += 4.0 * math.sin(t * math.pi * 3.0 + side * 0.8) * (1.0 - edge)
    point = Vector((x, y, z))
    normal = Vector((0.0, 0.0, side))
    return point + normal * lift


def color_at(t: float, s: float, side: float) -> tuple[float, float, float, float]:
    fold = fold_field(t, s)
    wet = 0.5 + 0.5 * math.sin(t * math.pi * 5.5 + s * 3.0)
    base = (0.72 + wet * 0.14, 0.25 + wet * 0.07, 0.31 + wet * 0.07)
    dark = (0.16, 0.006, 0.04)
    pale = (0.94, 0.46, 0.43)
    crease = min(0.82, fold * 0.88)
    highlight = max(0.0, side) * smoothstep(0.44, 0.95, math.sin(t * math.pi * 2.4 - 0.6)) * 0.12
    mixed = tuple(base[i] * (1.0 - crease) + dark[i] * crease for i in range(3))
    return tuple(mixed[i] * (1.0 - highlight) + pale[i] * highlight for i in range(3)) + (1.0,)


def create_slab_mesh() -> bpy.types.Object:
    vertices = []
    colors = []
    faces = []
    for side in (1.0, -1.0):
        side_offset = len(vertices)
        for y_index in range(Y_SEGMENTS + 1):
            s = -1.0 + 2.0 * y_index / Y_SEGMENTS
            for x_index in range(X_SEGMENTS + 1):
                t = -1.0 + 2.0 * x_index / X_SEGMENTS
                vertices.append(tuple(surface_point(t, s, side)))
                colors.append(color_at(t, s, side))
        for y_index in range(Y_SEGMENTS):
            for x_index in range(X_SEGMENTS):
                a = side_offset + y_index * (X_SEGMENTS + 1) + x_index
                b = a + 1
                c = a + X_SEGMENTS + 2
                d = a + X_SEGMENTS + 1
                faces.append((a, d, c, b) if side > 0 else (a, b, c, d))

    top_offset = 0
    bottom_offset = (Y_SEGMENTS + 1) * (X_SEGMENTS + 1)
    for x_index in range(X_SEGMENTS):
        top_a = top_offset + x_index
        top_b = top_offset + x_index + 1
        bottom_a = bottom_offset + x_index
        bottom_b = bottom_offset + x_index + 1
        faces.append((top_a, top_b, bottom_b, bottom_a))
        top_c = top_offset + Y_SEGMENTS * (X_SEGMENTS + 1) + x_index
        top_d = top_c + 1
        bottom_c = bottom_offset + Y_SEGMENTS * (X_SEGMENTS + 1) + x_index
        bottom_d = bottom_c + 1
        faces.append((top_c, bottom_c, bottom_d, top_d))

    for y_index in range(Y_SEGMENTS):
        top_a = top_offset + y_index * (X_SEGMENTS + 1)
        top_b = top_offset + (y_index + 1) * (X_SEGMENTS + 1)
        bottom_a = bottom_offset + y_index * (X_SEGMENTS + 1)
        bottom_b = bottom_offset + (y_index + 1) * (X_SEGMENTS + 1)
        faces.append((top_a, bottom_a, bottom_b, top_b))
        top_c = top_offset + y_index * (X_SEGMENTS + 1) + X_SEGMENTS
        top_d = top_offset + (y_index + 1) * (X_SEGMENTS + 1) + X_SEGMENTS
        bottom_c = bottom_offset + y_index * (X_SEGMENTS + 1) + X_SEGMENTS
        bottom_d = bottom_offset + (y_index + 1) * (X_SEGMENTS + 1) + X_SEGMENTS
        faces.append((top_c, top_d, bottom_d, bottom_c))

    mesh = bpy.data.meshes.new("pancreatic_membrane_slab_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    color_attribute = mesh.color_attributes.new(name="pancreatic_skin_color", type="BYTE_COLOR", domain="CORNER")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_attribute.data[loop_index].color = colors[mesh.loops[loop_index].vertex_index]
    obj = bpy.data.objects.new("Pancreatic Membrane Slab", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def material_from_attribute() -> bpy.types.Material:
    material = bpy.data.materials.new("pancreatic_wet_membrane")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        attribute = material.node_tree.nodes.new("ShaderNodeAttribute")
        attribute.attribute_name = "pancreatic_skin_color"
        material.node_tree.links.new(attribute.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.18
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.11, 0.006, 0.035, 1.0)
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


def add_dark_clefts(dark_material: bpy.types.Material, lip_material: bpy.types.Material) -> list[bpy.types.Object]:
    objects = []
    clefts = [(-24, -2, 8, 10, 2.6, 22), (8, 6, 12, 7, 2.2, 18), (42, -5, 8, 5.2, 1.8, 12)]
    for index, (x, y, z, sx, sy, sz) in enumerate(clefts):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=18, radius=1, location=(x, y, z))
        cleft = bpy.context.object
        cleft.name = f"pancreatic_dark_cleft_{index:02d}"
        cleft.scale = (sx, sy, sz)
        cleft.rotation_euler = (math.radians(6), math.radians(0), math.radians(8 + index * 6))
        cleft.data.materials.append(dark_material)
        bpy.ops.object.shade_smooth()
        objects.append(cleft)

        bpy.ops.mesh.primitive_torus_add(major_radius=sx * 0.78, minor_radius=1.25, major_segments=72, minor_segments=12, location=(x, y - 0.4, z))
        lip = bpy.context.object
        lip.name = f"pancreatic_fused_lip_{index:02d}"
        lip.scale = (1.0, 0.18, sz / max(1.0, sx) * 0.68)
        lip.rotation_euler = (math.radians(90), math.radians(0), math.radians(8 + index * 6))
        lip.data.materials.append(lip_material)
        bpy.ops.object.shade_smooth()
        objects.append(lip)
    return objects


def prepare_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type == "MESH":
        bpy.ops.object.shade_smooth()
        weighted = obj.modifiers.new("pancreatic_weighted_normals", "WEIGHTED_NORMAL")
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
        obj.rotation_euler.rotate_axis("Z", math.radians(-14))
        obj.rotation_euler.rotate_axis("X", math.radians(54))
        obj.location.z += 76

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-6, 0, 76))
    target = bpy.context.object
    target.name = "pancreatic_camera_target"

    bpy.ops.object.camera_add(location=(-12, -286, 136), rotation=(math.radians(62), 0, math.radians(-2)))
    camera = bpy.context.object
    camera.name = "pancreatic_camera"
    camera.data.lens = 44
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    constraint.target = target

    bpy.ops.object.light_add(type="AREA", location=(-132, -124, 182))
    key = bpy.context.object
    key.name = "pancreatic_warm_key"
    key.data.energy = 5600
    key.data.color = (1.0, 0.54, 0.52)
    key.data.size = 160

    bpy.ops.object.light_add(type="POINT", location=(124, 70, 126))
    rim = bpy.context.object
    rim.name = "pancreatic_dark_red_rim"
    rim.data.energy = 1750
    rim.data.color = (0.72, 0.03, 0.11)
    rim.data.shadow_soft_size = 90

    bpy.ops.object.light_add(type="AREA", location=(0, -186, 98))
    fill = bpy.context.object
    fill.name = "pancreatic_soft_front"
    fill.data.energy = 820
    fill.data.color = (1.0, 0.66, 0.62)
    fill.data.size = 230


def add_preview_backdrop() -> None:
    material = make_material("pancreatic_preview_dark_backdrop", (0.007, 0.001, 0.004, 1.0), 0.95)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 150, 76), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "pancreatic_preview_dark_backdrop"
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
    dark = make_material("pancreatic_internal_dark", (0.018, 0.001, 0.008, 1.0), 0.52)
    lip = make_material("pancreatic_fused_lip_skin", (0.78, 0.20, 0.28, 1.0), 0.17)
    slab = create_slab_mesh()
    slab.data.materials.append(skin)
    objects = [slab]
    objects.extend(add_dark_clefts(dark, lip))
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
