"""Generate Processional Aperture Engine assets in Blender GUI."""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1])).resolve()
SLUG = "processional-aperture-engine"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name, color, roughness, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def add_surface_texture(mat, scale, strength, distance):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.68
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def bevel(obj, width=1.2, segments=4):
    modifier = obj.modifiers.new("worked_edge", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    return smooth(obj)


def add_torus(name, major, minor, location, rotation, mat, parent=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=144,
        minor_segments=28,
        major_radius=major,
        minor_radius=minor,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    return smooth(obj)


def add_arc(name, center, radius, start, end, depth, mat, parent=None, y=0.0):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = depth
    curve.bevel_resolution = 8
    spline = curve.splines.new("POLY")
    steps = 72
    spline.points.add(steps)
    for index in range(steps + 1):
        t = start + (end - start) * index / steps
        wobble = math.sin(t * 3.0 + 0.7) * 1.2
        r = radius + wobble
        spline.points[index].co = (center[0] + math.cos(t) * r, y, center[2] + math.sin(t) * r, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def add_box(name, location, scale, rotation, mat, parent=None, width=1.4):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel(obj, width, 5)


def add_handle(name, points, depth, mat):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 18
    curve.bevel_depth = depth
    curve.bevel_resolution = 8
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinates in zip(spline.bezier_points, points):
        point.co = coordinates
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_membrane_rib(name, angle, mat, parent):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = 4.6
    curve.bevel_resolution = 8
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(3)
    radial = [(18, -4, 4), (29, -8, 12), (37, -5, 3), (44, -1, -7)]
    c, s = math.cos(angle), math.sin(angle)
    for point, (r, y, tangent) in zip(spline.bezier_points, radial):
        point.co = (c * r - s * tangent, y, s * r + c * tangent)
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def add_membrane_leaf(name, location, scale, rotation, mat, parent):
    vertices = [
        (-1.0, -0.5, -0.62), (1.0, -0.5, -0.32), (0.82, -0.5, 0.58), (-0.78, -0.5, 0.78),
        (-1.0, 0.5, -0.62), (1.0, 0.5, -0.32), (0.82, 0.5, 0.58), (-0.78, 0.5, 0.78),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel(obj, 1.9, 6)


def add_parts():
    bronze = make_material("blackened_bronze_shell", (0.13, 0.075, 0.038), 0.25, 0.78)
    bone = make_material("smoked_bone_inlay", (0.61, 0.54, 0.41), 0.58)
    brass = make_material("burnished_amber_lock", (0.42, 0.19, 0.045), 0.24, 0.55)
    tissue = make_material("recessed_oxblood_membrane", (0.27, 0.008, 0.045), 0.24, 0.0, 0.012)
    void = make_material("unlit_internal_void", (0.006, 0.001, 0.003), 0.08)
    add_surface_texture(bronze, 3.8, 0.28, 0.16)
    add_surface_texture(bone, 5.6, 0.2, 0.11)
    add_surface_texture(brass, 7.2, 0.13, 0.08)
    add_surface_texture(tissue, 4.2, 0.16, 0.09)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    gimbal = bpy.context.object
    gimbal.name = "aperture_gimbal_animation_root"
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(4, -5, -2))
    membrane = bpy.context.object
    membrane.name = "aperture_membrane_animation_root"

    objects = [gimbal, membrane]
    objects.append(add_arc("broken_processional_shell_upper", (-5, 0, 0), 72, math.radians(18), math.radians(198), 8.4, bronze, y=3))
    objects.append(add_arc("broken_processional_shell_lower", (-5, 0, 0), 72, math.radians(214), math.radians(340), 8.4, bronze, y=3))
    objects.append(add_torus("tilted_outer_gimbal", 53, 4.8, (3, -1, -1), (math.radians(82), math.radians(13), math.radians(-9)), bone, gimbal))
    objects.append(add_torus("offset_inner_gimbal", 39, 3.5, (5, -5, -3), (math.radians(96), math.radians(-18), math.radians(7)), brass, gimbal))

    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, location=(8, 18, -4), scale=(22, 5, 18))
    cavity = bpy.context.object
    cavity.name = "deep_recessed_biological_cavity"
    cavity.data.materials.append(void)
    objects.append(smooth(cavity))

    objects.append(add_membrane_leaf("upper_recessed_membrane", (-8, 3, 10), (35, 2.5, 13), (0.11, -0.2, 0.18), tissue, membrane))
    objects.append(add_membrane_leaf("lower_recessed_membrane", (11, 7, -11), (31, 2.3, 12), (-0.14, 0.24, -0.34), tissue, membrane))
    objects.append(add_torus("tissue_aperture_lip", 20, 2.8, (8, 7, -4), (math.radians(90), 0, math.radians(8)), tissue, membrane))

    objects.append(add_box("upper_left_counterweight", (-51, -1, 55), (9, 7, 15), (0.18, -0.18, -0.52), bone, width=2.3))
    objects.append(add_box("lower_right_counterweight", (58, 0, -40), (13, 8, 10), (-0.2, 0.25, -0.34), bone, width=2.3))
    objects.append(add_box("diagonal_locking_bar", (-18, 3, 11), (45, 3.4, 3.8), (0.05, 0.2, -0.52), bronze, width=1.4))

    lever = add_handle(
        "long_processional_control_lever",
        [(-55, 1, 38), (-91, -1, 62), (-112, 2, 42), (-94, 3, 11)],
        6.5,
        bronze,
    )
    objects.append(lever)
    grip = add_handle(
        "lower_right_weighted_grip",
        [(49, 2, -37), (83, 3, -63), (110, 5, -39), (82, 3, -17)],
        7.2,
        bronze,
    )
    objects.append(grip)

    for index, location in enumerate(((-61, -6, -27), (34, -7, 58), (72, -4, 18))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=5.8, depth=10, location=location, rotation=(math.radians(90), 0, 0))
        stud = bpy.context.object
        stud.name = f"structural_lock_{index + 1}"
        stud.data.materials.append(brass)
        objects.append(bevel(stud, 0.8, 3))

    gimbal.rotation_euler = (0, 0, -0.08)
    gimbal.keyframe_insert(data_path="rotation_euler", frame=1)
    gimbal.rotation_euler = (0, math.radians(28), math.radians(18))
    gimbal.keyframe_insert(data_path="rotation_euler", frame=120)
    gimbal.rotation_euler = (0, 0, -0.08)
    gimbal.keyframe_insert(data_path="rotation_euler", frame=240)
    membrane.scale = (0.9, 0.9, 0.9)
    membrane.keyframe_insert(data_path="scale", frame=1)
    membrane.scale = (1.08, 1.0, 1.08)
    membrane.keyframe_insert(data_path="scale", frame=72)
    membrane.scale = (0.9, 0.9, 0.9)
    membrane.keyframe_insert(data_path="scale", frame=144)
    return objects


def convert_curves(objects):
    converted = []
    for obj in objects:
        if obj.type == "CURVE":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target="MESH")
            obj.select_set(False)
        converted.append(obj)
    return converted


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1350
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.65
    scene.world.color = (0.002, 0.001, 0.001)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(158, -405, 122))
    camera = bpy.context.object
    camera.data.lens = 57
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    track.target = target

    for location, energy, color, size in (
        ((-130, -150, 170), 7600, (1.0, 0.55, 0.29), 110),
        ((125, -60, -80), 5200, (0.48, 0.025, 0.065), 85),
        ((35, 50, 120), 3600, (0.74, 0.55, 0.35), 70),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.size = size


def add_backdrop():
    mat = make_material("charcoal_processional_backdrop", (0.0025, 0.0018, 0.0016), 0.96)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 85, 0), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.dimensions = (700, 520, 1)
    backdrop.data.materials.append(mat)


def export_assets(objects):
    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in objects if obj.type == "MESH")
    try:
        bpy.ops.wm.stl_export(filepath=str(STL_PATH), export_selected_objects=True, apply_modifiers=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=str(STL_PATH), use_selection=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_selection=True, export_animations=True, export_apply=True)


def render_outputs():
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(44)
    scene.render.filepath = str(RENDER_PATH)
    scene.render.film_transparent = True
    bpy.ops.render.render(write_still=True)
    add_backdrop()
    scene.render.filepath = str(PREVIEW_PATH)
    scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()
    objects = convert_curves(add_parts())
    setup_scene()
    export_assets(objects)
    render_outputs()
    print(f"Generated {GLB_PATH}")
    print(f"Generated {STL_PATH}")
    print(f"Generated {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
