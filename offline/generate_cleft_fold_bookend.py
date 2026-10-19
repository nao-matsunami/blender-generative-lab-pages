"""Make a one-piece folded and perforated bookend in the running Blender GUI."""

import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "cleft-fold-bookend"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def profile_prism(name, outline, y_front, y_back):
    count = len(outline)
    verts = [(x, y_front, z) for x, z in outline]
    verts += [(x, y_back, z) for x, z in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count)
              for i in range(count)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def window_cutter(name, yz_outline):
    n = len(yz_outline)
    verts = [(-100, y, z) for y, z in yz_outline]
    verts += [(10, y, z) for y, z in yz_outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n)
              for i in range(n)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def build():
    # A broad flat foot turns up into a leaning back and a folded, sloped crest.
    # The edge profile is continuous, so the product exports as a single solid.
    body = profile_prism("single_piece_folding_bookend", [
        (-89, 0), (72, 0), (72, 9), (-61, 9),
        (-61, 119), (-37, 141), (-42, 150), (-72, 127),
        (-72, 19), (-89, 16),
    ], -52, 52)
    body.data.materials.append(material("chalk_rose_ceramic", (.74, .57, .51), .72))
    body.data.materials.append(material("dark_rose_cut_wall", (.36, .22, .25), .79))
    for name, yz in (
        ("large_offset_handle_window", [
            (-35, 59), (12, 55), (22, 61), (26, 85),
            (18, 96), (-33, 100), (-41, 91), (-42, 69),
        ]),
        ("short_lower_finger_window", [
            (14, 29), (38, 31), (41, 38), (37, 51),
            (11, 50), (7, 43),
        ]),
    ):
        cutter = window_cutter(name + "_tool", yz)
        mod = body.modifiers.new(name, "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cutter
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    # Cut walls are a deliberate material zone; the product has no small add-ons.
    for polygon in body.data.polygons:
        center = polygon.center
        polygon.material_index = 1 if (-78 < center.x < -55 and 25 < center.z < 106
                                       and abs(polygon.normal.x) < .6) else 0
    bevel = body.modifiers.new("soft_printable_edges", "BEVEL")
    bevel.width = 1.3
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    body.modifiers.new("weighted_normals", "WEIGHTED_NORMAL")
    return body


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1450
    scene.render.resolution_y = 1250
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.95
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.020, .013, .017, 1)
    bg.inputs["Strength"].default_value = .65
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-5, 0, 70))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(230, -245, 160))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 260
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for loc, energy, color, size in (
        ((-85, -150, 205), 25000, (1, .88, .79), 110),
        ((155, -65, 110), 18500, (1, .66, .55), 95),
        ((-20, 120, 170), 24000, (.88, .72, .72), 105),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.size = size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    body = build()
    scene_setup()
    for path in (STL, GLB, PNG):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
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
