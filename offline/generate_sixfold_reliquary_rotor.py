"""Generate Sixfold Reliquary Rotor assets in Blender.

Mac mini workflow:
npm run job:reliquary
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "sixfold-reliquary-rotor"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def material(name, color, roughness, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def bevel_and_smooth(obj, width=1.2, segments=4):
    bevel = obj.modifiers.new("ritual_softened_edges", "BEVEL")
    bevel.width = width
    bevel.segments = segments
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def add_wedge(name, angle, inner_radius, outer_radius, inner_half, outer_half, depth, mat, parent):
    y0 = -depth * 0.5
    y1 = depth * 0.5
    vertices = [
        (inner_radius, y0, -inner_half),
        (outer_radius, y0, -outer_half),
        (outer_radius, y0, outer_half),
        (inner_radius, y0, inner_half),
        (inner_radius, y1, -inner_half),
        (outer_radius, y1, -outer_half),
        (outer_radius, y1, outer_half),
        (inner_radius, y1, inner_half),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler[1] = angle
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel_and_smooth(obj, 1.8, 5)


def add_torus(name, major, minor, y, mat, parent=None, rotation=0.0):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=128,
        minor_segments=24,
        major_radius=major,
        minor_radius=minor,
        location=(0, y, 0),
        rotation=(math.radians(90), 0, rotation),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def add_cylinder(name, radius, depth, y, mat, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=96,
        radius=radius,
        depth=depth,
        location=(0, y, 0),
        rotation=(math.radians(90), 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel_and_smooth(obj, 0.9, 4)


def add_handle(name, side, mat):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 24
    curve.bevel_depth = 5.6
    curve.bevel_resolution = 8
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(3)
    x0 = side * 68
    x1 = side * 98
    points = [(x0, 1, 32), (x1, 3, 38), (x1, 3, -38), (x0, 1, -32)]
    for point, coords in zip(spline.bezier_points, points):
        point.co = coords
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_stud(name, angle, mat, parent):
    radius = 69
    x = math.cos(angle) * radius
    z = math.sin(angle) * radius
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=5.2,
        depth=12,
        location=(x, -1, z),
        rotation=(math.radians(90), 0, 0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel_and_smooth(obj, 0.7, 3)


def add_parts():
    bone = material("calcified_ivory_valve_housing", (0.62, 0.55, 0.43), 0.56)
    soot = material("soot_black_rotor_frame", (0.018, 0.012, 0.014), 0.68)
    amber = material("dark_amber_fasteners", (0.34, 0.16, 0.045), 0.42, 0.015)
    bruised = material("bruised_inner_valve_tissue", (0.24, 0.018, 0.07), 0.22, 0.035)
    wet = material("wet_reliquary_cavity", (0.055, 0.004, 0.018), 0.12, 0.025)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    outer_rotor = bpy.context.object
    outer_rotor.name = "reliquary_outer_rotor_animation_root"
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -8, 0))
    inner_rotor = bpy.context.object
    inner_rotor.name = "reliquary_inner_valve_animation_root"

    objects = [outer_rotor, inner_rotor]
    objects.append(add_torus("reliquary_outer_counterweight_ring", 61, 7.5, 3, soot, outer_rotor))
    objects.append(add_torus("reliquary_inner_bone_race", 43, 5.0, -1, bone, outer_rotor, math.radians(7)))
    # Keep the wet core recessed so the central void reads before the tissue.
    objects.append(add_cylinder("reliquary_deep_inner_cavity", 17, 5, 6, wet, inner_rotor))

    for index in range(6):
        angle = index * math.tau / 6
        objects.append(add_wedge(f"reliquary_outer_valve_arm_{index + 1}", angle, 48, 77, 9, 16, 10, bone, outer_rotor))
        objects.append(add_wedge(f"reliquary_inner_membrane_valve_{index + 1}", angle + 0.16, 8, 34, 4.5, 12, 4.5, bruised, inner_rotor))
        objects.append(add_stud(f"reliquary_amber_lock_stud_{index + 1}", angle + math.pi / 6, amber, outer_rotor))

    objects.append(add_handle("reliquary_left_weighted_handle", -1, soot))
    objects.append(add_handle("reliquary_right_weighted_handle", 1, soot))

    outer_rotor.rotation_euler[1] = 0
    outer_rotor.keyframe_insert(data_path="rotation_euler", frame=1)
    outer_rotor.rotation_euler[1] = math.tau
    outer_rotor.keyframe_insert(data_path="rotation_euler", frame=240)
    inner_rotor.rotation_euler[1] = 0
    inner_rotor.keyframe_insert(data_path="rotation_euler", frame=1)
    inner_rotor.rotation_euler[1] = -math.tau
    inner_rotor.keyframe_insert(data_path="rotation_euler", frame=180)
    for obj in (outer_rotor, inner_rotor):
        if obj.animation_data and obj.animation_data.action:
            for curve in obj.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"

    return objects


def convert_curves(objects):
    converted = []
    for obj in objects:
        if obj.type != "CURVE":
            converted.append(obj)
            continue
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
    scene.view_settings.exposure = 0.9
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0.002, 0.001, 0.002)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(6, -340, 18))
    camera = bpy.context.object
    camera.data.lens = 55
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    track.target = target

    bpy.ops.object.light_add(type="AREA", location=(-110, -125, 145))
    key = bpy.context.object
    key.data.energy = 5400
    key.data.color = (1.0, 0.64, 0.38)
    key.data.size = 125
    bpy.ops.object.light_add(type="AREA", location=(120, -55, -70))
    rim = bpy.context.object
    rim.data.energy = 3100
    rim.data.color = (0.58, 0.08, 0.18)
    rim.data.size = 95
    bpy.ops.object.light_add(type="POINT", location=(0, -80, 0))
    inner = bpy.context.object
    inner.data.energy = 750
    inner.data.color = (0.66, 0.08, 0.14)
    inner.data.shadow_soft_size = 40


def add_backdrop():
    mat = material("reliquary_coal_backdrop", (0.003, 0.002, 0.003), 0.98)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 90, 0), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "reliquary_preview_coal_backdrop"
    backdrop.dimensions = (620, 460, 1)
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
    scene.frame_set(36)
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
    print(f"Generated {STL_PATH}")
    print(f"Generated {GLB_PATH}")
    print(f"Generated {RENDER_PATH}")
    print(f"Generated {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
