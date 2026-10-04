"""Closed terrain, optical cells, and removable shell fittings. Millimetres."""
from pathlib import Path
import json,math,argparse
import numpy as np
import manifold3d as mf
import trimesh
from scipy.ndimage import map_coordinates
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'cad/generated'
D=json.loads((OUT/'layout.json').read_text());R=D['requirements'];N=np.array(D['nodes'])
T=json.loads((OUT/'terrain.json').read_text());H=np.array(T['heights_mm']).reshape(T['height'],T['width'])
AUDIT=[]

def tm(manifold):
 mesh=manifold.to_mesh();return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:,:3],faces=np.asarray(mesh.tri_verts),process=True)
def manifold(mesh):return mf.Manifold(mf.Mesh(vert_properties=np.asarray(mesh.vertices,dtype=np.float32),tri_verts=np.asarray(mesh.faces,dtype=np.uint32)))
def write(name,m,material):
 mesh=tm(m) if isinstance(m,mf.Manifold) else m
 if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume<=0:raise ValueError(name+' not a closed, correctly oriented solid')
 body_count=len(mesh.split(only_watertight=False))
 if body_count!=1:raise ValueError(f'{name} has {body_count} disconnected bodies')
 mesh.export(OUT/(name+'.stl'))
 AUDIT.append({'part':name,'material':material,'triangles':len(mesh.faces),'volume_mm3':float(mesh.volume),'bounds_mm':mesh.extents.tolist(),'watertight':True,'connected_solids':body_count})
 print(name,len(mesh.faces),round(mesh.volume),flush=True)
 return mesh

def xform(t):return np.column_stack([t['ex'],t['ey'],t['normal'],t['center']])
def local_point(t,x,y,z):return np.array(t['center'])+np.array(t['ex'])*x+np.array(t['ey'])*y+np.array(t['normal'])*z

def baffles():
 reps={}
 for t in D['tiles']:reps.setdefault(t['type'],t)
 for typ,t in reps.items():
  section=mf.CrossSection([np.array(t['outline'])])
  for p in t['leds']:
   x,y=p['x'],p['y'];s=R['led_pitch_mm']-R['baffle_wall_mm']
   section=section-mf.CrossSection.square([s,s],center=True).translate([x,y])
  # Mounting apertures clear the PCB screws and removable magnet seats.
  for x,y in t['holes']:section=section-mf.CrossSection.circle(3.5,32).translate([x,y])
  section=section.offset(-.06).offset(.06) # remove zero-width slivers at triangle edges
  components=sorted(section.decompose(),key=lambda c:c.area(),reverse=True)
  scrap=sum(c.area() for c in components[1:]);print('mount-corner scraps removed, mm2',typ,scrap,flush=True)
  if scrap>12:raise ValueError('Unexpected disconnected functional grid')
  section=components[0]
  shape=section.extrude(1)
  c=np.array(t['center']);ex=np.array(t['ex']);ey=np.array(t['ey']);n=np.array(t['normal']);d=c@n
  def warp(p):
   x,y,z=p;w=c+x*ex+y*ey+n*.10;top=w/np.linalg.norm(w)*(R['shell_inner_radius_mm']-R['baffle_top_clearance_mm']);rel=top-c
   target=np.array([rel@ex,rel@ey,rel@n]);base=np.array([x,y,.10]);return (base+z*(target-base)).tolist()
  shape=shape.warp(warp)
  # Cell walls fan radially toward the shell; vertical mounting seats need their own clearance.
  for x,y in t['holes']:shape=shape-mf.Manifold.cylinder(20,3.5,circular_segments=40).translate([x,y,0])
  pieces=sorted(shape.decompose(),key=lambda p:p.volume(),reverse=True)
  if sum(abs(p.volume()) for p in pieces[1:])>25:raise ValueError('Unexpected baffle fragments')
  shape=pieces[0]
  write(f'baffle-type-{typ:02}',shape,'opaque black resin; qualify 0.4 mm walls')
  # CAD-format reference from the same closed mesh (not an analytic nurbs surface).
 # Universal seat: fits over an M2 top-entering mounting screw. Magnet is removable for service.
 seat=mf.Manifold.cylinder(1.0,1.75,circular_segments=48)+mf.Manifold.cylinder(4.0,3.3,circular_segments=48).translate([0,0,1.0])
 seat-=mf.Manifold.cylinder(5.2,1.1,circular_segments=24).translate([0,0,-.1])
 # A countersunk M2 head seats above the LED package height; the broad holder starts at z=1 mm.
 seat-=mf.Manifold.cylinder(1.0,1.1,2.1,circular_segments=40).translate([0,0,.7])
 seat-=mf.Manifold.cylinder(2.25,2.1,circular_segments=40).translate([0,0,2.8])
 write('magnet-seat-M2-4mm',seat,'PA12; magnet pocket 4.2 mm')
 washer=mf.Manifold.cylinder(1,1.75,circular_segments=40)-mf.Manifold.cylinder(1.2,1.1,circular_segments=32).translate([0,0,-.1])
 write('pcb-head-spacer-M2',washer,'PA12 or purchased nylon; lifts screw head above LEDs')
 # Explicit insertion tool/optical fit coupon.
 coupon=mf.Manifold.cube([30,20,3])
 for i,dia in enumerate([4.0,4.1,4.2,4.3]):coupon-=mf.Manifold.cylinder(2.2,dia/2,circular_segments=40).translate([4+i*7,10,.9])
 write('magnet-fit-coupon',coupon,'same process as magnet seats')

def surface_mesh(vs,segments=128,sample_rotation=None,seam_mm=None):
 center=vs.mean(axis=0)
 # A narrow seam is obtained by shrinking the tangent triangle before spherical projection.
 edge_normals=[np.cross(vs[i],vs[(i+1)%3]) for i in range(3)]
 edge_offsets=[abs(n@center)/np.linalg.norm(n) for n in edge_normals]
 seam=R['shell_seam_mm'] if seam_mm is None else seam_mm
 shrink=(seam/2/152.5)/min(edge_offsets)
 vs=vs*(1-shrink)+center*shrink
 coords=[];lookup={}
 for i in range(segments+1):
  for j in range(segments+1-i):
   lookup[i,j]=len(coords);q=vs[0]*(1-(i+j)/segments)+vs[1]*i/segments+vs[2]*j/segments;coords.append(q/np.linalg.norm(q))
 directions=np.array(coords);sample=directions if sample_rotation is None else directions@sample_rotation.T
 lon=np.degrees(np.arctan2(sample[:,1],sample[:,0]));lat=np.degrees(np.arcsin(sample[:,2]))
 heights=map_coordinates(H,[(lat+90)*2,(lon+180)*2],order=1,mode='nearest')
 vertices=np.vstack([directions*(152.5+heights[:,None]),directions*151.5]);count=len(coords);faces=[]
 for i in range(segments):
  for j in range(segments-i):
   a,b,c=lookup[i,j],lookup[i+1,j],lookup[i,j+1];faces.append([a,b,c]);faces.append([a+count,c+count,b+count])
   if i+j<segments-1:
    d=lookup[i+1,j+1];faces.append([b,d,c]);faces.append([b+count,c+count,d+count])
 edge=[lookup[i,0] for i in range(segments)]+[lookup[segments-j,j] for j in range(segments)]+[lookup[0,segments-i] for i in range(segments)]
 for a,b in zip(edge,edge[1:]+edge[:1]):faces.extend([[a,b+count,b],[a,a+count,b+count]])
 m=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
 if m.volume<0:m.invert()
 return m

def shell_panels():
 degree=np.bincount(np.array(D['edges']).ravel(),minlength=len(N))
 anchor_manifest=[]
 for sector in range(20):
  ids=sorted(set(i for f in D['faces'] if f['sector']==sector for i in f['nodes']));vs=N[[i for i in ids if degree[i]==5]]
  if np.dot(np.cross(vs[1]-vs[0],vs[2]-vs[0]),vs[0])<0:vs=vs[[0,2,1]]
  mesh=surface_mesh(vs);shape=manifold(mesh)
  for anchor in [a for a in D['anchors'] if a['sector']==sector]:
   t=D['tiles'][anchor['tile']];x,y=t['holes'][anchor['hole']];p=local_point(t,x,y,0);normal=np.array(t['normal']);d=p@normal
   inner=-d+math.sqrt(d*d+151.5**2-p@p)
   # Frame-seat magnet ends at local z=4.8. Matching shell magnet starts 0.2 mm above it.
   bottom=5.0;magnet_end=7.0
   if inner<magnet_end+.5:raise ValueError('Insufficient shell magnet back wall')
   boss=mf.Manifold.cylinder(inner-bottom+.45,3.3,circular_segments=48).translate([x,y,bottom])
   # Blind magnet pocket opens toward the frame; retain with a removable silicone dot after pull testing.
   bore=mf.Manifold.cylinder(2.01,2.1,circular_segments=48).translate([x,y,bottom-.01])
   boss=boss-bore
   shape=shape+boss.transform(xform(t))
   anchor_manifest.append({**anchor,'shell_boss_bottom_local_z':bottom,'shell_inner_local_z':inner,'seat_top_local_z':5.0,'frame_magnet_face_local_z':4.8,'magnet_gap_mm':.2})
  # Physical support opening is present in the south polar panels, not concealed in the coverage map.
  shape-=mf.Manifold.cylinder(35,7,circular_segments=64).translate([0,0,-170])
  write(f'terrain-shell-{sector+1:02}-25x',shape,'translucent optical resin with qualified charcoal finish')
 (OUT/'shell-anchors.json').write_text(json.dumps(anchor_manifest,indent=2))

def main():
 p=argparse.ArgumentParser();p.add_argument('--only',choices=['baffles','shells','all'],default='all');a=p.parse_args()
 if a.only in ['baffles','all']:baffles()
 if a.only in ['shells','all']:shell_panels()
 (OUT/f'mesh-audit-{a.only}.json').write_text(json.dumps(AUDIT,indent=2))
if __name__=='__main__':main()
