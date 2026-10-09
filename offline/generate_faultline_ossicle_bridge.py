"""Build an eroded, connected fossil bridge in the running Blender GUI."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "faultline-ossicle-bridge"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def bone_material():
    mat = bpy.data.materials.new("weathered_ochre_bone")
    mat.diffuse_color = (.68, .60, .46, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = .82
    geometry = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.8
    noise.inputs["Detail"].default_value = 4
    links.new(geometry.outputs["Generated"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .25
    ramp.color_ramp.elements[0].color = (.32, .20, .12, 1)
    ramp.color_ramp.elements[1].position = .76
    ramp.color_ramp.elements[1].color = (.88, .79, .63, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .2
    bump.inputs["Distance"].default_value = .19
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def sweep(name, points, widths, depths, phase):
    """A broad irregular cross-section follows a hand-composed fossil strut."""
    centers = [Vector(p) for p in points]
    n = 72
    sides = 18
    vertices = []
    faces = []
    for step in range(n + 1):
        t = step / n
        k = min(int(t * (len(points) - 1)), len(points) - 2)
        f = t * (len(points) - 1) - k
        # Catmull-Rom: curved but anchored at each designed crossing.
        p0 = centers[max(0, k - 1)]
        p1 = centers[k]
        p2 = centers[k + 1]
        p3 = centers[min(len(points) - 1, k + 2)]
        pos = .5 * ((2 * p1) + (-p0 + p2) * f + (2*p0 - 5*p1 + 4*p2 - p3) * f*f + (-p0 + 3*p1 - 3*p2 + p3) * f*f*f)
        tangent = (p2 - p1).normalized()
        lateral = Vector((-tangent.z, 0, tangent.x)).normalized()
        across = tangent.cross(lateral).normalized()
        width = widths[k] * (1-f) + widths[k+1] * f
        depth = depths[k] * (1-f) + depths[k+1] * f
        # Ends are rounded; crossings overlap sufficiently for one solid.
        taper = .38 + .62 * min(1, t * 16, (1-t) * 16)
        for j in range(sides):
            a = j * math.tau / sides
            grain = 1 + .09 * math.sin(7*a + 13*t + phase) + .035 * math.sin(13*a - 19*t)
            v = pos + lateral * (width * taper * grain * math.cos(a)) + across * (depth * taper * grain * math.sin(a))
            vertices.append(tuple(v))
    for i in range(n):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(n*sides+j for j in range(sides)))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def make_fossil():
    specs = [
        ("swept_dorsal_keel", [(-90,-10,-37),(-68,-12,3),(-23,-5,45),(31,4,54),(77,12,35),(93,14,11)], [11,13,13,11,9,8], [8,10,9,9,8,7]),
        ("ventral_shelf", [(-78,-3,-47),(-45,0,-45),(-5,4,-28),(39,9,-21),(73,13,-7),(89,14,12)], [8,10,11,10,8,7], [7,9,9,8,7,6]),
        ("fractured_left_plate", [(-73,-11,-1),(-60,-6,-14),(-58,-1,-31),(-62,0,-47)], [10,11,8,6], [7,7,6,5]),
        ("wide_medial_plate", [(-29,-6,41),(-28,-2,17),(-20,3,-4),(-11,5,-30)], [12,14,12,9], [7,8,8,7]),
        ("off_axis_spur", [(15,1,53),(8,3,32),(15,7,4),(32,9,-19)], [10,12,11,8], [7,8,8,7]),
        ("distal_fold", [(67,11,39),(54,11,25),(52,12,9),(68,13,-9)], [8,10,10,7], [6,7,7,6]),
        ("left_heel", [(-90,-10,-37),(-90,-3,-51),(-72,0,-53)], [10,10,7], [8,8,7]),
        ("broken_crest", [(-32,-6,40),(-45,-9,59),(-53,-14,76)], [11,8,4], [8,7,4]),
    ]
    parts = [sweep(name, pts, widths, depths, i*1.7) for i, (name, pts, widths, depths) in enumerate(specs)]
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "single_fused_fossil_bridge"
    remesh = obj.modifiers.new("fuse_crossing_strata", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 1.1
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth = obj.modifiers.new("water_worn_edges", "SMOOTH")
    smooth.factor = 1.25
    smooth.iterations = 3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.materials.append(bone_material())
    return obj


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 20
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.0
    scene.world.color = (.023,.018,.016)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(2,1,2))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(210,-270,145))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 240
    scene.camera = camera
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    for loc, power, color, size in (
        ((-120,-110,175), 17500, (1,.86,.67), 105),
        ((100,-50,85), 8000, (1,.72,.43), 90),
        ((30,100,110), 12500, (.8,.65,.52), 100),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy = power
        light.data.color = color
        light.data.size = size


def export(obj):
    STL.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(STL), export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=True)


def render():
    PNG.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.film_transparent = True
    scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    dark = bpy.data.materials.new("warm_charcoal_backdrop")
    dark.diffuse_color = (.008,.006,.005,1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0,85,0), rotation=(math.pi/2,0,0))
    plane = bpy.context.object
    plane.dimensions = (650,650,1)
    plane.data.materials.append(dark)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = make_fossil()
    setup_scene()
    export(obj)
    render()


if __name__ == "__main__":
    main()
