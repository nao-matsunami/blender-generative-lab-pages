"""Interference Basin: connected nested screens for a removable LED core (mm)."""

import math
import os
import runpy
from collections import defaultdict
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / "designs/lanterns/2026-10-31/generate.py"), run_name="shade_mesh_library")
SLUG = "interference-basin"
HEIGHT = 160.0
WALL = 2.8
N, M = 224, 160
BASE_HEIGHT = 7  # solid annular footing; the nested gap starts above this layer
TAU = 2 * math.pi
REVISION = int(os.environ.get("BASIN_REVISION", "0"))


def wrap(angle):
    return (angle + math.pi) % TAU - math.pi


def outer_radius(theta, z):
    u = z / HEIGHT
    return (67 + 16 * u + 5.0 * math.sin(2 * theta + .8 * u) * math.sin(math.pi * u) ** 2
            + 3 * u * math.cos(theta - .8))


def inner_radius(theta, z):
    u = z / HEIGHT
    return 53 + 7 * u + 2 * math.sin(3 * theta + u) * math.sin(math.pi * u) ** 2


def outer_solid(theta, z):
    if z < 22 or z > 146:
        return True
    for row, (low, high) in enumerate(((29, 55), (68, 96), (108, 137))):
        if low < z < high:
            for k in range(7):
                center = TAU * (k + (.34 if REVISION else .17) * row) / 7 + .085 * math.sin(1.8 * k + row)
                t = (z - low) / (high - low)
                width = ((.10 + .18 * math.sin(math.pi * t) ** .8) if REVISION else .235)
                width += .025 * math.sin(2.1 * k + .7 * row)
                # Every opening inclines within its row; no diagonal bars cross.
                center += (.22 if REVISION else .06) * t
                if abs(wrap(theta - center)) < width:
                    return False
    return True


def inner_solid(theta, z):
    if z < 19 or z > 148:
        return True
    for row, (low, high) in enumerate(((25, 46), (56, 78), (89, 112), (123, 143))):
        if low < z < high:
            for k in range(5):
                center = TAU * (k + .32 * row + .13) / 5
                center += .10 * math.sin(k * 1.7 + row)
                if abs(wrap(theta - center)) < .43:
                    return False
    return True


def make_mesh(outer_mat, inner_mat, cut_mat):
    # Four radial sheets: exterior, its back, interior-screen front, and its back.
    # The three strips across z=0 fuse them into one open-bottom printable body.
    def radius(layer, theta, z):
        if layer < 2:
            return outer_radius(theta, z) - WALL * layer
        return inner_radius(theta, z) - WALL * (layer - 2)

    masks = []
    for mask_fn in (outer_solid, inner_solid):
        masks.append([[mask_fn(TAU * (i + .5) / N, HEIGHT * (j + .5) / M)
                       for i in range(N)] for j in range(M)])

    # Relax only aperture perimeters, eliminating one-cell stair steps without
    # softening the load-bearing wall or changing the opening topology.
    boundary_coords = []
    for solid in masks:
        neighbors = defaultdict(set)

        def connect(a, b):
            neighbors[a].add(b)
            neighbors[b].add(a)

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
        coords = {key: (TAU * key[1] / N, HEIGHT * key[0] / M) for key in neighbors}
        for _ in range(10):
            relaxed = {}
            for key, (theta, z) in coords.items():
                adjacent = neighbors[key]
                if len(adjacent) != 2:
                    relaxed[key] = (theta, z)
                    continue
                delta = sum(wrap(coords[n][0] - theta) for n in adjacent) / 2
                mean_z = sum(coords[n][1] for n in adjacent) / 2
                relaxed[key] = (theta + .47 * delta, z + .47 * (mean_z - z))
            coords = relaxed
        boundary_coords.append(coords)

    vertices = []
    for layer in range(4):
        for j in range(M + 1):
            z = HEIGHT * j / M
            for i in range(N):
                theta = TAU * i / N
                angle, height = boundary_coords[layer // 2].get((j, i), (theta, z))
                r = radius(layer, angle, height)
                vertices.append((r * math.cos(angle), r * math.sin(angle), height))

    def v(layer, j, i):
        return layer * (M + 1) * N + j * N + (i % N)

    faces, zones = [], []

    def add(face, zone):
        faces.append(face)
        zones.append(zone)

    for screen, solid in enumerate(masks):
        front, back = 2 * screen, 2 * screen + 1
        face_zone = screen
        for j in range(M):
            for i in range(N):
                if not solid[j][i]:
                    continue
                k = (i + 1) % N
                a, b, c, d = v(front, j, i), v(front, j, k), v(front, j + 1, k), v(front, j + 1, i)
                e, f, g, h = v(back, j, i), v(back, j, k), v(back, j + 1, k), v(back, j + 1, i)
                if screen == 0 or j >= BASE_HEIGHT:
                    add((a, b, c, d), face_zone)
                if screen == 1 or j >= BASE_HEIGHT:
                    add((h, g, f, e), face_zone)
                if not solid[j][(i - 1) % N]:
                    add((a, d, h, e), 2)
                if not solid[j][k]:
                    add((c, b, f, g), 2)
                if j < M - 1 and not solid[j + 1][i]:
                    add((d, c, g, h), 2)
                if j > 0 and not solid[j - 1][i]:
                    add((b, a, e, f), 2)
                if j == M - 1:
                    add((d, c, g, h), 2)
    # Full-width annular footing, assembled from shared vertex loops.
    for i in range(N):
        k = (i + 1) % N
        for outer, inner in ((0, 1), (1, 2), (2, 3)):
            add((v(outer, 0, k), v(outer, 0, i), v(inner, 0, i), v(inner, 0, k)), 2)
        add((v(1, BASE_HEIGHT, i), v(1, BASE_HEIGHT, k),
             v(2, BASE_HEIGHT, k), v(2, BASE_HEIGHT, i)), 2)

    mesh = bpy.data.meshes.new(SLUG + "_connected_screen_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(SLUG, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (outer_mat, inner_mat, cut_mat):
        mesh.materials.append(mat)
    for polygon, zone in zip(mesh.polygons, zones):
        polygon.material_index = zone
        polygon.use_smooth = zone != 2
    # Loose vertices under apertures are removed from the export and saved scene.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.delete(bm, geom=[vert for vert in bm.verts if not vert.link_faces], context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


def export(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=str(ROOT / "exports/stl" / (SLUG + ".stl")),
                          export_selected_objects=True, apply_modifiers=True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT / "exports/glb" / (SLUG + ".glb")),
                              export_format="GLB", use_selection=True, export_apply=True)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    outer = LIB["material"]("ivory_ceramic_screen", (.65, .68, .65) if not REVISION else (.71, .70, .64), roughness=.74)
    inner = LIB["material"]("warm_aluminium_inner_screen", (.54, .51, .42), metallic=.22, roughness=.65)
    cut = LIB["material"]("cut_edges", (.37, .38, .34), roughness=.87)
    shade = make_mesh(outer, inner, cut)
    scene = LIB["setup_scene"](SLUG, HEIGHT, (290, -280, 195) if not REVISION else (350, -185, 245),
                                280 if not REVISION else 270)
    scene.cycles.samples = 20
    scene.render.resolution_x, scene.render.resolution_y = 960, 1080
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.020, .022, .021, 1)
    scene.view_settings.exposure = 2.5 if not REVISION else 2.7
    bpy.ops.object.light_add(type="AREA", location=(170, -220, 160))
    fill = bpy.context.object
    fill.data.energy = 75000 if not REVISION else 110000
    fill.data.size = 180
    fill.data.color = (1.0, .97, .86)
    LIB["add_led"]((0, 0, 56))
    if REVISION:
        export(shade)
    scene.render.film_transparent = False
    scene.render.filepath = str(ROOT / "renders" / (SLUG + ("-preview.png" if REVISION else "-initial-preview.png")))
    bpy.ops.render.render(write_still=True)
    if REVISION:
        scene.render.film_transparent = True
        scene.render.filepath = str(ROOT / "renders" / (SLUG + ".png"))
        bpy.ops.render.render(write_still=True)
        target = ROOT / "designs/lanterns/2026-11-06" / (SLUG + ".blend")
        target.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))


if __name__ == "__main__":
    main()
