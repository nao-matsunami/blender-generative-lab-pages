"""An asymmetric, open marine shell made in the running Blender GUI."""

import math
import os
from pathlib import Path

import bmesh
import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "littoral-keel-shell"
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


def make_shell():
    n = 192
    outer_steps = 18
    inner_steps = 16
    verts = []
    faces = []
    face_materials = []

    def rim_height(theta):
        # The raised prow and uneven side lips keep the long silhouette legible.
        return 47 + 23 * max(0, math.cos(theta)) ** 4 - 8 * max(0, -math.cos(theta)) ** 4 + 18 * math.sin(theta) + 6 * math.sin(3 * theta + .4)

    def point(theta, radius, z, flute):
        wave = 1 + flute * (.056 * math.sin(19 * theta + .55 * z / 50) + .018 * math.sin(37 * theta - .2))
        radius *= wave
        x = 109 * radius * math.cos(theta)
        y = 52 * radius * math.sin(theta) + .11 * x
        return (x, y, z)

    # Outer shell climbs from a broad, stable keel to a sculpted open rim.
    for j in range(outer_steps + 1):
        t = j / outer_steps
        radius = .22 + .78 * (t ** .85)
        for i in range(n):
            theta = 2 * math.pi * i / n
            z = 2 + (rim_height(theta) - 2) * (t ** 2.5)
            z += 1.4 * math.sin(13 * math.pi * t) * math.sin(math.pi * t) ** 2
            verts.append(point(theta, radius, z, math.sin(math.pi * t) ** .7))

    # The same mesh returns inward to a visible, empty basin.
    for j in range(1, inner_steps + 1):
        t = j / inner_steps
        radius = 1 - .83 * (t ** .82)
        for i in range(n):
            theta = 2 * math.pi * i / n
            z = rim_height(theta) * (1 - t ** .7) + 7 * t ** .7
            verts.append(point(theta, radius, z, .24 * math.sin(math.pi * t)))

    ring_count = outer_steps + inner_steps + 1
    for j in range(ring_count - 1):
        for i in range(n):
            ni = (i + 1) % n
            faces.append((j*n+i, j*n+ni, (j+1)*n+ni, (j+1)*n+i))
            if j < outer_steps:
                face_materials.append(0 if j < 5 else (1 if j < outer_steps-3 else 2))
            else:
                face_materials.append(3 if j < outer_steps + 8 else (4 if j < outer_steps + 13 else 5))
    faces.append(tuple(reversed(tuple(range(n)))))
    face_materials.append(0)
    faces.append(tuple((ring_count-1)*n+i for i in range(n)))
    face_materials.append(5)

    mesh = bpy.data.meshes.new("continuous_littoral_shell_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("continuous_open_keel_shell", mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (
        material("plum_underside", (.22,.12,.18), .78),
        material("burnished_rose_ochre_shell", (.63,.39,.32), .69),
        material("bone_rose_lip", (.82,.65,.56), .59),
        material("pearl_ochre_interior", (.71,.56,.45), .74),
        material("ochre_interior_shelf", (.57,.41,.36), .8),
        material("deep_plum_interior", (.31,.19,.22), .82),
    ):
        mesh.materials.append(mat)
    for poly, idx in zip(mesh.polygons, face_materials):
        poly.material_index = idx
        poly.use_smooth = poly.loop_total == 4

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    bevel = obj.modifiers.new("integral_soft_lip", "BEVEL")
    bevel.width = .48
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = .55
    return obj


def scene_setup():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.85
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.022,.014,.019,1)
    bg.inputs["Strength"].default_value = .8
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0,0,29))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(150,-245,113))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 251
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for location, power, color, size in (
        ((-105,-110,175), 24500, (1,.82,.72), 115),
        ((100,70,170), 30500, (1,.68,.62), 110),
        ((40,-80,45), 12500, (1,.79,.63), 100),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy = power
        lamp.data.color = color
        lamp.data.size = size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = make_shell()
    scene_setup()
    for path in (STL, GLB, PNG, PREVIEW):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True)
    bpy.ops.object.duplicate()
    print_body = bpy.context.object
    print_body.name = "sealed_print_shell"
    for modifier in list(print_body.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    seal = print_body.modifiers.new("seal_shell_for_stl", "REMESH")
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
