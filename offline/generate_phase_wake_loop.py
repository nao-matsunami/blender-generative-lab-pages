"""Build a continuous, asymmetrical VJ motion ribbon in the Blender GUI."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "phase-wake-loop"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, metallic=0, roughness=.5):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def center(t):
    return Vector((
        83 * math.cos(t) + 16 * math.cos(2 * t + .55),
        48 * math.sin(t) + 12 * math.sin(3 * t - .35),
        33 * math.sin(t + .48) + 22 * math.sin(2 * t - .75),
    ))


def make_ribbon():
    count, across = 192, 24
    verts, faces, zones = [], [], []
    for side in (1, -1):
        for i in range(count):
            t = 2 * math.pi * i / count
            p = center(t)
            tangent = (center(t + .001) - center(t - .001)).normalized()
            radial = Vector((math.cos(t), math.sin(t), 0))
            upright = Vector((0, 0, 1))
            twist = t + .38 * math.sin(2 * t + .3) + .35
            width_axis = radial * math.cos(twist) + upright * math.sin(twist)
            width_axis = (width_axis - tangent * width_axis.dot(tangent)).normalized()
            normal = tangent.cross(width_axis).normalized()
            half_width = 11 + 9 * (1 + math.sin(t - .7)) / 2 + 8 * math.sin(2 * t + .9) ** 2
            for j in range(across + 1):
                v = 2 * j / across - 1
                # Integrated curled lips and broad pulse folds: one solid surface.
                lip = 4.5 * abs(v) ** 9
                pulse = 2.8 * math.sin(7 * t + 1.1) * (1 - v * v) ** 2
                thickness = side * 2.7
                q = p + width_axis * (half_width * v) + normal * (lip + pulse + thickness)
                verts.append(tuple(q))
    stride = across + 1
    layer_size = count * stride
    for i in range(count):
        nxt = (i + 1) % count
        for j in range(across):
            a = i * stride + j
            b = nxt * stride + j
            faces.append((a, b, b + 1, a + 1))
            zones.append(1 if .10 < i / count < .32 else 0)
            faces.append((layer_size + a + 1, layer_size + b + 1, layer_size + b, layer_size + a))
            zones.append(2)
        for j in (0, across):
            a = i * stride + j
            b = nxt * stride + j
            if j == 0:
                faces.append((a, layer_size + a, layer_size + b, b))
            else:
                faces.append((b, layer_size + b, layer_size + a, a))
            zones.append(3)
    mesh = bpy.data.meshes.new("continuous_phase_wake_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("one_piece_twisted_wake", mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (
        material("aubergine_satin", (.25, .13, .28), .17, .56),
        material("smoked_rose_phase", (.54, .29, .35), .08, .62),
        material("plum_copper_reverse", (.32, .16, .29), .13, .57),
        material("dark_amber_integral_edge", (.38, .19, .10), .31, .48),
    ):
        obj.data.materials.append(mat)
    for face, zone in zip(mesh.polygons, zones):
        face.material_index = zone
        face.use_smooth = True
    bevel = obj.modifiers.new("soft_band_edges", "BEVEL")
    bevel.width = .9
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    return obj


def setup_motion(obj):
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    root = bpy.context.object
    root.name = "phase_wake_loop_motion"
    obj.parent = root
    for frame, angles in ((1, (-10, -18, -13)), (90, (19, 66, 37)),
                          (180, (-10, 162, 97)), (270, (21, 263, 173)),
                          (361, (-10, 342, 347))):
        root.rotation_euler = tuple(math.radians(v) for v in angles)
        root.keyframe_insert(data_path="rotation_euler", frame=frame)
    for curve in root.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "LINEAR"
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 361
    bpy.context.scene.frame_set(1)
    return root


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x = 1450
    scene.render.resolution_y = 1120
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.7
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.012, .007, .013, 1)
    bg.inputs["Strength"].default_value = .7
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-2, 0, 3))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(170, -260, 165))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 275
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for location, energy, color, size in (
        ((-115, -135, 145), 28000, (1, .80, .71), 110),
        ((125, -35, 10), 17000, (1, .49, .40), 90),
        ((0, 130, 110), 23000, (.79, .59, .71), 125),
        ((-90, 45, -75), 9000, (1, .67, .41), 90),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy = energy
        lamp.data.color = color
        lamp.data.size = size


def export(obj, root):
    STL.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True,
                              export_animations=True, export_apply=True)


def render():
    PNG.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = make_ribbon()
    root = setup_motion(obj)
    scene_setup()
    export(obj, root)
    render()


if __name__ == "__main__":
    main()
