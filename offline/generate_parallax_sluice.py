"""A folded, one-piece motion surface with deep parallax under rotation."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "parallax-sluice"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, metallic=0, roughness=.6):
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
        238 * (u - .5),
        42 * math.sin(2.1 * math.pi * u - .55) + 17 * (u - .5),
        40 * math.sin(1.75 * math.pi * u + .1) + 17 * math.sin(4.1 * math.pi * u - .6),
    ))


def build():
    along, across = 180, 28
    vertices, faces, zones = [], [], []
    for side in (1, -1):
        for i in range(along + 1):
            u = i / along
            p = center(u)
            tangent = (center(min(1, u + .001)) - center(max(0, u - .001))).normalized()
            angle = .72 + .88 * math.sin(2.8 * math.pi * u - .6)
            width_axis = Vector((0, math.cos(angle), math.sin(angle)))
            width_axis = (width_axis - tangent * width_axis.dot(tangent)).normalized()
            normal = tangent.cross(width_axis).normalized()
            width = 38 + 10 * math.sin(3.2 * math.pi * u + .1) + 14 * u
            width *= .52 + .48 * min(1, u * 14, (1 - u) * 10)
            for j in range(across + 1):
                v = 2 * j / across - 1
                # Wide, irregular load folds, cut into the surface rather than applied as trim.
                fold = (6.2 * math.sin(3.3 * math.pi * v + 3.8 * math.pi * u) +
                        3.4 * math.sin(6.2 * math.pi * u - 1.5 * v)) * (1 - .48 * v * v)
                lip = 4.8 * abs(v) ** 9
                q = p + width_axis * (width * v) + normal * (fold + lip + side * 2.7)
                vertices.append(tuple(q))
    stride = across + 1
    layer = (along + 1) * stride
    for i in range(along):
        for j in range(across):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append((a, b, b + 1, a + 1))
            zones.append(1 if (36 < i < 81 and j < 18) or (119 < i < 161 and j > 9) else 0)
            faces.append((layer + a + 1, layer + b + 1, layer + b, layer + a))
            zones.append(2)
        for j in (0, across):
            a = i * stride + j
            b = (i + 1) * stride + j
            faces.append((a, layer + a, layer + b, b) if j == 0 else
                         (b, layer + b, layer + a, a))
            zones.append(3)
    for i, flip in ((0, True), (along, False)):
        ring = [i * stride + j for j in range(stride)]
        ring += [layer + i * stride + j for j in reversed(range(stride))]
        faces.append(tuple(reversed(ring)) if flip else tuple(ring))
        zones.append(3)

    mesh = bpy.data.meshes.new("parallax_sluice_continuous_surface")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("one_piece_folded_sluice", mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (
        material("smoked_rose_face", (.53, .34, .42), .08, .68),
        material("bone_light_fold_zone", (.75, .62, .59), .05, .7),
        material("aubergine_reverse", (.22, .12, .25), .12, .62),
        material("dark_amber_section", (.42, .27, .18), .13, .65),
    ):
        mesh.materials.append(mat)
    for polygon, zone in zip(mesh.polygons, zones):
        polygon.material_index = zone
        polygon.use_smooth = True
    bevel = obj.modifiers.new("rounded_integral_edges", "BEVEL")
    bevel.width = .75
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    return obj


def motion(obj):
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    root = bpy.context.object
    root.name = "parallax_sluice_rotation"
    obj.parent = root
    for frame, angle in ((1, 0), (91, 90), (181, 180), (271, 270), (361, 360)):
        root.rotation_euler = (math.radians(8 * math.sin(math.radians(angle))),
                               math.radians(15 * math.sin(math.radians(angle))),
                               math.radians(angle))
        root.keyframe_insert(data_path="rotation_euler", frame=frame)
    for curve in root.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 361
    bpy.context.scene.frame_set(1)
    return root


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x, scene.render.resolution_y = 1450, 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 2.55
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.016, .010, .017, 1)
    bg.inputs["Strength"].default_value = .68
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 8))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(125, -310, 190))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 410
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis, track.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    for location, energy, color, size in (
        ((-120, -160, 170), 38000, (1, .82, .74), 110),
        ((160, -70, 85), 28000, (1, .66, .59), 100),
        ((0, 140, 100), 26000, (.89, .68, .78), 120),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.color, lamp.data.size = energy, color, size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = build()
    root = motion(obj)
    scene_setup()
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
