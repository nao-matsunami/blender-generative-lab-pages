"""Build an asymmetric striated fossil plate in the running Blender GUI."""

import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "siltwing-fossil"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def prism(name, outline, bottom, top):
    count = len(outline)
    vertices = [(x, y, bottom) for x, y in outline]
    vertices += [(x, y, top) for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count)
              for i in range(count)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def stone_material():
    mat = bpy.data.materials.new("calcite_with_umber_bedding")
    mat.diffuse_color = (.70, .62, .49, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = .86
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.6
    noise.inputs["Detail"].default_value = 4
    wave = nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 12
    wave.inputs["Distortion"].default_value = 5
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .2
    ramp.color_ramp.elements[0].color = (.23, .17, .14, 1)
    ramp.color_ramp.elements[1].position = .77
    ramp.color_ramp.elements[1].color = (.95, .86, .74, 1)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = .38
    links.new(noise.outputs["Fac"], mix.inputs[1])
    links.new(wave.outputs["Fac"], mix.inputs[2])
    links.new(mix.outputs[0], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .16
    bump.inputs["Distance"].default_value = .24
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_fossil():
    # The broad, broken perimeter is a low wing, unlike yesterday's vertical ribbon.
    outer = [(-112, -27), (-107, -44), (-88, -55), (-50, -57), (-17, -46),
             (12, -48), (45, -36), (77, -33), (110, -15), (97, -1),
             (111, 16), (76, 35), (43, 36), (8, 52), (-28, 42),
             (-58, 49), (-94, 30), (-117, 5)]
    middle = [(-99, -20), (-83, -38), (-48, -43), (-15, -34), (17, -39),
              (48, -25), (80, -21), (92, -7), (68, 14), (38, 22),
              (2, 35), (-30, 27), (-61, 33), (-94, 11)]
    crest = [(-73, -13), (-45, -27), (-15, -20), (16, -29), (42, -12),
             (61, -7), (41, 2), (6, 13), (-28, 6), (-52, 15)]
    body = prism("single_fossil_plate", outer, 0, 11)
    prism("middle_bedding", middle, 8.5, 17)
    prism("off_axis_dorsal_keel", crest, 14.5, 24)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in [body, bpy.data.objects["middle_bedding"], bpy.data.objects["off_axis_dorsal_keel"]]:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    remesh = body.modifiers.new("fuse_bedding_into_one_stone", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 1.15
    apply(body, remesh)

    # Structural elongated holes pierce all three beds, with unequal directions.
    for x, y, rx, ry, angle in [(-61, -8, 19, 8, -.22), (20, -8, 28, 7, .31)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1, depth=100,
                                            location=(x, y, 8))
        cutter = bpy.context.object
        cutter.scale = (rx, ry, 1)
        cutter.rotation_euler[2] = angle
        bpy.context.view_layer.objects.active = body
        boolean = body.modifiers.new("open_eroded_fossil_window", "BOOLEAN")
        boolean.operation = "DIFFERENCE"
        boolean.solver = "EXACT"
        boolean.object = cutter
        apply(body, boolean)
        bpy.data.objects.remove(cutter, do_unlink=True)
    seal = body.modifiers.new("seal_cut_walls", "REMESH")
    seal.mode = "VOXEL"
    seal.voxel_size = .9
    apply(body, seal)
    smooth = body.modifiers.new("water_worn_edge", "SMOOTH")
    smooth.factor = 1.0
    smooth.iterations = 2
    apply(body, smooth)
    texture = bpy.data.textures.new("fine_stone_erosion", type="CLOUDS")
    texture.noise_scale = 5.5
    displace = body.modifiers.new("shallow_pitted_relief", "DISPLACE")
    displace.texture = texture
    displace.strength = .65
    apply(body, displace)
    for face in body.data.polygons:
        face.use_smooth = True
    body.data.materials.append(stone_material())
    return body


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 1450, 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.25
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.019, .014, .014, 1)
    bg.inputs["Strength"].default_value = .7
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-2, 0, 8))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(100, -175, 235))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 245
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis, track.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    for location, energy, color, size in (
        ((-115, -90, 170), 28000, (1, .88, .75), 110),
        ((115, -60, 115), 19000, (1, .72, .58), 90),
        ((15, 110, 145), 25000, (.91, .79, .74), 105),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.color, lamp.data.size = energy, color, size


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    body = make_fossil()
    setup_scene()
    for path in (STL, GLB, PNG, PREVIEW):
        path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True,
                              export_apply=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
