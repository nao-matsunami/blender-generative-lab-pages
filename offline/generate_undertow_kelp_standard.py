"""Grow a current-bent kelp standard in the active Blender GUI watcher."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "undertow-kelp-standard"
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


def mesh_object(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def stem_center(t):
    return Vector((-24 + 35*t - 13*t*t, 5*math.sin(math.pi*t), -88 + 174*t))


def build_stem(mat):
    verts, faces = [], []
    rings, sides = 120, 24
    for j in range(rings + 1):
        t = j/rings
        c = stem_center(t)
        radius = 8.8*(1-t)**.65 + 2.0
        radius += 1.6*math.exp(-((t-.03)/.055)**2)
        for i in range(sides):
            a = math.tau*i/sides
            groove = 1 + .055*math.cos(7*a + 1.8*t)
            verts.append((c.x + radius*math.cos(a)*groove,
                          c.y + radius*.78*math.sin(a)*groove,
                          c.z + 1.1*math.sin(a+5*t)))
    for j in range(rings):
        for i in range(sides):
            a=j*sides+i
            b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(rings*sides+i for i in range(sides)))
    return mesh_object("continuous_bent_holdfast_and_stipe", verts, faces, mat)


def bezier(a, b, c, d, t):
    return a*(1-t)**3 + b*3*(1-t)**2*t + c*3*(1-t)*t*t + d*t**3


def blade(name, root_t, direction, reach, rise, width, yaw, phase, mat):
    root = stem_center(root_t)
    root.x += direction*4
    root.y -= 2
    end = root + Vector((direction*reach, yaw, rise))
    ctrl1 = root + Vector((direction*reach*.27, -13 + yaw*.18, rise*.57))
    ctrl2 = root + Vector((direction*reach*.91, yaw*.66, rise*.97))
    verts, faces = [], []
    rows, cols = 92, 18
    for j in range(rows+1):
        t=j/rows
        center=bezier(root,ctrl1,ctrl2,end,t)
        # Each blade is a continuous, thick sheet with a curled midrib and pinched tip.
        half=width*1.75*(t**.7)*((1-t)**.9)
        center.y += 16*math.sin(math.pi*t)*math.sin(phase + 3.4*t)
        for i in range(cols+1):
            v=(i/cols)*2-1
            edge_scallop=1-.16*math.exp(-((t-.37)/.045)**2)-.12*math.exp(-((t-.68)/.055)**2)
            span=half*v*edge_scallop
            twist=phase*.18 + 2.2*t
            z=center.z + span*.68*math.cos(twist) + 3.8*(1-v*v)*math.sin(math.pi*t)
            y=center.y + span*.68*math.sin(twist) - 7.5*(1-v*v)*math.sin(math.pi*t)
            x=center.x + direction*span*.23
            verts.append((x,y,z))
    for j in range(rows):
        for i in range(cols):
            a=j*(cols+1)+i
            faces.append((a,a+1,a+cols+2,a+cols+1))
    obj=mesh_object(name,verts,faces,mat)
    solid=obj.modifiers.new("leathery_blade_thickness","SOLIDIFY")
    solid.thickness=2.2
    solid.offset=0
    bevel=obj.modifiers.new("soft_living_edge","BEVEL")
    bevel.width=.45
    bevel.segments=2
    return obj


def setup_scene():
    scene=bpy.context.scene
    scene.unit_settings.system="METRIC"
    scene.unit_settings.scale_length=.001
    scene.render.engine="CYCLES"
    scene.cycles.samples=20
    scene.render.resolution_x=1250
    scene.render.resolution_y=1350
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.view_settings.look="Medium High Contrast"
    scene.view_settings.exposure=2.0
    scene.world.use_nodes=True
    world_bg=scene.world.node_tree.nodes.get("Background")
    world_bg.inputs["Color"].default_value=(.009,.004,.007,1)
    world_bg.inputs["Strength"].default_value=.35
    bpy.ops.object.empty_add(type="PLAIN_AXES",location=(6,0,0))
    target=bpy.context.object
    bpy.ops.object.camera_add(location=(250,-250,145))
    camera=bpy.context.object
    camera.data.type="ORTHO"
    camera.data.ortho_scale=275
    scene.camera=camera
    track=camera.constraints.new(type="TRACK_TO")
    track.target=target
    track.track_axis="TRACK_NEGATIVE_Z"
    track.up_axis="UP_Y"
    for loc,power,color,size in (
        ((-135,-120,175),26000,(1,.83,.66),100),
        ((90,-60,60),14500,(1,.54,.43),88),
        ((25,110,85),26000,(.9,.62,.69),105),
        ((75,-185,125),12500,(1,.82,.72),125),
    ):
        bpy.ops.object.light_add(type="AREA",location=loc)
        lamp=bpy.context.object
        lamp.data.energy=power
        lamp.data.color=color
        lamp.data.size=size


def export(objects):
    STL.parent.mkdir(parents=True,exist_ok=True)
    GLB.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format="GLB",use_selection=True,export_apply=True)


def render():
    PNG.parent.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.render.film_transparent=True
    scene.render.filepath=str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent=False
    scene.render.filepath=str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    stem=material("dark_amber_holdfast",(.43,.23,.16),.56)
    pale=material("ochre_rose_frond",(.65,.35,.25),.69)
    dusk=material("bruised_plum_frond",(.46,.25,.31),.66)
    bone=material("clouded_shell_frond",(.72,.56,.43),.72)
    objects=[build_stem(stem)]
    specs=[
        ("lower_larboard",.18,-1,77,-12,13,-25,.3,dusk),
        ("lower_starboard",.26,1,98,-5,18,-34,1.4,pale),
        ("middle_larboard",.44,-1,100,22,20,-26,2.0,bone),
        ("middle_starboard",.54,1,112,27,23,-42,.6,pale),
        ("upper_larboard",.67,-1,76,40,15,-22,1.7,dusk),
        ("crown_starboard",.78,1,77,52,16,-30,2.5,bone),
    ]
    objects.extend(blade(*spec) for spec in specs)
    setup_scene()
    export(objects)
    render()


if __name__=="__main__":
    main()
