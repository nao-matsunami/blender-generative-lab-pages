"""Split Delta Lantern: alternating broad triangular voids in a low faceted vessel."""
import math, os, runpy
from pathlib import Path
import bpy, bmesh

ROOT=Path(__file__).resolve().parents[1]
LIB=runpy.run_path(str(ROOT/'designs/lanterns/2026-10-31/generate.py'),run_name='shade_mesh_library')
SLUG='split-delta-lantern'
REV=int(os.environ.get('DELTA_REVISION','0'))
H,N,M,T=136.0,480 if REV else 160,408 if REV else 136,4.2
TAU=2*math.pi
def wrap(x):return (x+math.pi)%TAU-math.pi
def radius(a,z):
    u=z/H
    sector=wrap(a+math.pi/8)%(math.pi/4)-math.pi/8
    apothem=69+8*math.sin(math.pi*u)-8*u
    return apothem/math.cos(sector)
def solid(a,z):
    if z<25 or z>H-20:return True
    # Four alternating delta voids: two rise, two descend. Wide uninterrupted
    # webs remain between each sector rather than becoming a diagrid.
    for k in range(4):
        center=TAU*k/4+0.11
        u=(z-25)/(H-45)
        extent=(0.07+0.48*u) if k%2==0 else (0.07+0.48*(1-u))
        if abs(wrap(a-center))<extent:return False
    return True
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
    face=LIB['material']('ivory_ceramic',(.70,.72,.69) if REV else (.45,.47,.47),roughness=.76)
    edge=LIB['material']('cut_section',(.30,.34,.33),roughness=.83)
    shade=make_object(face,edge)
    scene=LIB['setup_scene'](SLUG,H,(350,-160,185) if REV else (300,-300,240),235)
    scene.cycles.samples=16;scene.render.resolution_x=1080;scene.render.resolution_y=960
    scene.render.film_transparent=False;scene.view_settings.exposure=2.3 if REV else 1.8
    bpy.ops.object.light_add(type='AREA',location=(190,-170,190))
    bpy.context.object.data.energy=100000;bpy.context.object.data.size=190
    LIB['add_led']((0,0,55))
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
        target=ROOT/'designs/lanterns/2026-11-25'/(SLUG+'.blend');target.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
if __name__=='__main__':main()
