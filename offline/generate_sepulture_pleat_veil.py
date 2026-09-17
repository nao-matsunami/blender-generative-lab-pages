"""Generate Sepulture Pleat Veil assets in Blender.

Mac mini workflow:
npm run job:veil
"""

import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if "BLENDER_LAB_ROOT" in os.environ:
    ROOT = Path(os.environ["BLENDER_LAB_ROOT"]).resolve()

SLUG = "sepulture-pleat-veil"
STL_PATH = ROOT / "exports" / "stl" / f"{SLUG}.stl"
GLB_PATH = ROOT / "exports" / "glb" / f"{SLUG}.glb"
RENDER_PATH = ROOT / "renders" / f"{SLUG}.png"
PREVIEW_PATH = ROOT / "renders" / f"{SLUG}-preview.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def make_material(name, color, roughness, transmission=0.0, alpha=1.0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, alpha)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.22
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "DITHERED"
        elif hasattr(material, "blend_method"):
            material.blend_method = "BLEND"
    return material


def hole_mask(x, z, layer):
    holes = (
        (-38 + layer * 8, 18 - layer * 5, 10, 18),
        (7 - layer * 5, -4 + layer * 7, 8, 13),
        (41 - layer * 7, 29 - layer * 8, 11, 15),
    )
    for cx, cz, rx, rz in holes:
        if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 < 1.0:
            return True
    return False


def add_pleated_sheet(layer, material):
    columns = 56
    rows = 46
    width = 126.0
    height = 104.0
    vertices = []
    faces = []
    x_shift = (layer - 1.5) * 7.0
    y_shift = layer * 8.5

    for row in range(rows + 1):
        v = row / rows
        z = 58 - v * height
        for column in range(columns + 1):
            u = column / columns
            x = (u - 0.5) * width + x_shift
            sag = (1.0 - (2.0 * u - 1.0) ** 2) * (12 + layer * 1.5) * v
            pleat = math.sin(u * math.tau * (7 + layer)) * (5.8 - v * 2.0)
            cross_fold = math.sin(v * math.tau * 1.35 + u * 5.0 + layer) * 2.7
            y = y_shift + pleat + cross_fold + sag * 0.18
            bottom_fray = 0.0
            if v > 0.82:
                bottom_fray = (v - 0.82) * 18 * (0.45 + 0.55 * math.sin(u * 31 + layer) ** 2)
            vertices.append((x, y, z + sag - bottom_fray))

    stride = columns + 1
    for row in range(rows):
        for column in range(columns):
            u = (column + 0.5) / columns
            v = (row + 0.5) / rows
            x = (u - 0.5) * width + x_shift
            z = 58 - v * height
            if hole_mask(x, z, layer):
                continue
            a = row * stride + column
            faces.append((a, a + 1, a + stride + 1, a + stride))

    mesh = bpy.data.meshes.new(f"sepulture_membrane_mesh_{layer + 1}")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"sepulture_suspended_pleat_layer_{layer + 1}", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("printable_membrane_thickness", "SOLIDIFY")
    solidify.thickness = 1.15 + layer * 0.18
    solidify.offset = 0.0
    bevel = obj.modifiers.new("soft_torn_edges", "BEVEL")
    bevel.width = 0.42
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj


def add_clamp(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("rounded_clamp_edges", "BEVEL")
    bevel.width = 1.4
    bevel.segments = 4
    return obj


def setup_scene(objects):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.7
    scene.world = scene.world or bpy.data.worlds.new("World")
    scene.world.color = (0.003, 0.002, 0.004)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 16, 5))
    target = bpy.context.object
    bpy.ops.object.camera_add(location=(8, -238, 28))
    camera = bpy.context.object
    camera.data.lens = 58
    scene.camera = camera
    track = camera.constraints.new(type="TRACK_TO")
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    track.target = target

    bpy.ops.object.light_add(type="AREA", location=(-105, -90, 118))
    key = bpy.context.object
    key.data.energy = 5000
    key.data.color = (1.0, 0.53, 0.42)
    key.data.shape = "RECTANGLE"
    key.data.size = 130
    key.data.size_y = 190
    bpy.ops.object.light_add(type="AREA", location=(115, 20, 42))
    rim = bpy.context.object
    rim.data.energy = 3900
    rim.data.color = (0.50, 0.12, 0.26)
    rim.data.size = 110
    bpy.ops.object.light_add(type="POINT", location=(0, -55, -22))
    low = bpy.context.object
    low.data.energy = 900
    low.data.color = (0.48, 0.19, 0.08)
    low.data.shadow_soft_size = 60


def add_preview_backdrop():
    mat = make_material("sepulture_coal_backdrop", (0.004, 0.003, 0.005), 0.96)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 95, 5), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "sepulture_preview_coal_backdrop"
    backdrop.dimensions = (700, 450, 1)
    backdrop.data.materials.append(mat)


def export_assets(objects):
    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    try:
        bpy.ops.wm.stl_export(filepath=str(STL_PATH), export_selected_objects=True, apply_modifiers=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=str(STL_PATH), use_selection=True)
    bpy.ops.export_scene.gltf(filepath=str(GLB_PATH), export_format="GLB", use_selection=True, export_apply=True)


def render_outputs():
    RENDER_PATH.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.filepath = str(RENDER_PATH)
    scene.render.film_transparent = True
    bpy.ops.render.render(write_still=True)
    add_preview_backdrop()
    scene.render.filepath = str(PREVIEW_PATH)
    scene.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()
    smoke = make_material("smoked_plum_back_membrane", (0.13, 0.025, 0.07), 0.33, 0.2, 0.80)
    rose = make_material("clouded_rose_middle_membrane", (0.58, 0.16, 0.24), 0.25, 0.35, 0.72)
    flesh = make_material("pale_flesh_front_membrane", (0.82, 0.34, 0.36), 0.22, 0.28, 0.76)
    amber = make_material("dark_amber_inner_membrane", (0.36, 0.13, 0.055), 0.38, 0.18, 0.78)
    clamp_mat = make_material("violet_black_suspension_clamps", (0.028, 0.012, 0.025), 0.74)
    materials = (smoke, amber, rose, flesh)
    objects = [add_pleated_sheet(layer, materials[layer]) for layer in range(4)]
    objects.extend(
        [
            add_clamp("sepulture_left_suspension_clamp", (-48, 18, 64), (11, 4.5, 3.2), clamp_mat),
            add_clamp("sepulture_right_suspension_clamp", (50, 18, 64), (11, 4.5, 3.2), clamp_mat),
        ]
    )
    setup_scene(objects)
    export_assets(objects)
    render_outputs()
    print(f"Generated {STL_PATH}")
    print(f"Generated {GLB_PATH}")
    print(f"Generated {RENDER_PATH}")
    print(f"Generated {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
