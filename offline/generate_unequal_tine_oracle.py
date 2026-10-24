"""Asymmetric two-tine ritual instrument, run inside the live Blender GUI watcher."""
import os
from pathlib import Path
import bpy

ROOT = Path(os.environ.get('BLENDER_LAB_ROOT', Path(__file__).resolve().parents[1]))
SLUG = 'unequal-tine-oracle'
STL = ROOT/'exports/stl'/f'{SLUG}.stl'
GLB = ROOT/'exports/glb'/f'{SLUG}.glb'
PNG = ROOT/'renders'/f'{SLUG}.png'
PREVIEW = ROOT/'renders'/f'{SLUG}-preview.png'


def material(name, color, rough=.58, metal=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metal
    return m


def prism(name, profile, front, back, mat, bevel=0):
    n=len(profile)
    verts=[(x,front,z) for x,z in profile]+[(x,back,z) for x,z in profile]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    mesh=bpy.data.meshes.new(name+'_mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('cast_edge_radius','BEVEL')
        mod.width=bevel
        mod.segments=3
        obj.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
    return obj


def cut(obj, profile):
    tool=prism('heel_window_cutting_tool',profile,-50,50,None)
    mod=obj.modifiers.new('true_heel_window','BOOLEAN')
    mod.operation='DIFFERENCE'
    mod.solver='EXACT'
    mod.object=tool
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool,do_unlink=True)


def build():
    bronze=material('plum_black_cast_bronze',(.49,.34,.39),.48,.48)
    copper=material('warm_rose_copper_contact',(.76,.48,.39),.43,.57)
    bone=material('ivory_ceramic_anvil',(.78,.68,.55),.64,.08)
    shadow=material('burnished_brown_heel',(.57,.37,.33),.58,.32)
    # The broad offset tines and weighted heel are one connected outline.
    body=prism('one_piece_unequal_fork',[
        (-102,-85),(89,-85),(104,-62),(100,-48),(56,-35),(45,-5),
        (62,62),(108,142),(101,162),(81,164),(69,148),(24,71),
        (5,11),(-14,-20),(-27,8),(-17,61),(-1,139),(-14,175),
        (-38,179),(-53,157),(-60,111),(-64,45),(-85,-20),(-105,-47)
    ],-16,16,bronze)
    tri=body.modifiers.new('prepare_boolean_faces','TRIANGULATE')
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.modifier_apply(modifier=tri.name)
    cut(body,[(-37,-69),(36,-69),(46,-61),(35,-49),(-32,-48),(-42,-59)])
    bevel=body.modifiers.new('cast_edge_softening','BEVEL')
    bevel.width=2.5; bevel.segments=3
    body.modifiers.new('corner_normals','WEIGHTED_NORMAL')
    # These wide contact shoes bury their roots in the casting and carry its silhouette.
    right=prism('right_tine_contact_shoe',[
        (68,85),(108,142),(101,162),(81,164),(69,148),(52,119)
    ],-19,-11,copper,1.3)
    left=prism('left_tine_ceramic_striker',[
        (-52,145),(-38,179),(-14,175),(-1,139),(-10,106),(-25,120),(-29,144)
    ],-21,-10,bone,1.2)
    heel=prism('load_bearing_offset_heel',[
        (51,-85),(89,-85),(104,-62),(100,-48),(79,-40),(70,-62)
    ],-19,21,shadow,1.6)
    return [body,right,left,heel]


def scene_setup():
    s=bpy.context.scene
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=.001
    s.render.engine='CYCLES';s.cycles.samples=18
    s.render.resolution_x=1180;s.render.resolution_y=1360;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    s.view_settings.look='Medium High Contrast';s.view_settings.exposure=2.15
    s.world.use_nodes=True
    bg=s.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(.018,.012,.018,1)
    bg.inputs['Strength'].default_value=.7
    bpy.ops.object.empty_add(type='PLAIN_AXES',location=(1,0,43));target=bpy.context.object
    bpy.ops.object.camera_add(location=(120,-340,145));camera=bpy.context.object
    camera.data.type='ORTHO';camera.data.ortho_scale=326;s.camera=camera
    track=camera.constraints.new(type='TRACK_TO');track.target=target
    track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y'
    for loc,power,color,size in (
        ((-130,-155,220),26000,(1,.86,.74),115),
        ((120,-95,125),22000,(1,.70,.60),105),
        ((65,100,180),28000,(.95,.76,.70),120),
        ((0,-190,40),18000,(1,.83,.77),115),
    ):
        bpy.ops.object.light_add(type='AREA',location=loc)
        l=bpy.context.object;l.data.energy=power;l.data.color=color;l.data.size=size


def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
    parts=build();scene_setup()
    for path in (STL,GLB,PNG,PREVIEW):path.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True)
    # A sealed print copy; presentation keeps the crisp material joints.
    bpy.ops.object.duplicate()
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    print_body=bpy.context.object
    seal=print_body.modifiers.new('fused_print_shell','REMESH')
    seal.mode='VOXEL';seal.voxel_size=.72
    bpy.ops.object.modifier_apply(modifier=seal.name)
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.data.objects.remove(print_body,do_unlink=True)
    s=bpy.context.scene
    s.render.film_transparent=True;s.render.filepath=str(PNG);bpy.ops.render.render(write_still=True)
    s.render.film_transparent=False;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True)

if __name__=='__main__':main()
