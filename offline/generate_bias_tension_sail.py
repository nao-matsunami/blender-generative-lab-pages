"""Build an asymmetric tensioned membrane in the running Blender GUI."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "bias-tension-sail"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def surface(u, v):
    """A sheared four-corner sheet with tension, billow, and bias folds."""
    top = Vector((-92 + 157*u, -22 + 31*u, 16 + 77*u))
    bottom = Vector((-31 + 130*u, 0 + 17*u, -80 + 42*u))
    p = top.lerp(bottom, v)
    p.x += (-12 + 27*u) * math.sin(math.pi*v)
    p.z += (13-31*v) * math.sin(math.pi*u)
    # Broad load-bearing creases grow from the corners rather than tiling the sheet.
    fold = (20 * math.sin(math.pi*(4*u + .6*v)) + 4 * math.sin(math.pi*(8*u - .9*v)))
    p.y += fold * math.sin(math.pi*v) + 18 * math.sin(math.pi*u) * math.sin(math.pi*v)
    return p


def make_sheet(name, u0, u1, v0, v1, cols, rows, mat, thickness, offset=0):
    verts = []
    faces = []
    for j in range(rows+1):
        v = v0 + (v1-v0)*j/rows
        for i in range(cols+1):
            u = u0 + (u1-u0)*i/cols
            p = surface(u, v)
            p.y += offset
            verts.append(tuple(p))
    stride = cols+1
    for j in range(rows):
        for i in range(cols):
            u = u0 + (u1-u0)*(i+.5)/cols
            v = v0 + (v1-v0)*(j+.5)/rows
            a = j*stride+i
            faces.append((a,a+1,a+stride+1,a+stride))
    mesh = bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    solid = obj.modifiers.new("continuous_fabric_thickness", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0
    bevel = obj.modifiers.new("soft_cut_edges", "BEVEL")
    bevel.width = min(.45, thickness*.32)
    bevel.segments = 2
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def make_reinforcement(name, edge, start, stop, width, mat):
    """Integrated broad hems, sampled directly from the membrane surface."""
    if edge == "top":
        coords = (start, stop, 0, width)
    elif edge == "bottom":
        coords = (start, stop, 1-width, 1)
    elif edge == "left":
        coords = (0, width, start, stop)
    else:
        coords = (1-width, 1, start, stop)
    return make_sheet(name, *coords, 80, 7, mat, 2.7, offset=-.5)


def make_bias_seam(mat):
    verts = []
    faces = []
    rows = 120
    for j in range(rows+1):
        v = j/rows
        center = .36 + .24*v
        for i in range(5):
            u = center + (i-2)*.008
            p = surface(u, v)
            p.y -= .45
            verts.append(tuple(p))
    for j in range(rows):
        for i in range(4):
            a = j*5+i
            faces.append((a,a+1,a+6,a+5))
    mesh = bpy.data.meshes.new("bias_seam_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("continuous_bias_seam", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    solid = obj.modifiers.new("stitched_seam_relief", "SOLIDIFY")
    solid.thickness = 2.1
    solid.offset = 0
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def setup_scene():
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
    scene.view_settings.exposure = 2.15
    scene.world.color = (.025,.015,.020)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0,0,3))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(185,-235,160))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 257
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    for loc, power, color, size in (
        ((-115,-105,175), 25000, (1,.83,.69), 105),
        ((105,-20,100), 14000, (1,.58,.47), 95),
        ((12,110,80), 20500, (.86,.6,.7), 100),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lamp = bpy.context.object
        lamp.data.energy = power
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
    backdrop = material("warm_black_backdrop", (.012,.007,.011), .95)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0,95,0), rotation=(math.pi/2,0,0))
    plane = bpy.context.object
    plane.dimensions = (650,650,1)
    plane.data.materials.append(backdrop)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    skin = material("clouded_rose_tension_skin", (.61,.29,.32), .68)
    hem = material("bone_rose_reinforced_selvedge", (.77,.53,.43), .7)
    shadow = material("violet_black_underfold", (.19,.085,.13), .73)
    objects = [make_sheet("load_bearing_sail", 0, 1, 0, 1, 320, 220, skin, 1.7)]
    objects += [
        make_reinforcement("upper_tension_hem", "top", 0, 1, .053, hem),
        make_reinforcement("lower_weighted_hem", "bottom", 0, 1, .072, shadow),
        make_reinforcement("left_anchored_edge", "left", 0, 1, .038, hem),
        make_reinforcement("right_anchored_edge", "right", 0, 1, .045, shadow),
        make_bias_seam(shadow),
    ]
    setup_scene()
    export(objects)
    render()


if __name__ == "__main__":
    main()
