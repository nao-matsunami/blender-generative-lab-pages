"""Pleat Drift Shade: one folded, open-ended shade in millimetres."""
import math
import os
import runpy
from pathlib import Path

import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / 'designs/lanterns/2026-10-31/generate.py'), run_name='shade_mesh_library')
SLUG = 'pleat-drift-shade'
H, N, M, T = 174.0, 168, 116, 3.0
REV = int(os.environ.get('PLEAT_REVISION', '0'))


def radius(theta, z):
    u = z / H
    # Twelve broad triangular folds drift in phase; a two-lobed envelope leans
    # the top away from the foot, making the silhouette asymmetric.
    phase = theta * 12 / (2 * math.pi) - .48 * u
    tri = 1 - 4 * abs((phase % 1) - .5)
    return 65 + 24 * u + 14 * tri * math.sin(math.pi * (.14 + .72 * u)) + 9.0 * u * math.cos(theta - .7)


def solid(theta, z):
    if z < 18 or z > 160:
        return True
    # Separated vertical reveals between folds; their stagger and changing
    # height create an irregular light rhythm without crossing diagonal bars.
    for k in range(0, 12, 2):
        center = 2 * math.pi * k / 12
        gap = abs((theta - center + math.pi) % (2 * math.pi) - math.pi)
        low = 25 + (k % 3) * 11
        high = 149 - ((2 * k) % 4) * 8
        if low < z < high and gap < (.11 if REV else .052):
            return False
    return True


def make_object(mat, edge):
    verts, faces, zones = [], [], []
    for side in (0, 1):
        for j in range(M + 1):
            z = H * j / M
            for i in range(N):
                a = 2 * math.pi * i / N
                r = radius(a, z) - T * side
                verts.append((r * math.cos(a), r * math.sin(a), z))

    def v(side, j, i):
        return side * (M + 1) * N + j * N + i % N

    mask = [[solid(2 * math.pi * (i + .5) / N, H * (j + .5) / M) for i in range(N)] for j in range(M)]

    def add(face, zone):
        faces.append(face)
        zones.append(zone)

    for j in range(M):
        for i in range(N):
            if not mask[j][i]:
                continue
            k = (i + 1) % N
            a, b, c, d = v(0,j,i),v(0,j,k),v(0,j+1,k),v(0,j+1,i)
            e, f, g, h = v(1,j,i),v(1,j,k),v(1,j+1,k),v(1,j+1,i)
            add((a,b,c,d),0)
            add((h,g,f,e),0)
            if not mask[j][(i-1)%N]: add((a,d,h,e),1)
            if not mask[j][k]: add((c,b,f,g),1)
            if j == 0 or not mask[j-1][i]: add((b,a,e,f),1)
            if j == M-1 or not mask[j+1][i]: add((d,c,g,h),1)
    mesh = bpy.data.meshes.new(SLUG+'_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(SLUG,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(mat); mesh.materials.append(edge)
    for poly,zone in zip(mesh.polygons,zones):
        poly.material_index=zone
        poly.use_smooth=False
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.delete(bm,geom=[p for p in bm.verts if not p.link_faces],context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    return ob


def main():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    face=LIB['material']('satin_chalk',(.58,.61,.58) if not REV else (.70,.71,.65),roughness=.67)
    edge=LIB['material']('fold_edges',(.31,.33,.32),roughness=.8)
    shade=make_object(face,edge)
    scene=LIB['setup_scene'](SLUG,H,(310,-280,215) if not REV else (340,-240,240),275 if not REV else 265)
    scene.cycles.samples=20
    scene.render.resolution_x=960; scene.render.resolution_y=1080
    scene.view_settings.exposure=2.6 if not REV else 2.8
    bpy.ops.object.light_add(type='AREA',location=(170,-210,185))
    bpy.context.object.data.energy=85000 if not REV else 105000
    bpy.context.object.data.size=190
    LIB['add_led']((0,0,55))
    scene.render.filepath=str(ROOT/'renders'/(SLUG+('-preview.png' if REV else '-initial-preview.png')))
    bpy.ops.render.render(write_still=True)
    if REV:
        bpy.ops.object.select_all(action='DESELECT');shade.select_set(True);bpy.context.view_layer.objects.active=shade
        bpy.ops.wm.stl_export(filepath=str(ROOT/'exports/stl'/(SLUG+'.stl')),export_selected_objects=True,apply_modifiers=True)
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/glb'/(SLUG+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
        scene.render.film_transparent=True
        scene.render.filepath=str(ROOT/'renders'/(SLUG+'.png'))
        bpy.ops.render.render(write_still=True)
        target=ROOT/'designs/lanterns/2026-11-07'/(SLUG+'.blend')
        target.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))

if __name__=='__main__': main()
