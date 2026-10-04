"""Robust native solid construction for the eight cage pieces.
The shared dimensions/features come from build.frame_geometry; curved primitives
are faceted to less than 0.05 mm chord error before booleans.
"""
from pathlib import Path
import math,json,argparse
import numpy as np
import manifold3d as mf
import trimesh
import build as b

def cylinder(r,a,z):
 a=np.array(a,dtype=float);z=np.array(z,dtype=float);d=z-a;L=np.linalg.norm(d);normal=d/L
 ref=np.array([0.,0.,1.]) if abs(normal[2])<.95 else np.array([0.,1.,0.]);ex=np.cross(ref,normal);ex/=np.linalg.norm(ex);ey=np.cross(normal,ex)
 segments=max(20,int(math.ceil(math.pi/math.acos(max(-1,1-.025/r)))))
 return mf.Manifold.cylinder(float(L),float(r),circular_segments=segments).transform(np.column_stack([ex,ey,normal,a]))
def sphere(r,p):return mf.Manifold.sphere(r,16).translate(p)
def transformed(s,t):return s.transform(np.column_stack([t['ex'],t['ey'],t['normal'],t['center']]))
def hexprism(flat,z,h,x=0,y=0):return mf.CrossSection.circle(flat/2/math.cos(math.pi/6),6).extrude(h).translate([x,y,z])
def radial_slot(a,z):
 a=np.array(a);z=np.array(z);d=z-a
 return mf.Manifold.cube([float(np.linalg.norm(d)),12,.5],center=True).rotate([0,0,math.degrees(math.atan2(d[1],d[0]))]).translate((a+z)/2)

def mesh_of(s):
 raw=s.to_mesh64();points=np.asarray(raw.vert_properties)[:,:3];f=np.asarray(raw.tri_verts);p=np.arange(len(points))
 for a,z in zip(raw.merge_from_vert,raw.merge_to_vert):p[a]=z
 while np.any(p[p]!=p):p=p[p]
 m=trimesh.Trimesh(vertices=points,faces=p[f],process=False);m.remove_unreferenced_vertices();return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--octant',type=int);a=p.parse_args()
 for name in ['cylinder','sphere','transformed','hexprism','radial_slot']:setattr(b,name,globals()[name])
 parts,cuts,joints,major=b.frame_geometry();reports=[]
 (b.OUT/'joints.json').write_text(json.dumps(joints,indent=2))
 for i in ([a.octant] if a.octant is not None else range(8)):
  signs=np.array([1 if i&(1<<k) else -1 for k in range(3)]);origin=np.where(signs>0,.025,-170)
  selected=[]
  for shape in parts:
   bb=np.array(shape.bounding_box());lo=bb[:3];hi=bb[3:]
   if np.any((signs>0)&(hi<0)) or np.any((signs<0)&(lo>0)):continue
   selected.append(shape)
  print('Native octant',i,'operands',len(selected),flush=True)
  s=mf.Manifold.batch_boolean(selected,mf.OpType.Add)^mf.Manifold.cube([169.975]*3).translate(origin)
  relevant=[]
  for cut in cuts:
   bb=np.array(cut.bounding_box());lo=bb[:3];hi=bb[3:]
   if np.any((signs>0)&(hi<0)) or np.any((signs<0)&(lo>0)):continue
   relevant.append(cut)
  s=s-mf.Manifold.batch_boolean(relevant,mf.OpType.Add);s=s.as_original().simplify(.005)
  components=s.decompose();specks=sum(abs(c.volume()) for c in components if abs(c.volume())<1e-4)
  # A post immediately beside a split can leave a sub-0.6 mm crescent on the
  # opposite octant. Relieve that unsupported skin; retain the complete post
  # on its owning octant. Any larger or non-seam disconnected part is an error.
  relief=[];kept=[]
  for c in components:
   volume=abs(c.volume());bb=np.array(c.bounding_box());extent=bb[3:]-bb[:3]
   at_seam=any(extent[k]<.6 and min(abs(bb[k]),abs(bb[k+3]))<.026 for k in range(3))
   if volume<1e-4:continue
   if volume<5 and at_seam:relief.append({'volume_mm3':volume,'bounds':bb.tolist()})
   else:kept.append(c)
  s=mf.Manifold.batch_boolean(kept,mf.OpType.Add)
  m=mesh_of(s)
  for piece in s.decompose():
   if piece.volume()<10:print('Small component',piece.volume(),piece.bounding_box(),flush=True)
  print('Boundary',s.status(),m.is_watertight,m.is_winding_consistent,'volume',m.volume,'triangles',len(m.faces),'pieces',[round(c.volume,3) for c in m.split(only_watertight=False)],flush=True)
  if not m.is_watertight or not m.is_winding_consistent or len(m.split())!=1:raise ValueError('Invalid native cage')
  target=b.OUT/f'cage-octant-{i+1:02}.stl';m.export(target);r=trimesh.load_mesh(target)
  # STL stores 32-bit coordinates. Weld duplicate vertices and remove the zero-area
  # triangles that quantization collapses; require closure and volume preservation.
  r.merge_vertices(digits_vertex=6);r.update_faces(r.nondegenerate_faces(height=1e-7));r.update_faces(r.unique_faces());r.remove_unreferenced_vertices()
  if abs(r.volume-m.volume)/m.volume>1e-5:raise ValueError('STL cleanup altered volume')
  r.export(target);r=trimesh.load_mesh(target)
  print('Export/reimport closed',r.is_watertight,r.is_winding_consistent,'volume',r.volume,flush=True)
  if not r.is_watertight or not r.is_winding_consistent:raise ValueError('STL round trip failed')
  reports.append({'part':target.stem,'material':'PA12','volume_mm3':r.volume,'triangles':len(r.faces),'bounds_mm':r.extents.tolist(),'watertight':True,'connected_solids':1,'numerical_specks_removed_mm3':specks,'split_skin_relief':relief,'joint_gap_mm':.05,'step_status':'pending boundary conversion'})
  np.savez(b.OUT/(target.stem+'.npz'),vertices=r.vertices,faces=r.faces)
 (b.OUT/('cad-audit-frame'+('' if a.octant is None else '-'+str(a.octant))+'.json')).write_text(json.dumps(reports,indent=2))
if __name__=='__main__':main()
