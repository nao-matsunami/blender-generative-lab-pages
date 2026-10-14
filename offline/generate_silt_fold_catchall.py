"""Make a one-piece, asymmetric catchall with a continuous open basin in Blender GUI."""
import math
import os
from pathlib import Path
import bpy

ROOT = Path(os.environ.get('BLENDER_LAB_ROOT', Path(__file__).resolve().parents[1]))
SLUG = 'silt-fold-catchall'
STL = ROOT / 'exports/stl' / (SLUG + '.stl')
GLB = ROOT / 'exports/glb' / (SLUG + '.glb')
PNG = ROOT / 'renders' / (SLUG + '.png')
PREVIEW = ROOT / 'renders' / (SLUG + '-preview.png')


def material(name, color, rough=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    return mat


def contour(a, scale, z, pleat=0):
    wave = 1 + .075 * math.sin(3*a+.48) + .038 * math.sin(7*a-1.2)
    back = max(0, math.sin(a))
    rib = pleat * back**1.4 * math.sin(12*a + .35)
    r = scale * (wave + rib)
    return (112*r*math.cos(a) + 9*r*math.sin(2*a),
            65*r*math.sin(a) + 8*r*math.cos(a), z)


def make_object():
    n = 256
    vertices, faces, zones = [], [], []
    # Outer wall rises from a broad stable foot; the inner wall slopes into the basin.
    rings = [(.70, 0, 0), (.85, .5, 0), (.94, 3.5, .022),
             (1.0, None, .043), (.965, None, .038),
             (.85, None, .015), (.66, 8.0, 0), (.40, 5.7, 0), (.13, 5.2, 0)]
    for idx, (scale, fixed_z, pleat) in enumerate(rings):
        for i in range(n):
            a = 2*math.pi*i/n
            back = max(0, math.sin(a))
            crest = 12 + 45*back**1.8 + 6.5*math.sin(2*a+.7)*back
            if idx == 3:
                z = crest
            elif idx == 4:
                z = crest - .8
            elif idx == 5:
                z = 9.5 + .64*crest
            else:
                z = fixed_z
            vertices.append(contour(a, scale, z, pleat))
    for j in range(len(rings)-1):
        for i in range(n):
            ni=(i+1)%n
            faces.append((j*n+i, j*n+ni, (j+1)*n+ni, (j+1)*n+i))
            zones.append(0 if j < 3 else (2 if j < 5 else 1))
    bottom_idx=len(vertices)
    vertices.append((0, 0, 0))
    top_idx=len(vertices)
    vertices.append((0, 0, 5.2))
    for i in range(n):
        ni=(i+1)%n
        faces.append((bottom_idx, ni, i))
        zones.append(0)
        k=(len(rings)-1)*n
        faces.append((top_idx, k+i, k+ni))
        zones.append(1)
    mesh=bpy.data.meshes.new('continuous_silt_fold_basin_mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj=bpy.data.objects.new('one_piece_open_catchall', mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (
        material('smoked_rose_ceramic', (.43,.28,.29)),
        material('matte_wine_interior', (.24,.13,.16)),
        material('chalk_ochre_integral_lip', (.48,.34,.29), .69),
    ):
        mesh.materials.append(mat)
    for poly, zone in zip(mesh.polygons, zones):
        poly.material_index=zone
        poly.use_smooth=True
    bevel=obj.modifiers.new('soft_ceramic_rim', 'BEVEL')
    bevel.width=.6
    bevel.segments=2
    bevel.limit_method='ANGLE'
    weighted=obj.modifiers.new('weighted_surface_normals','WEIGHTED_NORMAL')
    return obj


def scene_setup():
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.001
    scene.render.engine='CYCLES'
    scene.cycles.samples=20
    scene.render.resolution_x=1450
    scene.render.resolution_y=1120
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=2.5
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value=(.015,.009,.012,1)
    bg.inputs['Strength'].default_value=.7
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,13))
    target=bpy.context.object
    bpy.ops.object.camera_add(location=(165,-225,118))
    camera=bpy.context.object
    camera.data.type='ORTHO'
    camera.data.ortho_scale=275
    scene.camera=camera
    track=camera.constraints.new(type='TRACK_TO')
    track.target=target
    track.track_axis='TRACK_NEGATIVE_Z'
    track.up_axis='UP_Y'
    for location,energy,color,size in (
        ((-100,-125,155),25000,(1,.84,.75),100),
        ((105,-10,90),15000,(1,.57,.43),95),
        ((10,120,160),24000,(.87,.69,.71),110),
    ):
        bpy.ops.object.light_add(type='AREA',location=location)
        light=bpy.context.object
        light.data.energy=energy
        light.data.color=color
        light.data.size=size


def export(obj):
    STL.parent.mkdir(parents=True,exist_ok=True)
    GLB.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.wm.stl_export(filepath=str(STL),export_selected_objects=True,apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True)


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
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    obj=make_object()
    scene_setup()
    export(obj)
    render()

if __name__=='__main__':
    main()
