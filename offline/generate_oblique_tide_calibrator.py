"""Build an asymmetric cut-through ritual instrument in the Blender GUI watcher."""

import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "oblique-tide-calibrator"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, roughness=.6, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def prism(name, outline, front, back, mat=None, bevel=0):
    n = len(outline)
    verts = [(x, front, z) for x, z in outline] + [(x, back, z) for x, z in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("machined_edge_round", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("corner_normals", "WEIGHTED_NORMAL")
    return obj


def cut(obj, name, outline):
    tool = prism(name + "_tool", outline, -45, 45)
    mod = obj.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = tool
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool, do_unlink=True)


def open_arch(outside, inside, front, back, mat):
    """Build actual front/back annular faces and the exposed aperture wall."""
    n = len(outside)
    assert n == len(inside)
    verts = ([(x, front, z) for x, z in outside] +
             [(x, front, z) for x, z in inside] +
             [(x, back, z) for x, z in outside] +
             [(x, back, z) for x, z in inside])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.extend([
            (i, j, n+j, n+i),
            (2*n+j, 2*n+i, 3*n+i, 3*n+j),
            (j, i, 2*n+i, 2*n+j),
            (n+i, n+j, 3*n+j, 3*n+i),
        ])
    mesh = bpy.data.meshes.new("cast_open_arch_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("one_piece_inclined_calibration_arch", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj


def build():
    bronze = material("blackened_rose_bronze", (.40, .25, .27), .50, .48)
    edge = material("warm_copper_load_face", (.63, .37, .27), .42, .58)
    ivory = material("bone_ceramic_pointer", (.77, .67, .52), .64, .08)
    back = material("violet_black_counterweight", (.20, .13, .19), .65, .22)

    # A weighted, slanted arch. The aperture is a genuine cut-through opening.
    chassis = open_arch([
        (-101,-69),(-87,-80),(26,-80),(95,-60),(96,-42),
        (64,-31),(46,18),(14,73),(-20,94),(-56,79),(-82,38),(-95,-12),
    ], [
        (-59,-43),(-35,-43),(20,-43),(36,-43),(36,-28),(35,-12),
        (28,13),(2,55),(-21,64),(-39,47),(-52,31),(-57,-3),
    ], -16, 16, bronze)
    mod = chassis.modifiers.new("cast_edge_fillet", "BEVEL")
    mod.width = 2.7
    mod.segments = 3
    chassis.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    pieces = [chassis]

    # Pointer is seated deeply into the upper arch and stops inside the aperture.
    pieces.append(prism("integral_broad_oscillator_tongue", [
        (-23,83),(-5,70),(2,43),(-9,-14),(-19,-22),(-27,-13),(-25,40),
    ], -20, 5, ivory, 1.8))
    # Load strip is recessed into the left pier; it changes the edge rhythm.
    pieces.append(prism("forged_left_load_strip", [
        (-96,-65),(-86,-70),(-72,-35),(-69,25),(-48,66),(-58,75),
        (-82,38),(-95,-12),
    ], -18.3, -15, edge, 1.0))
    pieces.append(prism("offset_counterweight_heel", [
        (23,-80),(95,-60),(94,-44),(65,-47),(43,-62),
    ], 9, 31, back, 1.6))
    pieces.append(prism("lower_copper_contact_land", [
        (35,-55),(68,-48),(87,-42),(95,-42),(94,-58),(33,-75),
    ], -18.2, -15, edge, 1.0))
    return pieces


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1450
    scene.render.resolution_y = 1180
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.9
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.016, .010, .015, 1)
    bg.inputs["Strength"].default_value = .55
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-3, 0, 4))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(220, -285, 190))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 255
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for loc, power, color, size in (
        ((-130,-150,180),23000,(1,.88,.72),110),
        ((125,-90,85),22000,(1,.69,.55),100),
        ((30,110,145),26000,(.91,.70,.70),115),
        ((-100,40,15),10000,(1,.77,.59),95),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy = power
        light.data.color = color
        light.data.size = size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    pieces = build()
    scene_setup()
    for path in (STL, GLB, PNG):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
