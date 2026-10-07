"""Generate Umbra Slip Shutter in the running Blender GUI watcher."""

import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "umbra-slip-shutter"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, metal=0, rough=.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def ribbon():
    # One closed, continuously folded casting. The rolled edges are geometry,
    # rather than decorative surface tubing.
    nx, nv = 112, 24
    verts, faces, zones = [], [], []
    stride = nv + 1
    for side in (-1, 1):
        for i in range(nx + 1):
            t = i / nx
            x = -94 + 188 * t
            center_z = 25 * math.sin(2 * math.pi * (t - .10)) + 12 * (t - .5)
            half_width = 12 + 25 * math.sin(math.pi * t) ** .74
            for j in range(nv + 1):
                v = 2 * j / nv - 1
                z = center_z + half_width * v
                rolled = 4.2 * abs(v) ** 9
                fold = 9 * math.sin(3 * math.pi * t + .4) * (1 - v * v)
                y = 7 * math.sin(2 * math.pi * t) + 5 * v * v + fold + rolled
                verts.append((x, y + side * 2.2, z))
    layer = (nx + 1) * stride
    for i in range(nx):
        for j in range(nv):
            a = i * stride + j
            faces.append((a, a + stride, a + stride + 1, a + 1))
            zones.append(0 if i < 24 or i > 85 else 1)
            b = layer + a
            faces.append((b + 1, b + stride + 1, b + stride, b))
            zones.append(0)
    for i in range(nx):
        for j in (0, nv):
            a = i * stride + j
            b = layer + a
            if j == 0:
                faces.append((a, b, b + stride, a + stride))
            else:
                faces.append((a + stride, b + stride, b, a))
            zones.append(2)
    for i in (0, nx):
        for j in range(nv):
            a = i * stride + j
            b = layer + a
            if i == 0:
                faces.append((a + 1, b + 1, b, a))
            else:
                faces.append((a, b, b + 1, a + 1))
            zones.append(2)
    mesh = bpy.data.meshes.new("continuous_folded_shutter_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("one_piece_slip_shutter", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("bruised_graphite_cast", (.15, .055, .095), .35, .43))
    obj.data.materials.append(material("plum_satin_face", (.34, .105, .19), .18, .54))
    obj.data.materials.append(material("dark_amber_cut_edge", (.43, .22, .075), .38, .42))
    for poly, zone in zip(mesh.polygons, zones):
        poly.material_index = zone
    return obj


def cut_slot(obj, name, x, z, rx, rz, tilt):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(x, 0, z))
    cutter = bpy.context.object
    cutter.name = name
    cutter.scale = (rx, 80, rz)
    cutter.rotation_euler[1] = math.radians(tilt)
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    modifier = obj.modifiers.new(name, "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def make_object():
    obj = ribbon()
    # Large negative spaces interrupt the sheet but leave load-bearing bridges.
    for args in (
        ("long_left_aperture", -43, 11, 17, 7.5, -13),
        ("central_breath_aperture", 0, -8, 23, 9, 9),
        ("right_key_aperture", 51, -14, 16, 7, -18),
    ):
        cut_slot(obj, *args)
    bevel = obj.modifiers.new("soft_cast_cut_edges", "BEVEL")
    bevel.width = .8
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    for poly in obj.data.polygons:
        poly.use_smooth = True
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    root = bpy.context.object
    root.name = "looping_shutter_motion"
    obj.parent = root
    for frame, rotation in ((1, (-5, -12, -5)), (120, (5, 13, 8)), (240, (-5, -12, -5))):
        root.rotation_euler = tuple(math.radians(v) for v in rotation)
        root.keyframe_insert(data_path="rotation_euler", frame=frame)
    return obj, root


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.frame_start, scene.frame_end = 1, 240
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.1
    scene.world.color = (.002, .001, .002)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(76, -265, 120))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 237
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for location, energy, color, size in (
        ((-55, -145, 155), 16000, (1, .82, .65), 125),
        ((115, -70, -45), 9500, (.83, .29, .33), 95),
        ((15, 85, 85), 7000, (.82, .5, .28), 115),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.size = size


def export(obj, root):
    STL.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=str(STL), use_selection=True)
    root.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_animations=True, export_apply=True)


def render():
    PNG.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(52)
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    backdrop = material("charcoal_stage", (.003, .002, .003), 0, .9)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 85, 0), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.object
    plane.dimensions = (650, 500, 1)
    plane.data.materials.append(backdrop)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj, root = make_object()
    scene_setup()
    export(obj, root)
    render()


if __name__ == "__main__":
    main()
