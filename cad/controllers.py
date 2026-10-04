"""Sector service carriers and base wiring carrier. PA12; modules are envelopes."""
import json,math
import numpy as np
import cadquery as cq
import build as b
from cadquery import Vector as V
D=b.D;N=b.N;OUT=b.OUT;manifest=[]
def box(w,h,d,x=0,y=0,z=0):return cq.Solid.makeBox(w,h,d,V(x-w/2,y-h/2,z))
for s in D['sectors']:
 sid=s['id'];faces=[f for f in D['faces'] if f['sector']==sid];ids=sorted(set(i for f in faces for i in f['nodes']));normal=N[ids].mean(axis=0);normal/=np.linalg.norm(normal);ex=N[ids[1]]-N[ids[0]];ex-=normal*(ex@normal);ex/=np.linalg.norm(ex);ey=np.cross(normal,ex);center=normal*96;t={'center':center.tolist(),'ex':ex.tolist(),'ey':ey.tolist(),'normal':normal.tolist()}
 local=box(64,44,2,z=-10).cut(box(54,32,4,z=-11))
 for x in [-28,28]:
  for y in [-18,18]:
   local=local.fuse(b.cylinder(3,[x,y,-9],[x,y,0]));local=local.cut(b.cylinder(1.1,[x,y,-11],[x,y,2]))
 shape=b.transformed(local,t);edge_ids={tuple(sorted([f['nodes'][i],f['nodes'][(i+1)%3]])) for f in faces for i in range(3)};targets=[]
 for a,z in edge_ids:
  q=(N[a]+N[z])*66;rel=q-center;xy=np.array([rel@ex,rel@ey]);
  if np.linalg.norm(xy)>37:targets.append((a,z,q,xy))
 mounts=[]
 for xy in [np.array([-30.,-20.]),np.array([30.,-20.]),np.array([0.,21.])]:
  target=min(targets,key=lambda item:math.acos(np.clip(item[3]@xy/(np.linalg.norm(item[3])*np.linalg.norm(xy)),-1,1))+.002*np.linalg.norm(item[3]));a,z,q,_=target;targets.remove(target);along=N[z]-N[a];along/=np.linalg.norm(along);out=q/np.linalg.norm(q);out-=along*(out@along);out/=np.linalg.norm(out);side=np.cross(along,out)
  socket=b.cylinder(3.8,q-along*5,q+along*5).cut(b.cylinder(2.05,q-along*6,q+along*6))
  # The open saddle faces outward: it can be pushed onto a completed cage from inside.
  cut=box(10,14,14,x=5,z=-7);socket=socket.cut(b.transformed(cut,{'center':q,'ex':out,'ey':side,'normal':along}))
  start=center+ex*xy[0]+ey*xy[1]-normal*9;end=q-out*3
  shape=shape.fuse(b.cylinder(1.8,start,end),socket)
  mounts.append({'frameEdge':[int(a),int(z)],'center':q.tolist(),'retainer':'2.5 mm PA66 cable tie around the saddle and cage strut'})
 name=f'controller-carrier-{sid+1:02}';b.export(name,shape.clean(),group='controllers');manifest.append({'sector':sid,**t,'mounts':mounts,'perfboard_mm':[60,40,1.6],'hole_xy_mm':[[x,y] for x in [-28,28] for y in [-18,18]],'components':'Pico on inward face; mux, RS485 transceiver, 3.3V regulator on outward face; wiring per diagram'})
# Left-hand removable base perfboard carrier, above ballast, below the lid.
shape=box(72,76,1.5,x=-39,z=-213.5)
for x in [-71,-7]:
 for y in [-34,34]:
  shape=shape.fuse(b.cylinder(3,[x,y,-213],[x,y,-210.5]));shape=shape.cut(b.cylinder(1.1,[x,y,-214],[x,y,-209]))
b.export('base-electronics-carrier',shape.clean(),group='base')
(OUT/'controller-mounts.json').write_text(json.dumps(manifest,indent=2));(OUT/'cad-audit-controllers.json').write_text(json.dumps(b.REPORT,indent=2))
