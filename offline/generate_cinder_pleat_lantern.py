"""Build a single-piece perforated lantern shell in the running Blender GUI."""

import math
import os
from pathlib import Path

import bpy

ROOT = Path(os.environ.get("BLENDER_LAB_ROOT", Path(__file__).resolve().parents[1]))
SLUG = "cinder-pleat-lantern"
STL = ROOT / "exports/stl" / f"{SLUG}.stl"
GLB = ROOT / "exports/glb" / f"{SLUG}.glb"
PNG = ROOT / "renders" / f"{SLUG}.png"
PREVIEW = ROOT / "renders" / f"{SLUG}-preview.png"


def material(name, color, rough=.72):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def angle_delta(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def radius(t, angle):
    # A broad, flat foot rises into a leaning shoulder and an open narrow mouth.
    profile = 52 + 11 * math.sin(math.pi * t) ** 2 - 17 * t
    foot = 4.5 * math.exp(-((t - .025) / .065) ** 2)
    lip = 4.0 * math.exp(-((t - .97) / .045) ** 2)
    irregular_pleat = (4.8 + 3.0 * math.sin(math.pi * t) ** 2) * (
        .60 * math.cos(9 * angle + 1.4 * t)
        + .25 * math.cos(13 * angle - 2.2 * t)
        + .15 * math.cos(5 * angle + 3.0 * t)
    )
    return profile + foot + lip + irregular_pleat


def shell():
    around, high = 384, 168
    verts, faces, zones = [], [], []
    for j in range(high + 1):
        t = j / high
        z = 126 * t
        lean_x = 12 * t * t
        lean_y = -7 * math.sin(math.pi * t)
        for i in range(around):
            a = 2 * math.pi * i / around
            r = radius(t, a)
            verts.append((lean_x + 1.10 * r * math.cos(a), lean_y + .87 * r * math.sin(a), z))

    for j in range(high):
        t = (j + .5) / high
        for i in range(around):
            b = j * around + i
            n = j * around + (i + 1) % around
            faces.append((b, n, n + around, b + around))
            zones.append(1 if t < .11 or t > .93 else 0)

    mesh = bpy.data.meshes.new("open_pleated_shell_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("single_piece_perforated_lantern", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material("warm_calcined_ochre", (.72, .50, .30)))
    obj.data.materials.append(material("dark_umber_rim", (.36, .20, .12)))
    obj.data.materials.append(material("cut_clay_wall", (.52, .28, .16)))
    for poly, zone in zip(mesh.polygons, zones):
        poly.material_index = zone
        poly.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    thick = obj.modifiers.new("printable_shell_and_opening_walls", "SOLIDIFY")
    thick.thickness = 3.4
    thick.offset = -1
    thick.use_even_offset = True
    thick.material_offset = 2
    thick.material_offset_rim = 2
    bpy.ops.object.modifier_apply(modifier=thick.name)
    # Ellipsoidal boolean cuts keep the window walls continuous and smooth.
    for name, angle, height, width, vertical in (
        ("west_tall_window", -1.53, .50, 20, 31),
        ("front_low_window", -.55, .43, 16, 36),
    ):
        r = radius(height, angle)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48,
            location=(12 * height * height + 1.10 * r * math.cos(angle),
                      -7 * math.sin(math.pi * height) + .87 * r * math.sin(angle),
                      126 * height))
        cutter = bpy.context.object
        cutter.name = name + "_cutter"
        cutter.scale = (28, width, vertical)
        cutter.rotation_euler[2] = angle
        bpy.context.view_layer.objects.active = cutter
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        cut = obj.modifiers.new(name, "BOOLEAN")
        cut.operation = "DIFFERENCE"
        cut.solver = "EXACT"
        cut.object = cutter
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=cut.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        if len(obj.data.polygons) < 100000:
            raise RuntimeError(f"Lantern shell collapsed after {name}")
    return obj


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 1500
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 2.15
    scene.world.color = (.025, .018, .013)
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(5, 0, 64))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(195, -235, 136))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 212
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    for location, energy, color, size in (
        ((-120, -150, 205), 16500, (1, .88, .71), 115),
        ((120, -60, 95), 9500, (1, .62, .39), 90),
        ((35, 105, 140), 10400, (.9, .76, .55), 100),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.color = color
        light.data.size = size
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 56))
    bpy.context.object.data.energy = 420
    bpy.context.object.data.color = (1, .35, .11)


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
    backdrop = material("charcoal_backdrop", (.007, .005, .005), 1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 90, 60), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.object
    plane.dimensions = (600, 600, 1)
    plane.data.materials.append(backdrop)
    scene.render.film_transparent = False
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    obj = shell()
    setup_scene()
    export(obj)
    render()


if __name__ == "__main__":
    main()
