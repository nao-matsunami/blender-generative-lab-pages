"""Sculpt a single pleated membrane arch in the running Blender GUI."""

import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "dusk-loom-aperture"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, roughness, transmission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def membrane():
    cols, rows = 180, 32
    verts, faces = [], []
    for j in range(rows + 1):
        v = j / rows
        for i in range(cols + 1):
            u = i / cols
            t = math.pi * u
            arch = max(0, math.sin(t)) ** .85
            top = 34 + 112 * arch + 16 * (u - .5) + 17*math.sin(t)*math.cos(t)
            drop = 26 + 16 * u + 25 * math.sin(t) ** 2 + 8 * math.sin(3*t) * math.sin(t)
            x = -102 + 204*u + (8 + 13*arch)*v*math.sin(t+.3)
            z = top - drop*v - 2.5*math.sin(5*t)*math.sin(math.pi*v)
            pleat = math.sin(11*t + .7*v)
            y = -6 + 19*math.sin(t)*math.sin(2.4*t) + (2.5+14*v)*pleat
            verts.append((x, y, z))
    stride = cols+1
    for j in range(rows):
        for i in range(cols):
            a = j*stride+i
            faces.append((a,a+1,a+stride+1,a+stride))
    mesh = bpy.data.meshes.new("continuous_loom_skin_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("continuous_pleated_loom_skin", mesh)
    bpy.context.collection.objects.link(obj)
    mats = [
        material("clouded_rose_weft", (.75,.46,.49), .68, .07),
        material("plum_shadow_selvedge", (.34,.2,.29), .78),
        material("warm_bone_loaded_crest", (.8,.64,.57), .7),
    ]
    for mat in mats:
        mesh.materials.append(mat)
    for poly in mesh.polygons:
        row = poly.index // cols
        col = poly.index % cols
        if row >= rows-4 or col < 4 or col >= cols-4:
            poly.material_index = 1
        elif row < 3:
            poly.material_index = 2
        poly.use_smooth = True
    solid = obj.modifiers.new("single_thickened_skin", "SOLIDIFY")
    solid.thickness = 2.6
    solid.offset = 0
    bevel = obj.modifiers.new("soft_integral_edges", "BEVEL")
    bevel.width = .55
    bevel.segments = 2
    return obj


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x = 1350
    scene.render.resolution_y = 1150
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.25
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.016,.011,.017,1)
    bg.inputs["Strength"].default_value = .75
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(5,0,70))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(205,-270,175))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 262
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    for location, power, color, size in (
        ((-105,-130,185), 29000, (1,.81,.76), 110),
        ((110,45,160), 25000, (1,.67,.72), 115),
        ((10,-100,0), 10000, (1,.76,.62), 90),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy = power
        lamp.data.color = color
        lamp.data.size = size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = membrane()
    scene_setup()
    for path in (STL, GLB, PNG, PREVIEW):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True)
    bpy.ops.object.duplicate()
    print_body = bpy.context.object
    print_body.name = "sealed_print_skin"
    for modifier in list(print_body.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    seal = print_body.modifiers.new("seal_fold_contacts_for_stl", "REMESH")
    seal.mode = "VOXEL"
    seal.voxel_size = .65
    bpy.ops.object.modifier_apply(modifier=seal.name)
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    bpy.data.objects.remove(print_body, do_unlink=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
