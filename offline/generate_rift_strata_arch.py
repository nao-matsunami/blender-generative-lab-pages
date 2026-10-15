"""Make an asymmetric, perforated fossil arch in the running Blender GUI."""
import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get('BLENDER_LAB_ROOT', Path(__file__).resolve().parents[1]))
SLUG = 'rift-strata-arch'
STL = ROOT / 'exports/stl' / f'{SLUG}.stl'
GLB = ROOT / 'exports/glb' / f'{SLUG}.glb'
PNG = ROOT / 'renders' / f'{SLUG}.png'
PREVIEW = ROOT / 'renders' / f'{SLUG}-preview.png'


def material():
    mat = bpy.data.materials.new('chalk_umber_strata')
    mat.diffuse_color = (.58, .48, .37, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .89
    tex = nodes.new('ShaderNodeTexCoord')
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 5.5
    wave.inputs['Distortion'].default_value = 4.0
    wave.inputs['Detail'].default_value = 3
    links.new(tex.outputs['Generated'], wave.inputs['Vector'])
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 11
    noise.inputs['Detail'].default_value = 3
    links.new(tex.outputs['Generated'], noise.inputs['Vector'])
    blend = nodes.new('ShaderNodeMixRGB')
    blend.blend_type = 'MIX'
    blend.inputs[0].default_value = .14
    links.new(noise.outputs['Fac'], blend.inputs[1])
    links.new(wave.outputs['Color'], blend.inputs[2])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .28
    ramp.color_ramp.elements[0].color = (.27, .23, .19, 1)
    ramp.color_ramp.elements[1].position = .74
    ramp.color_ramp.elements[1].color = (.88, .81, .69, 1)
    links.new(blend.outputs[0], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .24
    bump.inputs['Distance'].default_value = .55
    links.new(blend.outputs[0], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def arch():
    # A single open, grounded outline. The irregular upper ridge and unequal feet
    # distinguish this fossil from yesterday's concentric shallow basin.
    outline = [
        (-101,-57),(-109,-35),(-104,-13),(-95,15),(-77,36),
        (-57,52),(-32,57),(-9,44),(12,48),(33,67),(56,61),
        (75,47),(94,19),(99,-10),(87,-41),(80,-57),
        (56,-57),(61,-32),(50,-8),(35,8),(13,19),
        (-13,14),(-36,-3),(-53,-31),(-55,-57)
    ]
    n = len(outline)
    verts = [(x, -12 + 1.6*math.sin(i*1.91), z) for i,(x,z) in enumerate(outline)]
    verts += [(x, 11 + 1.2*math.sin(i*1.29), z) for i,(x,z) in enumerate(outline)]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new('continuous_broken_arch_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('one_piece_rift_strata_arch', mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Unequal, structural perforations carry through the thickness.
    for x,z,rx,rz,angle in [(-82,0,10,17,-.28),(60,30,9,15,.42)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(x,0,z))
        cutter = bpy.context.object
        cutter.scale = (rx, 45, rz)
        cutter.rotation_euler[1] = angle
        bpy.context.view_layer.objects.active = obj
        mod = obj.modifiers.new('eroded_through_aperture','BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)

    remesh = obj.modifiers.new('fuse_eroded_stone','REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 1.55
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    soften = obj.modifiers.new('weathered_edges','SMOOTH')
    soften.factor = 1.0
    soften.iterations = 2
    bpy.ops.object.modifier_apply(modifier=soften.name)
    erosion = bpy.data.textures.new('granular_stone_erosion', type='CLOUDS')
    erosion.noise_scale = 7.0
    displace = obj.modifiers.new('shallow_erosion','DISPLACE')
    displace.texture = erosion
    displace.strength = 1.6
    bpy.ops.object.modifier_apply(modifier=displace.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.materials.append(material())
    return obj


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = .001
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 20
    scene.render.resolution_x = 1450
    scene.render.resolution_y = 1120
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 2.35
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (.015,.011,.01,1)
    bg.inputs['Strength'].default_value = .7
    bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,4))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(215,-260,150))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 255
    scene.camera = camera
    track = camera.constraints.new(type='TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    for loc,power,color,size in [
        ((-120,-115,160),26000,(1,.85,.68),100),
        ((110,-45,100),16000,(1,.72,.48),90),
        ((20,95,130),20000,(.88,.73,.61),105),
    ]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        light = bpy.context.object
        light.data.energy = power
        light.data.color = color
        light.data.size = size


def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    obj = arch()
    setup_scene()
    STL.parent.mkdir(parents=True,exist_ok=True)
    GLB.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True)
    PNG.parent.mkdir(parents=True,exist_ok=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
