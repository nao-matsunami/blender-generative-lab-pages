"""Build an asymmetric continuous VJ motion ribbon through Blender GUI watcher."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "shear-cascade"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def center(u):
    return Vector((
        51 * math.sin(2.65 * math.pi * u - .6) + 18 * u - 12,
        19 * math.sin(3.8 * math.pi * u + .4),
        178 * (u - .5),
    ))


def build():
    length, across = 180, 18
    verts, faces, zones = [], [], []
    for side in (1, -1):
        for i in range(length + 1):
            u = i / length
            point = center(u)
            tangent = (center(min(1, u + .0001)) - center(max(0, u - .0001))).normalized()
            angle = .3 + .48 * math.sin(2.5 * math.pi * u + .3)
            across_axis = Vector((math.sin(angle), math.cos(angle), .08 * math.sin(4 * math.pi * u)))
            across_axis = (across_axis - tangent * across_axis.dot(tangent)).normalized()
            normal = tangent.cross(across_axis).normalized()
            width = 23 + 7 * math.sin(2.7 * math.pi * u + .7)
            for j in range(across + 1):
                v = 2 * j / across - 1
                pleat = 3.5 * math.cos(3 * math.pi * v + .5 * math.sin(6 * math.pi * u))
                lip = 4.5 * abs(v) ** 8
                point_on_skin = point + across_axis * (width * v) + normal * (pleat + lip + side * 2.2)
                verts.append(tuple(point_on_skin))
    stride = across + 1
    layer = (length + 1) * stride
    for i in range(length):
        for j in range(across):
            a, b = i * stride + j, (i + 1) * stride + j
            faces.append((a, b, b + 1, a + 1))
            zones.append(1 if 48 <= i <= 94 else 0)
            faces.append((layer + a + 1, layer + b + 1, layer + b, layer + a))
            zones.append(2)
        for j in (0, across):
            a, b = i * stride + j, (i + 1) * stride + j
            faces.append((a, layer + a, layer + b, b) if j == 0 else
                         (b, layer + b, layer + a, a))
            zones.append(3)
    for i, flip in ((0, True), (length, False)):
        ring = [i * stride + j for j in range(stride)]
        ring += [layer + i * stride + j for j in reversed(range(stride))]
        faces.append(tuple(reversed(ring)) if flip else tuple(ring))
        zones.append(3)
    mesh = bpy.data.meshes.new("continuous_sheared_ribbon_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("one_piece_shear_cascade", mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (
        material("violet_black_satin", (.32, .20, .34), .18, .59),
        material("chalk_rose_broad_face", (.74, .51, .56), .08, .64),
        material("burnt_plum_reverse", (.47, .30, .39), .12, .66),
        material("ochre_integral_edge", (.55, .36, .25), .18, .57),
    ):
        mesh.materials.append(mat)
    for polygon, zone in zip(mesh.polygons, zones):
        polygon.material_index = zone
        polygon.use_smooth = True
    bevel = obj.modifiers.new("continuous_soft_edge", "BEVEL")
    bevel.width = .7
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    return obj


def setup_motion(obj):
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    root = bpy.context.object
    root.name = "shear_cascade_loop_motion"
    obj.parent = root
    for frame, z in ((1, 0), (91, 90), (181, 180), (271, 270), (361, 360)):
        root.rotation_euler = (0, 0, math.radians(z))
        root.keyframe_insert(data_path="rotation_euler", frame=frame)
    for curve in root.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 361
    scene.frame_set(1)
    return root


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.75
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.018, .011, .018, 1)
    bg.inputs["Strength"].default_value = .65
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(72, -380, 115))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 260
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis, track.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    for location, energy, color, size in (
        ((-120, -170, 180), 34000, (1, .83, .78), 110),
        ((160, -90, 70), 23000, (1, .63, .55), 90),
        ((0, 120, 150), 22000, (.88, .66, .77), 115),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.color, lamp.data.size = energy, color, size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = build()
    root = setup_motion(obj)
    setup_scene()
    for path in (STL, GLB, PNG, PREVIEW):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True,
                              export_animations=True, export_apply=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
