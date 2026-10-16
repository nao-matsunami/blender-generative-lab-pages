"""Build Loomfall Veil inside the running Blender GUI watcher."""
import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get('BLENDER_LAB_ROOT', Path(__file__).resolve().parents[1]))
SLUG = 'loomfall-veil'
STL = ROOT / 'exports/stl' / f'{SLUG}.stl'
GLB = ROOT / 'exports/glb' / f'{SLUG}.glb'
PNG = ROOT / 'renders' / f'{SLUG}.png'
PREVIEW = ROOT / 'renders' / f'{SLUG}-preview.png'


def make_material(name, color, roughness, transmission=0.0, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Transmission Weight'].default_value = transmission
    return mat


def mesh_object(name, verts, faces, material):
    mesh = bpy.data.meshes.new(name + '_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def panel(name, x0, width, drop, phase, depth, material, hem_material, back=False):
    # Vertical pleats become deeper towards the free edge. Three panels have
    # different lengths and skew, so their lower silhouette reads as fabric.
    nu, nv = 48, 30
    verts, faces = [], []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            x = x0 + width*u + (9 if back else 5)*v*v*(u-.35)
            top = 49 + 4*math.sin((x+70)*.023) + 2.4*math.sin((x+40)*.066)
            edge = -drop + 10*math.sin(u*math.pi*1.25 + phase) - 8*u
            z = top*(1-v) + edge*v - 3.5*math.sin(v*math.pi)*math.cos(2*math.pi*u+phase)
            fold = math.sin(2*math.pi*(4.2*u + .10*v) + phase)
            y = depth + (3.5 + 7*v)*fold + 4*math.sin(v*math.pi) + 1.5*u*v
            verts.append((x,y,z))
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i
            faces.append((a,a+1,a+nu+2,a+nu+1))
    obj=mesh_object(name,verts,faces,material)
    solid=obj.modifiers.new('woven_skin_thickness','SOLIDIFY')
    solid.thickness=1.7 if back else 2.4
    solid.offset=0
    bevel=obj.modifiers.new('soft_cut_edge','BEVEL')
    bevel.width=.55
    bevel.segments=2
    obj.data.materials.append(hem_material)
    # Color the final row like a broad, integral selvedge instead of piping.
    for poly in obj.data.polygons:
        if poly.index // nu >= nv - 5:
            poly.material_index=1
    return obj


def header(material):
    # One continuous sculpted clamp visibly captures all four membrane roots.
    profile=[(-130,43),(-129,51),(-119,57),(-84,60),(-34,56),
             (14,62),(70,58),(116,50),(124,44),(123,40),
             (77,45),(17,49),(-37,44),(-86,48)]
    n=len(profile)
    verts=[(x,y,z) for y in (-12,13) for x,z in profile]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=mesh_object('continuous_warp_clamp',verts,faces,material)
    bevel=obj.modifiers.new('worked_clamp_edges','BEVEL')
    bevel.width=2
    bevel.segments=3
    return obj


def setup_scene():
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.001
    scene.render.engine='CYCLES'
    scene.cycles.samples=20
    scene.render.resolution_x=1500
    scene.render.resolution_y=1150
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=2.25
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(.018,.011,.017,1)
    bg.inputs['Strength'].default_value=.8
    bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,-8))
    target=bpy.context.object
    bpy.ops.object.camera_add(location=(110,-380,65))
    camera=bpy.context.object
    camera.data.type='ORTHO'
    camera.data.ortho_scale=300
    scene.camera=camera
    track=camera.constraints.new(type='TRACK_TO')
    track.target=target
    track.track_axis='TRACK_NEGATIVE_Z'
    track.up_axis='UP_Y'
    for loc,power,color,size in [
        ((-130,-170,140),34000,(1,.84,.78),125),
        ((120,35,125),28000,(1,.68,.8),130),
        ((-20,-110,-5),17000,(1,.72,.65),100),
    ]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        light=bpy.context.object
        light.data.energy=power
        light.data.color=color
        light.data.size=size


def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    shell=make_material('frosted_muted_rose',(.72,.35,.4),.62,.1)
    shell_light=make_material('rose_quartz_weft',(.9,.55,.52),.58,.1)
    shadow=make_material('violet_black_reverse',(.31,.16,.25),.72,.04)
    edge=make_material('integral_dark_selvedge',(.32,.15,.22),.76)
    clamp=make_material('patinated_plum_clamp',(.27,.14,.22),.48,0,.33)
    parts=[
        panel('rear_shadow_veil',-113,223,67,.5,16,shadow,edge,True),
        panel('left_rose_drape',-116,77,69,.3,-2,shell,edge),
        panel('long_quartz_drape',-36,74,91,1.4,-2,shell_light,edge),
        panel('right_rose_drape',42,78,61,2.3,-2,shell,edge),
        header(clamp),
    ]
    setup_scene()
    STL.parent.mkdir(parents=True,exist_ok=True)
    GLB.parent.mkdir(parents=True,exist_ok=True)
    PNG.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts: obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[-1]
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True)
    scene=bpy.context.scene
    scene.render.film_transparent=True
    scene.render.filepath=str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent=False
    scene.render.filepath=str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
