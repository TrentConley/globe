"""Vancouver tile 124: real curved shell, matching baffle and printable bench cradle."""
import json,math
import numpy as np
import cadquery as cq
from scipy.spatial.transform import Rotation
import build as b
import surfaces as s
D=b.D;t=D['tiles'][124];M=np.eye(4);M[:3,:3]=np.column_stack([t['ex'],t['ey'],t['normal']]);M[:3,3]=t['center'];vs=b.N[D['faces'][124]['nodes']]
if np.cross(vs[1]-vs[0],vs[2]-vs[0])@vs[0]<0:vs=vs[[0,2,1]]
for name,target in [('vancouver',None),('himalaya',[28,86])]:
 rotation=None
 if target:
  lat,lon=np.radians(target);n=np.array([math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)]);source=np.array(t['center']);source/=np.linalg.norm(source);axis=np.cross(source,n);axis/=np.linalg.norm(axis);rotation=Rotation.from_rotvec(axis*math.acos(source@n)).as_matrix()
 shape=s.manifold(s.surface_mesh(vs,64,rotation,seam_mm=.1))
 for x,y in t['holes']:
  p=s.local_point(t,x,y,0);n=np.array(t['normal']);d=p@n;inner=-d+math.sqrt(d*d+151.5**2-p@p)
  boss=s.mf.Manifold.cylinder(inner-5+.45,3.3,circular_segments=48).translate([x,y,5])-s.mf.Manifold.cylinder(2.01,2.1,circular_segments=40).translate([x,y,4.99]);shape+=boss.transform(s.xform(t))
 mesh=s.tm(shape);mesh.apply_transform(np.linalg.inv(M));s.write(f'prototype-shell-{name}-25x',mesh,'translucent resin; local PCB coordinates')
# Open-center cradle leaves underside driver and connectors accessible to probes/cables.
base=cq.Workplane('XY').rect(56,48).rect(39,30).extrude(3).val().translate((0,2,-20))
for x,y in t['holes']:
 p=b.cylinder(3.3,[x,y,-20],[x,y,-1]);near=[x,(-16 if y<0 else 23),-18.5];base=base.fuse(p,b.cylinder(2,[x,y,-18.5],near))
 base=base.cut(b.cylinder(1.1,[x,y,-21],[x,y,1]),b.hexprism(4.2,-20.1,2,x,y))
b.export('prototype-cradle-type-02',base.clean(),group='prototype')
(s.OUT/'mesh-audit-prototype.json').write_text(json.dumps(s.AUDIT,indent=2));(s.OUT/'cad-audit-prototype.json').write_text(json.dumps(b.REPORT,indent=2));(s.OUT/'prototype.json').write_text(json.dumps({'tile':124,'sector':7,'bus':3,'address':'0x30','boardType':t['type'],'baffle':'baffle-type-02.stl','shells':['prototype-shell-vancouver-25x.stl','prototype-shell-himalaya-25x.stl'],'cradle':'prototype-cradle-type-02.stl','mounts':3,'magnetPairs':3,'pcbCoordinates':True,'himalaya':'Terrain stress coupon centered approximately at 28N 86E, on identical curvature and board outline.'},indent=2))
