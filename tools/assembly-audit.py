"""Actual mesh assembly, independent file inspection and intersection audit."""
from pathlib import Path
import json,math
import numpy as np
import trimesh
import cadquery as cq
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'engineering/release';CAD=ROOT/'cad/generated';D=json.loads((CAD/'layout.json').read_text());meshes={};instances=[];audit=[]
def transform(t):
 m=np.eye(4);m[:3,:3]=np.column_stack([t['ex'],t['ey'],t['normal']]);m[:3,3]=t['center'];return m
def add(name,group,source=None,matrix=None,mesh=None):
 key=source or name
 if key not in meshes:
  m=mesh if mesh is not None else trimesh.load_mesh(CAD/(key+'.stl'))
  if not m.is_watertight or not m.is_winding_consistent or m.volume<=0:raise ValueError('Bad mesh '+key)
  meshes[key]=m;audit.append({'part':key,'watertight':True,'volume_mm3':m.volume,'triangles':len(m.faces),'connectedSolids':len(m.split(only_watertight=False))})
 instances.append({'name':name,'group':group,'mesh':key,'transform':(np.eye(4) if matrix is None else matrix).tolist()})
for path in sorted(CAD.glob('*.stl')):
 name=path.stem
 if name.startswith('cage-octant'):add(name,'frame')
 elif name.startswith('terrain-shell'):add(name,'shell')
 elif name.startswith(('spine-','spoke-','hub-')):add(name,'support')
 elif name.startswith(('base-','ballast-')):add(name,'base')
 elif name.startswith('controller-carrier'):add(name,'controllers')
for typ in range(6):
 shape=cq.importers.importStep(str(CAD/f'pcb-outline-type-{typ:02}.step')).val();v,f=shape.tessellate(.05,.2);m=trimesh.Trimesh(vertices=[p.toTuple() for p in v],faces=f,process=True);meshes[f'pcb-type-{typ:02}']=m;m.export(CAD/f'pcb-type-{typ:02}.stl')
envelopes=json.loads((ROOT/'electronics/generated/component-envelopes.json').read_text())
for t in D['tiles']:
 if not t['populated']:continue
 matrix=transform(t);typ=t['type'];add(f"pcb-{t['id']:03}",'pcb',f'pcb-type-{typ:02}',matrix);add(f"cells-{t['id']:03}",'baffles',f'baffle-type-{typ:02}',matrix)
 for h in range(3):
  x,y=t['holes'][h];local=np.eye(4);local[:3,3]=[x,y,0];anchor=any(a['tile']==t['id'] and a['hole']==h for a in D['anchors']);part='magnet-seat-M2-4mm' if anchor else 'pcb-head-spacer-M2';add(f"seat-{t['id']}-{h}",'mounts',part,matrix@local)
 for e in envelopes[str(typ)]:
  lo,hi=np.array(e['low']),np.array(e['high']);m=trimesh.creation.box(hi-lo);m.apply_translation((lo+hi)/2);add(f"component-{t['id']}-{e['ref']}",'component-clearance',f"envelope-{typ}-{e['ref']}",matrix,mesh=m)
# Controller perfboards and reserved module/Pico clearances; all are explicitly marked envelopes.
for c in json.loads((CAD/'controller-mounts.json').read_text()):
 matrix=transform(c);m=trimesh.creation.box([60,40,1.6]);m.apply_translation([0,0,.8]);add(f"sector-board-{c['sector']:02}",'controller-boards','sector-board',matrix,mesh=m)
 for name,lo,hi in [('pico',[-25.5,-10.5,-6],[25.5,10.5,-1]),('buck',[-26,-16,1.6],[-7,6,11.6]),('mux',[-3,-16,1.6],[27,4,8.6]),('rs485',[-3,5,1.6],[20,18,8.6])]:
  lo=np.array(lo);hi=np.array(hi);m=trimesh.creation.box(hi-lo);m.apply_translation((lo+hi)/2);add(f"sector-{c['sector']}-{name}",'controller-envelopes',name,matrix,mesh=m)
# Shell anchors on unpopulated ocean tiles use a 1 mm dummy PCB spacer.
for a in D['anchors']:
 t=D['tiles'][a['tile']]
 if t['populated']:continue
 x,y=t['holes'][a['hole']];matrix=transform(t);q=np.eye(4);q[:3,3]=[x,y,0];add(f"ocean-anchor-{a['tile']}-{a['hole']}",'mounts','magnet-seat-M2-4mm',matrix@q);q[2,3]=-1;add(f"ocean-spacer-{a['tile']}-{a['hole']}",'mounts','pcb-head-spacer-M2',matrix@q)
for i,a in enumerate(D['anchors']):
 t=D['tiles'][a['tile']];x,y=t['holes'][a['hole']];matrix=transform(t)
 for side,z in [('frame',3.8),('shell',6.0)]:
  m=trimesh.creation.cylinder(radius=2,height=2,sections=32);q=np.eye(4);q[:3,3]=[x,y,z];add(f'magnet-{i}-{side}','mounts','purchased-magnet-4x2',matrix@q,mesh=m)
(CAD/'assembly.json').write_text(json.dumps({'units':'mm','instances':instances},separators=(',',':')))
(OUT/'mesh-audit.json').write_text(json.dumps(audit,indent=2));print('Loaded',len(meshes),'unique meshes,',len(instances),'instances',flush=True)
# Collisions between material groups. Mating screw/washer contact and envelope overlaps with their own PCB are omitted.
groups={}
for item in instances:
 group=item['group'];groups.setdefault(group,trimesh.collision.CollisionManager()).add_object(item['name'],meshes[item['mesh']],np.array(item['transform']))
checks=[('frame','controllers'),('support','controllers'),('shell','baffles'),('frame','pcb'),('frame','component-clearance'),('support','controller-envelopes'),('controllers','controller-envelopes'),('controllers','pcb'),('base','support')];report=[]
for a,b in checks:
 collided,pairs=groups[a].in_collision_other(groups[b],return_names=True);contacts=[]
 if (a,b)==('frame','pcb'):
  raised=trimesh.collision.CollisionManager()
  for item in instances:
   if item['group']=='pcb':
    matrix=np.array(item['transform']);matrix[:3,3]+=matrix[:3,2]*.02;raised.add_object(item['name'],meshes[item['mesh']],matrix)
  _,deep=groups[a].in_collision_other(raised,return_names=True);contacts=sorted(pairs-deep);pairs=deep
 if (a,b)==('base','support'):
  intended={(f'base-collar-half-{side:+d}','spine-12OD-8ID-314L') for side in [-1,1]}
  contacts=sorted(pairs & intended);pairs=pairs-intended
 report.append({'groups':[a,b],'intersections':[list(p) for p in sorted(pairs)],'matingContactsWithin002MM':[list(p) for p in contacts]});print(a,b,len(pairs),list(sorted(pairs))[:6],flush=True)
(OUT/'assembly-intersections.json').write_text(json.dumps(report,indent=2))
# Browser meshes are exact checked print boundaries; a separate JSON describes repeated instances.
web=ROOT/'artifacts/assembly';web.mkdir(parents=True,exist_ok=True)
colors={'shell':[58,60,60,255],'frame':[178,187,186,255],'support':[186,172,133,255],'base':[44,48,50,255],'controllers':[104,121,131,255],'pcb':[41,103,82,255],'baffles':[64,69,73,255],'mounts':[167,177,183,255],'component-clearance':[72,121,151,255],'controller-boards':[42,113,91,255],'controller-envelopes':[60,81,96,255]}
scene=trimesh.Scene()
for item in instances:
 if item['mesh'] not in scene.geometry:
  m=meshes[item['mesh']].copy();m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=colors[item['group']],metallicFactor=.1,roughnessFactor=.85));scene.geometry[item['mesh']]=m
 scene.graph.update(frame_to=item['name'],matrix=np.array(item['transform']),geometry=item['mesh'],metadata={'group':item['group']})
scene.export(web/'assembly.glb');(web/'assembly-index.json').write_text(json.dumps(instances,separators=(',',':')));print('Exported actual CAD assembly',round((web/'assembly.glb').stat().st_size/1e6,1),'MB',flush=True)

# Local-coordinate, buildable bench assembly, without floating full-globe supports.
prototype=trimesh.Scene()
for name,group in [('prototype-shell-vancouver-25x','shell'),('prototype-cradle-type-02','frame'),('baffle-type-02','baffles'),('pcb-type-02','pcb')]:
 m=trimesh.load_mesh(CAD/(name+'.stl'));m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=colors[group],metallicFactor=.1,roughnessFactor=.85));prototype.add_geometry(m,node_name=name)
# Ten emitters on the passive qualification board, at their actual channel positions.
selection=json.loads((OUT/'optical-bench-selection.json').read_text())
import csv
channel_rows={int(r['linear_channel']):r for r in csv.DictReader((ROOT/'electronics/generated/led-tile-02-channels.csv').open())}
for i,ch in enumerate(selection['channels']):
 r=channel_rows[ch];m=trimesh.creation.box([1,.5,.45]);m.apply_translation([float(r['x_mm']),float(r['y_mm']),.225]);m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[205,158,66,255],metallicFactor=0,roughnessFactor=.7));prototype.add_geometry(m,node_name=f'LED-D{i+1}-body-envelope')
t=D['tiles'][124]
for i,(x,y) in enumerate(t['holes']):
 m=trimesh.load_mesh(CAD/'magnet-seat-M2-4mm.stl');m.apply_translation([x,y,0]);m.visual.face_colors=[180,190,191,255];prototype.add_geometry(m,node_name=f'prototype-seat-{i}')
prototype.export(web/'prototype.glb')
