"""Construct an asymmetric open-jaw measuring instrument in the active Blender GUI."""

import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "cantilever-aperture-gauge"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, roughness=.62, metallic=.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def extruded_profile(name, outline, y_front, y_back, mat, bevel=0):
    count = len(outline)
    verts = [(x, y_front, z) for x, z in outline] + [(x, y_back, z) for x, z in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("machined_edge_radii", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.affect = "EDGES"
        mod.loop_slide = True
        obj.modifiers.new("weighted_corner_normals", "WEIGHTED_NORMAL")
    return obj


def cut_slot(obj, name, location, scale, rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cutter = bpy.context.object
    cutter.name = name + "_cutter"
    cutter.dimensions = scale
    cutter.rotation_euler[1] = rotation
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mod = obj.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def build_object():
    forged = material("oxidized_black_bronze", (.29, .19, .18), .50, .60)
    copper = material("abraded_rose_copper", (.53, .28, .22), .43, .52)
    bone = material("ceramic_contact_faces", (.76, .64, .49), .58, .10)
    dark = material("plum_depth_grip", (.17, .10, .14), .7, .22)

    # The upper arm overhangs the lower jaw, leaving the central aperture open.
    outline = [
        (-83, -68), (-62, -82), (7, -80), (30, -66), (32, -49),
        (20, -42), (-31, -42), (-43, -29), (-42, 24), (-30, 42),
        (37, 42), (65, 50), (76, 65), (67, 77), (42, 83),
        (-49, 82), (-72, 62), (-84, 32), (-76, -31),
    ]
    chassis = extruded_profile("one_piece_open_C_chassis", outline, -13, 13, forged)
    cut_slot(chassis, "upper_arm_long_open_slot", (-1, 0, 63), (52, 40, 7))
    cut_slot(chassis, "spine_lightening_window", (-63, 0, -3), (9, 40, 34), -.06)
    bevel = chassis.modifiers.new("forged_round_edges", "BEVEL")
    bevel.width = 2.6
    bevel.segments = 3
    chassis.modifiers.new("weighted_corner_normals", "WEIGHTED_NORMAL")

    objects = [chassis]
    # Copper load strap follows the left spine, embedded into the forging.
    objects.append(extruded_profile("inset_load_strap", [
        (-82, -65), (-70, -76), (-55, -72), (-61, -43),
        (-63, 28), (-56, 64), (-66, 72), (-75, 59), (-82, 32),
    ], -15.2, -12.6, copper, 1.1))
    # Dissimilar jaw blocks meet the chassis with substantial overlap.
    objects.append(extruded_profile("upper_angled_contact", [
        (44, 55), (66, 60), (69, 38), (56, 28), (43, 32),
    ], -17, 16, bone, 1.5))
    objects.append(extruded_profile("lower_rising_contact", [
        (9, -77), (30, -64), (30, -47), (15, -43), (7, -53),
    ], -16, 15, copper, 1.5))
    # A rear counterweight makes the frame legible as a deep object in oblique view.
    objects.append(extruded_profile("rear_counterweight", [
        (-87, -60), (-74, -83), (-47, -86), (-50, -65), (-70, -47),
    ], 9, 28, dark, 1.6))
    return objects


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1150
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.9
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.015, .009, .013, 1)
    bg.inputs["Strength"].default_value = .45
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-3, 0, 0))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(235, -270, 180))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 255
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for location, energy, color, size in (
        ((-130, -145, 185), 21000, (1, .83, .69), 100),
        ((100, -85, 75), 21000, (1, .65, .52), 82),
        ((15, 105, 120), 28000, (.75, .67, .71), 105),
        ((-110, 30, -15), 9000, (1, .74, .55), 90),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy = energy
        lamp.data.color = color
        lamp.data.size = size


def export(objects):
    STL.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True)


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
    objects = build_object()
    setup_scene()
    export(objects)
    render()


if __name__ == "__main__":
    main()
