"""Generate Tidal Ossicle Canopy assets in Blender GUI."""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1])).resolve()
SLUG = "tidal-ossicle-canopy"
STL_PATH = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports/glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def material(name, color, roughness, metallic=0.0, emission=0.0, texture=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    if texture:
        scale, strength, distance = texture
        noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = scale
        noise.inputs["Detail"].default_value = 5.0
        noise.inputs["Roughness"].default_value = 0.7
        bump = mat.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = strength
        bump.inputs["Distance"].default_value = distance
        mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def bevel(obj, width=1.1, segments=4):
    modifier = obj.modifiers.new("water_worn_edge", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    return smooth(obj)


def add_curve(name, points, depth, mat, parent=None, cyclic=False):
    curve = bpy.data.curves.new(name + "_curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 20
    curve.bevel_depth = depth
    curve.bevel_resolution = 8
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    spline.use_cyclic_u = cyclic
    for index, (point, coords) in enumerate(zip(spline.bezier_points, points)):
        point.co = coords
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
        point.radius = 1.18 - 0.58 * index / max(1, len(points) - 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def add_leaf(name, location, scale, rotation, mat, parent):
    segments = 24
    vertices = []
    for side_y in (-0.12, 0.12):
        for index in range(segments + 1):
            t = index / segments
            x = -1.0 + 2.0 * t
            width = math.sin(math.pi * t) ** 0.72
            camber = 0.24 * math.sin(math.pi * t) + 0.08 * x
            vertices.extend(((x, side_y + camber, -width), (x, side_y + camber, width)))
    stride = (segments + 1) * 2
    faces = []
    for index in range(segments):
        a = index * 2
        faces.append((a, a + 2, a + 3, a + 1))
        b = stride + a
        faces.append((b, b + 1, b + 3, b + 2))
        faces.append((a, b, b + 2, a + 2))
        faces.append((a + 1, a + 3, b + 3, b + 1))
    faces.extend(((0, 1, stride + 1, stride), (segments * 2, stride + segments * 2, stride + segments * 2 + 1, segments * 2 + 1)))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    obj.parent = parent
    return bevel(obj, 1.8, 6)


def add_torus(name, location, major, minor, rotation, scale, mat, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=128, minor_segments=24, major_radius=major, minor_radius=minor, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    obj.parent = parent
    return smooth(obj)


def add_sphere(name, location, scale, mat, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    obj.parent = parent
    return smooth(obj)


def add_parts():
    bone = material("salt_bleached_ossicle", (0.66, 0.59, 0.47), 0.58, texture=(4.8, 0.23, 0.12))
    ochre = material("tidal_ochre_joint", (0.35, 0.18, 0.055), 0.46, texture=(6.0, 0.18, 0.09))
    membrane = material("bruised_kelp_membrane", (0.20, 0.012, 0.052), 0.3, emission=0.012, texture=(3.6, 0.14, 0.08))
    void = material("pod_internal_void", (0.004, 0.001, 0.003), 0.1)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    sway = bpy.context.object
    sway.name = "canopy_sway_animation_root"
    objects = [sway]

    trunk_a = [(-35,-4,-70),(-38,-8,-30),(-20,-12,12),(7,-5,53),(36,4,79)]
    trunk_b = [(-26,8,-65),(-7,4,-36),(21,-8,-10),(48,-12,25),(56,-4,58)]
    trunk_c = [(-43,15,-60),(-63,10,-26),(-58,2,10),(-43,-6,42),(-55,-10,72)]
    objects.append(add_curve("primary_calcified_frond", trunk_a, 6.2, bone, sway))
    objects.append(add_curve("forward_branching_frond", trunk_b, 4.8, bone, sway))
    objects.append(add_curve("rear_hooked_frond", trunk_c, 5.4, ochre, sway))
    objects.append(add_curve("upper_bridge_branch", [(7,-1,53),(28,-2,61),(56,2,58)], 3.8, bone, sway))
    objects.append(add_curve("lower_bridge_branch", [(-38,0,-30),(-8,-3,-18),(21,-4,-10)], 3.5, ochre, sway))
    objects.append(add_curve("cross_current_branch", [(-58,2,10),(-26,-7,23),(7,-5,53)], 3.1, bone, sway))
    objects.append(add_curve("pod_cradle_branch", [(-20,-12,12),(-7,-9,2),(3,-5,11)], 2.8, ochre, sway))

    objects.append(add_leaf("upper_manta_leaf", (24,-8,58), (32,4.0,21), (0.18,-0.48,0.48), membrane, sway))
    objects.append(add_leaf("right_folded_leaf", (49,4,22), (27,3.4,17), (-0.25,0.38,-0.34), membrane, sway))
    objects.append(add_leaf("left_low_leaf", (-44,12,-20), (24,3.1,15), (0.28,-0.3,1.02), membrane, sway))
    objects.append(add_leaf("rear_shadow_leaf", (-28,8,38), (23,2.8,14), (-0.2,0.4,2.18), membrane, sway))

    objects.append(add_torus("suspended_seed_pod_rim", (1,-5,12), 23, 4.2, (math.radians(88),math.radians(14),math.radians(18)), (1.15,0.78,1), bone, sway))
    objects.append(add_sphere("seed_pod_dark_recess", (3,4,11), (20,5,15), void, sway))
    objects.append(add_curve("pod_suspension_tendon", [(-12,-1,31),(-4,-4,23),(1,-5,12)], 2.8, ochre, sway))

    for index, (location, scale) in enumerate((((-34,1,-68),(15,9,9)),((-18,1,-64),(12,8,8)),((-31,3,-52),(10,7,7)))):
        objects.append(add_sphere(f"fused_reef_anchor_{index+1}", location, scale, bone if index != 1 else ochre, sway))

    sway.rotation_euler = (0,0,math.radians(-4))
    sway.keyframe_insert(data_path="rotation_euler", frame=1)
    sway.rotation_euler = (math.radians(3),math.radians(-5),math.radians(5))
    sway.keyframe_insert(data_path="rotation_euler", frame=120)
    sway.rotation_euler = (0,0,math.radians(-4))
    sway.keyframe_insert(data_path="rotation_euler", frame=240)
    return objects


def convert_curves(objects):
    for obj in objects:
        if obj.type == "CURVE":
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target="MESH")
            obj.select_set(False)
    return objects


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 1700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.35
    scene.world.color = (0.0015,0.001,0.0015)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0,0,4))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(155,-315,88))
    camera = bpy.context.object
    camera.data.lens = 58
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    track.target = target
    for location, energy, color, size in (
        ((-120,-145,190),7200,(1.0,0.66,0.38),125),
        ((120,-60,-35),4100,(0.48,0.025,0.08),90),
        ((20,45,130),2600,(0.72,0.48,0.25),80),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light=bpy.context.object
        light.data.energy=energy
        light.data.color=color
        light.data.size=size


def add_backdrop():
    mat=material("abyssal_backdrop",(0.002,0.0015,0.002),0.98)
    bpy.ops.mesh.primitive_plane_add(size=1,location=(0,90,0),rotation=(math.radians(90),0,0))
    obj=bpy.context.object
    obj.dimensions=(650,720,1)
    obj.data.materials.append(mat)


def export_assets(objects):
    STL_PATH.parent.mkdir(parents=True,exist_ok=True)
    GLB_PATH.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=next(obj for obj in objects if obj.type=="MESH")
    try: bpy.ops.wm.stl_export(filepath=str(STL_PATH),export_selected_objects=True,apply_modifiers=True)
    except Exception: bpy.ops.export_mesh.stl(filepath=str(STL_PATH),use_selection=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH),export_format="GLB",use_selection=True,export_animations=True,export_apply=True)


def render_outputs():
    RENDER_PATH.parent.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.frame_set(52)
    scene.render.filepath=str(RENDER_PATH)
    scene.render.film_transparent=True
    bpy.ops.render.render(write_still=True)
    add_backdrop()
    scene.render.filepath=str(PREVIEW_PATH)
    scene.render.film_transparent=False
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()
    objects=convert_curves(add_parts())
    setup_scene()
    export_assets(objects)
    render_outputs()


if __name__=="__main__": main()
