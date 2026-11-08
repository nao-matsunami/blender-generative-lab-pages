"""Orbit Terrace Lantern: annular terraces joined by offset broad piers."""
import math
import os
import runpy
from pathlib import Path

import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[1]
LIB = runpy.run_path(str(ROOT / 'designs/lanterns/2026-10-31/generate.py'), run_name='shade_mesh_library')
SLUG = 'orbit-terrace-lantern'
H, N, M, T = 166.0, 180, 132, 3.2
REV = int(os.environ.get('TERRACE_REVISION', '0'))


def radius(theta, z):
    u = z / H
    # Broad stepped terraces grow from a planted foot, with a shifted upper axis.
    tier = min(4, int(u * 5))
    shoulder = (0, 7, 16, 11, 4)[tier]
    r = 64 + shoulder + 4 * math.cos(2 * theta + 1.4 * u)
    r += (5 if REV else 2) * u * math.cos(theta - .85)
    return r


def solid(theta, z):
    if z < 19 or z > 151:
        return True
    # Five annular shadow gaps, each crossed by three broad alternating piers.
    for band in range(5):
        mid = 31 + 28 * band
        if abs(z - mid) < (5.5 if REV else 4.5):
            for k in range(3):
                center = 2 * math.pi * k / 3 + .31 * band
                gap = abs((theta - center + math.pi) % (2 * math.pi) - math.pi)
                if gap < (.20 if REV else .16):
                    return True
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
    face=LIB['material']('satin_chalk',(.53,.55,.55) if not REV else (.70,.68,.59),roughness=.67)
    edge=LIB['material']('fold_edges',(.32,.33,.30),roughness=.8)
    shade=make_object(face,edge)
    scene=LIB['setup_scene'](SLUG,H,(320,-290,225) if not REV else (335,-265,245),265 if not REV else 255)
    scene.cycles.samples=20
    scene.render.resolution_x=960; scene.render.resolution_y=1080
    scene.view_settings.exposure=2.5 if not REV else 2.7
    bpy.ops.object.light_add(type='AREA',location=(170,-210,185))
    bpy.context.object.data.energy=85000 if not REV else 100000
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
        target=ROOT/'designs/lanterns/2026-11-08'/(SLUG+'.blend')
        target.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))

if __name__=='__main__': main()
