"""Folded Meridian Lantern: six straight, folded piers around unequal vertical voids."""
import math, os, runpy
from pathlib import Path
import bpy, bmesh

ROOT=Path(__file__).resolve().parents[1]
LIB=runpy.run_path(str(ROOT/'designs/lanterns/2026-10-31/generate.py'),run_name='shade_mesh_library')
SLUG='folded-meridian-lantern'
REV=int(os.environ.get('MERIDIAN_REVISION','0'))
H,N,M,T=160.0,360 if REV else 180,300 if REV else 140,4.2
TAU=2*math.pi
def wrap(x):return (x+math.pi)%TAU-math.pi
def radius(a,z):
    u=z/H
    sector=wrap(a-0.18+math.pi/6)%(math.pi/3)-math.pi/6
    apothem=60+10*math.sin(math.pi*u)+7*u
    fold=apothem/math.cos(sector)
    return fold+2.5*math.cos(6*a+0.4)*math.sin(math.pi*u)**2
def solid(a,z):
    if z<24 or z>H-19:return True
    u=(z-24)/(H-43)
    # Six uncrossed folded meridians. Their intervals vary to make a nonrepeating profile.
    for k in range(6):
        c=TAU*k/6+0.18+0.06*math.sin(k*1.7)
        width=(0.24 if REV else 0.19)+0.025*math.sin(k*1.9)
        # Constant angular section keeps each junction clean in the printed mesh.
        if abs(wrap(a-c))<width:return True
    return False
def make_object(face,edge):
    verts=[];faces=[];zones=[]
    for side in (0,1):
        for j in range(M+1):
            z=H*j/M
            for i in range(N):
                a=TAU*i/N;r=radius(a,z)-T*side
                verts.append((r*math.cos(a),r*math.sin(a),z))
    def v(s,j,i):return s*(M+1)*N+j*N+i%N
    mask=[[solid(TAU*(i+.5)/N,H*(j+.5)/M) for i in range(N)]for j in range(M)]
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
    face=LIB['material']('warm_limestone',(.73,.70,.62) if REV else (.50,.50,.47),roughness=.78)
    edge=LIB['material']('fold_section',(.39,.37,.32),roughness=.83)
    shade=make_object(face,edge)
    scene=LIB['setup_scene'](SLUG,H,(350,-180,205) if REV else (300,-300,255),260)
    scene.cycles.samples=16;scene.render.resolution_x=1080;scene.render.resolution_y=960
    scene.render.film_transparent=False;scene.view_settings.exposure=2.4 if REV else 1.9
    bpy.ops.object.light_add(type='AREA',location=(190,-170,190))
    bpy.context.object.data.energy=100000;bpy.context.object.data.size=190
    LIB['add_led']((0,0,58))
    scene.render.filepath=str(ROOT/'renders'/(SLUG+('-preview.png' if REV else '-initial-preview.png')))
    bpy.ops.render.render(write_still=True)
    if REV:
        bpy.ops.object.select_all(action='DESELECT');shade.select_set(True);bpy.context.view_layer.objects.active=shade
        bpy.ops.wm.stl_export(filepath=str(ROOT/'exports/stl'/(SLUG+'.stl')),export_selected_objects=True,apply_modifiers=True)
        mod=shade.modifiers.new('Web decimation','DECIMATE');mod.ratio=.45
        bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/glb'/(SLUG+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
        shade.modifiers.remove(mod)
        scene.render.film_transparent=True;scene.render.filepath=str(ROOT/'renders'/(SLUG+'.png'))
        bpy.ops.render.render(write_still=True)
        target=ROOT/'designs/lanterns/2026-11-24'/(SLUG+'.blend');target.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
if __name__=='__main__':main()
