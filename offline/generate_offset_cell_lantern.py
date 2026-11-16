"""Offset Cell Lantern: staggered polygonal windows on an asymmetric shell."""
import math, os, runpy
from pathlib import Path
import bpy, bmesh

ROOT=Path(__file__).resolve().parents[1]
LIB=runpy.run_path(str(ROOT/'designs/lanterns/2026-10-31/generate.py'),run_name='shade_mesh_library')
SLUG='offset-cell-lantern'
REV=int(os.environ.get('CELL_REVISION','0'))
H,N,M,T=158.0,960 if REV else 480,480 if REV else 240,4.0

def radius(a,z):
    u=z/H
    return 75+12*math.sin(math.pi*u)+(13 if REV else 7)*math.cos(3*a+0.7*u)*math.sin(math.pi*u)-5*u

def solid(a,z):
    if z<20 or z>140:return True
    for row,(zc,count,phase) in enumerate(((51,6,0.0),(108,6,math.pi/6))):
        for k in range(count):
            center=2*math.pi*k/count+phase+0.08*math.sin(z/H*math.pi)
            d=abs((a-center+math.pi)%(2*math.pi)-math.pi)
            dz=abs(z-zc)
            # Staggered chamfered cell: wide centre, tapered roof and sill.
            halfwidth=(.30 if REV else .27)*min(1,max(0,(25-dz)/(14 if REV else 7)))
            if dz<25 and d<halfwidth:return False
    return True

def make_object(face,edge):
    verts=[];faces=[];zones=[]
    for side in (0,1):
        for j in range(M+1):
            z=H*j/M
            for i in range(N):
                a=2*math.pi*i/N;r=radius(a,z)-T*side
                verts.append((r*math.cos(a),r*math.sin(a),z))
    def v(s,j,i):return s*(M+1)*N+j*N+i%N
    mask=[[solid(2*math.pi*(i+.5)/N,H*(j+.5)/M) for i in range(N)]for j in range(M)]
    def add(f,zone):faces.append(f);zones.append(zone)
    for j in range(M):
        for i in range(N):
            if not mask[j][i]:continue
            k=(i+1)%N
            a,b,c,d=v(0,j,i),v(0,j,k),v(0,j+1,k),v(0,j+1,i)
            e,f,g,h=v(1,j,i),v(1,j,k),v(1,j+1,k),v(1,j+1,i)
            add((a,b,c,d),0);add((h,g,f,e),0)
            if not mask[j][(i-1)%N]:add((a,d,h,e),1)
            if not mask[j][k]:add((c,b,f,g),1)
            if j==0 or not mask[j-1][i]:add((b,a,e,f),1)
            if j==M-1 or not mask[j+1][i]:add((d,c,g,h),1)
    mesh=bpy.data.meshes.new(SLUG+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(SLUG,mesh);bpy.context.collection.objects.link(ob)
    mesh.materials.append(face);mesh.materials.append(edge)
    for p,z in zip(mesh.polygons,zones):p.material_index=z;p.use_smooth=False
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.delete(bm,geom=[p for p in bm.verts if not p.link_faces],context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free();mesh.update()
    return ob

def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
    if bpy.context.scene.world is None:bpy.context.scene.world=bpy.data.worlds.new('World')
    face=LIB['material']('chalk_ceramic',(.78,.79,.75) if REV else (.64,.66,.63),roughness=.76)
    edge=LIB['material']('cut_faces',(.42,.44,.40),roughness=.8)
    shade=make_object(face,edge)
    scene=LIB['setup_scene'](SLUG,H,(300,-330,225) if REV else (300,-360,200),255)
    scene.cycles.samples=20;scene.render.resolution_x=1080;scene.render.resolution_y=960
    scene.render.film_transparent=False
    scene.view_settings.exposure=2.4 if REV else 2.2
    bpy.ops.object.light_add(type='AREA',location=(170,-210,185))
    bpy.context.object.data.energy=115000;bpy.context.object.data.size=190
    LIB['add_led']((0,0,58))
    scene.render.filepath=str(ROOT/'renders'/(SLUG+('-preview.png' if REV else '-initial-preview.png')))
    bpy.ops.render.render(write_still=True)
    if REV:
        bpy.ops.object.select_all(action='DESELECT');shade.select_set(True);bpy.context.view_layer.objects.active=shade
        bpy.ops.wm.stl_export(filepath=str(ROOT/'exports/stl'/(SLUG+'.stl')),export_selected_objects=True,apply_modifiers=True)
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/glb'/(SLUG+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
        scene.render.film_transparent=True;scene.render.filepath=str(ROOT/'renders'/(SLUG+'.png'))
        bpy.ops.render.render(write_still=True)
        target=ROOT/'designs/lanterns/2026-11-16'/(SLUG+'.blend');target.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
if __name__=='__main__':main()
