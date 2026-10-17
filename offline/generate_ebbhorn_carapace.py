"""Build an asymmetric marine horn shell in the active Blender GUI watcher."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "ebbhorn-carapace"
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


def center(t):
    return Vector((-103 + 186*t, 38*math.sin(1.55*math.pi*t)*(1-.42*t),
                   -16 + 51*t + 30*math.sin(math.pi*t)))


def frame(t):
    tangent = (center(min(1, t+.001)) - center(max(0, t-.001))).normalized()
    side = tangent.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(tangent).normalized()
    return side, up


def outer_radius(t, a):
    base = 2.5 + 43*t**1.48
    # Long, carved shell flutes and one lifted dorsal crest define the surface.
    flutes = (1.2 + 3.2*t)*math.cos(11*a + 1.5*t)
    shoulder = 6.2*math.exp(-((t-.80)/.19)**2) * math.exp(-(math.atan2(math.sin(a-1.9),math.cos(a-1.9))/.46)**2)
    lip = 5.5*t**12*(.5 + .5*math.sin(a+1.4))
    return base + flutes*t + shoulder + lip


def point(t, a, inner=False):
    side, up = frame(t)
    radius = outer_radius(t, a)
    if inner:
        radius = max(.75, radius - (5.3 + 1.8*t))
    ellipse_side = 1.08
    ellipse_up = .80 + .05*math.sin(math.pi*t)
    p = center(t) + radius*(ellipse_side*math.cos(a)*side + ellipse_up*math.sin(a)*up)
    # The opening is swept and high on one shoulder, not a frontal circle.
    p += Vector((0, 0, 8*t**10*math.sin(a)))
    return tuple(p)


def shell():
    rows, sides, inner_start = 144, 128, 20
    verts, faces, zones = [], [], []
    for j in range(rows+1):
        for i in range(sides):
            verts.append(point(j/rows, math.tau*i/sides))
    inner_offset = len(verts)
    for j in range(inner_start, rows+1):
        for i in range(sides):
            verts.append(point(j/rows, math.tau*i/sides, True))
    for j in range(rows):
        for i in range(sides):
            a=j*sides+i; b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
            zones.append(2 if j > rows-5 else 0)
    for j in range(rows-inner_start):
        for i in range(sides):
            a=inner_offset+j*sides+i; b=inner_offset+j*sides+(i+1)%sides
            faces.append((a+sides,b+sides,b,a))
            zones.append(1)
    for i in range(sides):
        nxt=(i+1)%sides
        faces.append((rows*sides+i, rows*sides+nxt,
                      inner_offset+(rows-inner_start)*sides+nxt,
                      inner_offset+(rows-inner_start)*sides+i))
        zones.append(2)
    faces.append(tuple(reversed(range(sides))))
    zones.append(0)
    faces.append(tuple(inner_offset+i for i in range(sides)))
    zones.append(1)
    mesh=bpy.data.meshes.new("carved_hollow_horn_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj=bpy.data.objects.new("continuous_ebbhorn_shell",mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("calcified_ochre_shell",(.58,.43,.30),.76))
    obj.data.materials.append(material("dark_rose_inner_cavity",(.37,.19,.22),.72))
    obj.data.materials.append(material("bone_worn_mouth",(.72,.59,.43),.68))
    for poly,zone in zip(mesh.polygons,zones):
        poly.material_index=zone
        poly.use_smooth=True
    bevel=obj.modifiers.new("soft_shell_lip","BEVEL")
    bevel.width=1.2
    bevel.segments=2
    bevel.limit_method="ANGLE"
    return obj


def setup_scene():
    scene=bpy.context.scene
    scene.unit_settings.system="METRIC"
    scene.unit_settings.scale_length=.001
    scene.render.engine="CYCLES"
    scene.cycles.samples=20
    scene.render.resolution_x=1450
    scene.render.resolution_y=1120
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.look="Medium High Contrast"
    scene.view_settings.exposure=2.0
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.015,.009,.009,1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.65
    bpy.ops.object.empty_add(type="PLAIN_AXES",location=(0,0,14))
    target=bpy.context.object
    bpy.ops.object.camera_add(location=(250,-280,125))
    camera=bpy.context.object
    camera.data.type="ORTHO"
    camera.data.ortho_scale=248
    scene.camera=camera
    track=camera.constraints.new(type="TRACK_TO")
    track.target=target
    track.track_axis="TRACK_NEGATIVE_Z"
    track.up_axis="UP_Y"
    for loc,power,color,size in (
        ((-110,-170,185),31000,(1,.84,.68),125),
        ((145,-80,70),19000,(1,.68,.51),105),
        ((20,125,130),25000,(.93,.70,.66),125),
        ((220,-200,30),12000,(1,.79,.69),110),
    ):
        bpy.ops.object.light_add(type="AREA",location=loc)
        lamp=bpy.context.object
        lamp.data.energy=power
        lamp.data.color=color
        lamp.data.size=size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj=shell()
    setup_scene()
    STL.parent.mkdir(parents=True,exist_ok=True)
    GLB.parent.mkdir(parents=True,exist_ok=True)
    PNG.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format="GLB",use_selection=True,export_apply=True)
    scene=bpy.context.scene
    scene.render.film_transparent=True
    scene.render.filepath=str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent=False
    scene.render.filepath=str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__=="__main__":
    main()
