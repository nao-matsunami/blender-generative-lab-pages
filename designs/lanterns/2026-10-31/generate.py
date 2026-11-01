"""Two parametric, printable lantern shade studies, built in Blender GUI.

Coordinates are millimetres. These are shade prototypes, not electrical assemblies.
"""

import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
TAU = 2 * math.pi
N = 320  # circumference samples
M = 168  # one-millimetre height samples
WALL = 2.8


def wrap(a):
    return (a + math.pi) % TAU - math.pi


def distance_to_segment(x, z, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)))
    return math.hypot(x - a[0] - t * dx, z - a[1] - t * dz)


def material(name, color, metallic=0, roughness=.75):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def tidal_radius(theta, z):
    h = 160
    u = z / h
    return (58 + 11 * math.sin(math.pi * u)
            + 7 * math.cos(5 * theta + 1.8 * u) * math.sin(math.pi * u) ** 2
            + 3 * math.sin(theta + .4) * math.sin(math.pi * u))


def tidal_solid(theta, z):
    q = (z - 24) / 112
    if q <= 0 or q >= 1:
        return True
    for k in range(10):
        opening = (.17 + .03 * math.sin(1.7 * k + .3)) * math.sin(math.pi * q) ** .82
        centre = TAU * k / 10 + .32 * (q - .5) + .09 * math.sin(2.1 * k)
        if abs(wrap(theta - centre)) < opening:
            return False
    return True


BRANCHES = [
    ((-1, 24), (-4, 75), 7.0),
    ((-4, 61), (-34, 100), 5.4),
    ((-5, 78), (-20, 126), 4.7),
    ((-1, 70), (34, 102), 5.7),
    ((2, 87), (22, 127), 4.8),
    ((-3, 47), (23, 69), 4.3),
]
LEAVES = [(-35, 103, 12, 9), (-20, 128, 11, 8), (35, 105, 13, 9),
          (23, 129, 11, 9), (25, 70, 10, 7)]


def orchard_radius(theta, z):
    u = z / 168
    return 67 + 5 * math.sin(math.pi * u) + 2.2 * math.cos(3 * theta + .8 * u) * math.sin(math.pi * u)


def orchard_solid(theta, z):
    q = (z - 24) / 120
    if q <= 0 or q >= 1:
        return True
    centre = -math.pi / 2 + .10 * (q - .5)
    half = .78 * math.sin(math.pi * q) ** .35
    d = wrap(theta - centre)
    if abs(d) >= half:
        return True
    x = 69 * d
    if x * x + (z - 78) ** 2 < 11 ** 2:
        return True
    for a, b, width in BRANCHES:
        if distance_to_segment(x, z, a, b) < width:
            return True
    for cx, cz, rx, rz in LEAVES:
        if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 < 1:
            return True
    return False


def build_shade(name, height, radius_fn, solid_fn, body_mat, inner_mat):
    # Every solid cell contributes its front and back. Exposed cell edges form
    # thickness walls, including the opening boundaries and both open rims.
    solid = [[solid_fn(TAU * (i + .5) / N, height * (j + .5) / M)
              for i in range(N)] for j in range(M)]
    # A diagonal cell contact would create a nonmanifold edge. Fill the tiny
    # checkerboard corner before deriving the printable surface.
    changed = True
    while changed:
        changed = False
        for j in range(M - 1):
            for i in range(N):
                k = (i + 1) % N
                a, b = solid[j][i], solid[j][k]
                c, d = solid[j + 1][i], solid[j + 1][k]
                if a == d and b == c and a != b:
                    if a:
                        solid[j][k] = True
                    else:
                        solid[j][i] = True
                    changed = True
    # Close one-cell pinholes at branch junctions; they would project bright dots.
    for j in range(1, M - 1):
        for i in range(N):
            if (not solid[j][i] and solid[j - 1][i] and solid[j + 1][i]
                    and solid[j][(i - 1) % N] and solid[j][(i + 1) % N]):
                solid[j][i] = True
    seen = set()
    for j in range(M):
        for i in range(N):
            if solid[j][i] or (j, i) in seen:
                continue
            group = [(j, i)]
            queue = deque(group)
            seen.add((j, i))
            while queue:
                row, col = queue.popleft()
                for nr, nc in ((row - 1, col), (row + 1, col),
                               (row, (col - 1) % N), (row, (col + 1) % N)):
                    if 0 <= nr < M and not solid[nr][nc] and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        group.append((nr, nc))
                        queue.append((nr, nc))
            if len(group) < 70:
                for row, col in group:
                    solid[row][col] = True

    boundary = defaultdict(set)

    def connect(a, b):
        boundary[a].add(b)
        boundary[b].add(a)

    for j in range(M):
        for i in range(N):
            if not solid[j][i]:
                continue
            k = (i + 1) % N
            if not solid[j][(i - 1) % N]:
                connect((j, i), (j + 1, i))
            if not solid[j][k]:
                connect((j, k), (j + 1, k))
            if j < M - 1 and not solid[j + 1][i]:
                connect((j + 1, i), (j + 1, k))
            if j > 0 and not solid[j - 1][i]:
                connect((j, i), (j, k))
    coords = {key: (TAU * key[1] / N, height * key[0] / M) for key in boundary}
    for _ in range(9):
        next_coords = {}
        for key, (theta, z) in coords.items():
            neighbors = boundary[key]
            if len(neighbors) != 2:
                next_coords[key] = (theta, z)
                continue
            theta_delta = sum(wrap(coords[n][0] - theta) for n in neighbors) / 2
            mean_z = sum(coords[n][1] for n in neighbors) / 2
            next_coords[key] = (theta + .47 * theta_delta, z + .47 * (mean_z - z))
        coords = next_coords

    vertices = []
    for side in (0, 1):
        for j in range(M + 1):
            for i in range(N):
                theta, z = coords.get((j, i), (TAU * i / N, height * j / M))
                r = radius_fn(theta, z) - WALL * side
                top_wave = (7 * (z / height) ** 3 * math.sin(2 * theta + .4)
                            if name == "tidal-pleat" else 0)
                vertices.append((r * math.cos(theta), r * math.sin(theta), z + top_wave))

    layer = (M + 1) * N

    def v(side, j, i):
        return layer * side + j * N + i % N

    faces, zones = [], []

    def add(face, zone):
        faces.append(face)
        zones.append(zone)

    for j in range(M):
        for i in range(N):
            if not solid[j][i]:
                continue
            k = (i + 1) % N
            a, b, c, d = v(0, j, i), v(0, j, k), v(0, j + 1, k), v(0, j + 1, i)
            e, f, g, h = v(1, j, i), v(1, j, k), v(1, j + 1, k), v(1, j + 1, i)
            add((a, b, c, d), 0)
            add((h, g, f, e), 1)
            if not solid[j][(i - 1) % N]:
                add((a, d, h, e), 2)
            if not solid[j][k]:
                add((c, b, f, g), 2)
            if j == M - 1 or not solid[j + 1][i]:
                add((d, c, g, h), 2)
            if j == 0 or not solid[j - 1][i]:
                add((b, a, e, f), 2)

    mesh = bpy.data.meshes.new(name + "_print_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (body_mat, inner_mat, body_mat):
        mesh.materials.append(mat)
    for polygon, zone in zip(mesh.polygons, zones):
        polygon.material_index = zone
        polygon.use_smooth = zone != 2
    return obj


def point_target(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene(name, height, camera_location, scale):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = .001
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.render.resolution_x, scene.render.resolution_y = 1200, 1400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 2.25
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (.025, .018, .022, 1)
    bg.inputs["Strength"].default_value = .7
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    point_target(camera, (0, 0, height * .52))
    scene.camera = camera
    for location, energy, color, size in (
        ((-145, -145, 235), 26000, (1, .84, .73), 120),
        ((150, -60, 100), 16000, (1, .64, .52), 90),
        ((0, 130, 200), 19000, (.89, .72, .80), 120),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.color, lamp.data.size = energy, color, size
    return scene


def add_led(location):
    bpy.ops.object.light_add(type="POINT", location=location)
    led = bpy.context.object
    led.name = "illustrative_warm_LED_point"
    led.data.energy = 45000
    led.data.color = (1, .58, .32)
    led.data.shadow_soft_size = .75
    return led


def export_and_render(name, obj, scene):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(OUT / (name + ".stl")), export_selected_objects=True,
                          apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + ".glb")), export_format="GLB",
                              use_selection=True, export_apply=True)
    scene.render.film_transparent = False
    scene.render.filepath = str(OUT / (name + "-preview.png"))
    bpy.ops.render.render(write_still=True)


def shadow_study(scene):
    # A white wall 220 mm from the shade tests whether the branch silhouette
    # survives an actual point-source projection. It is not part of the STL.
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, -220, 130))
    wall = bpy.context.object
    wall.name = "shadow_test_wall_not_for_print"
    wall.rotation_euler.x = -math.pi / 2
    wall.scale = (220, 170, 1)
    wall.data.materials.append(material("matte_wall", (.79, .72, .65), roughness=.95))
    # Remove bright area lights so the projected shadow remains visible.
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT" and obj.name != "illustrative_warm_LED_point":
            bpy.data.objects.remove(obj, do_unlink=True)
    camera = scene.camera
    camera.location = (0, -100, 155)
    camera.data.ortho_scale = 550
    point_target(camera, (0, -220, 145))
    scene.view_settings.exposure = 3.0
    scene.render.resolution_x, scene.render.resolution_y = 1500, 1100
    scene.render.filepath = str(OUT / "night-orchard-shadow-study.png")
    bpy.ops.render.render(write_still=True)


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reset()
    pale = material("warm_chalk_ceramic", (.79, .67, .54), roughness=.82)
    deep = material("inner_ochre", (.39, .25, .20), roughness=.87)
    tidal = build_shade("tidal-pleat", 160, tidal_radius, tidal_solid, pale, deep)
    scene = setup_scene("tidal-pleat", 160, (235, -260, 195), 255)
    add_led((0, 0, 58))
    export_and_render("tidal-pleat", tidal, scene)

    reset()
    plum = material("opaque_plum_ceramic", (.43, .29, .37), roughness=.84)
    inner = material("inner_dark_umber", (.16, .11, .14), roughness=.9)
    orchard = build_shade("night-orchard", 168, orchard_radius, orchard_solid, plum, inner)
    scene = setup_scene("night-orchard", 168, (125, -285, 190), 255)
    add_led((0, 40, 55))
    export_and_render("night-orchard", orchard, scene)
    shadow_study(scene)


if __name__ == "__main__":
    main()
