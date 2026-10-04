"""Parametric A0 engineering solids; all dimensions millimetres, +Z north.
Run with XDG_CACHE_HOME=/tmp/globe-cache python3 cad/build.py.
STEP contains analytic mechanical solids; terrain uses a separate closed mesh.
"""
from pathlib import Path
import json, math, time, argparse
import numpy as np
import cadquery as cq
from cadquery import Vector as V

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/generated'; OUT.mkdir(exist_ok=True)
D=json.loads((OUT/'layout.json').read_text()); R=D['requirements']
N=np.array(D['nodes']);N[np.abs(N)<1e-7]=0;N/=np.linalg.norm(N,axis=1)[:,None]; E=D['edges']; RF=R['frame_vertex_radius_mm']
REPORT=[]; ASSEMBLY=[]

def vec(a): return V(*[float(v) for v in a])
def cylinder(radius,a,b):
 a=np.asarray(a,float);b=np.asarray(b,float);d=b-a
 return cq.Solid.makeCylinder(radius,float(np.linalg.norm(d)),vec(a),vec(d))
def sphere(r,p): return cq.Solid.makeSphere(r,vec(p),angleDegrees1=-90,angleDegrees2=90)
def fuse(parts):
 if len(parts)==1:return parts[0]
 return parts[0].fuse(*parts[1:],tol=.002)
def prism(poly,z,height):return cq.Workplane('XY').polyline(poly).close().extrude(height).val().translate((0,0,z))
def transformed(s,t):
 return s.moved(cq.Plane(origin=vec(t['center']),xDir=vec(t['ex']),normal=vec(t['normal'])).location)

def radial_slot(a,b):
 a=np.asarray(a);b=np.asarray(b);d=b-a;angle=math.degrees(math.atan2(d[1],d[0]));return cq.Workplane("XY").box(float(np.linalg.norm(d)),12,.5).val().rotate((0,0,0),(0,0,1),angle).translate(vec((a+b)/2))
def hexprism(flat,z,h,x=0,y=0):
 return cq.Workplane('XY').center(x,y).polygon(6,flat/math.cos(math.pi/6)).extrude(h).val().translate((0,0,z))
def export(name,s,material='PA12',stl=True,group='frame'):
 if not s.isValid():raise ValueError(name+' is not a valid BRep')
 solids=s.Solids()
 if not solids:raise ValueError(name+' contains no solids')
 bb=s.BoundingBox();info={'part':name,'material':material,'solids':len(solids),'volume_mm3':s.Volume(),'bounds_mm':[bb.xlen,bb.ylen,bb.zlen],'valid':True,'group':group}
 cq.exporters.export(s,str(OUT/(name+'.step')))
 if stl:cq.exporters.export(s,str(OUT/(name+'.stl')),tolerance=.12,angularTolerance=.15)
 REPORT.append(info); ASSEMBLY.append((name,s,group));print(name,round(info['volume_mm3']),len(solids),flush=True)
 return s

def frame_geometry():
 parts=[]
 for a,b in E:parts.append(cylinder(R['frame_strut_radius_mm'],N[a]*RF,N[b]*RF))
 for n in N:parts.append(sphere(R['frame_strut_radius_mm'],n*RF))
 cutters=[];posts=[]
 for t in D['tiles']:
  if not t['populated'] and not any(a['tile']==t['id'] for a in D.get('anchors',[])):continue
  for h in t['holes']:
   q=np.array(t['center'])+np.array(t['ex'])*h[0]+np.array(t['ey'])*h[1];normal=np.array(t['normal'])
   a=q-normal*11;b=q-normal
   near=N[np.argmax(N@(q/np.linalg.norm(q)))]*RF
   posts.extend([cylinder(3.3,a,b),cylinder(1.8,near,a+normal*4)])
   # A top-entering M2 screw and a bottom-loaded, captive DIN 934 nut.
   local=cylinder(1.1,[h[0],h[1],-15],[h[0],h[1],1])
   nut=hexprism(4.2,-11.1,2.0,h[0],h[1])
   cutters.extend([transformed(local,t),transformed(nut,t)])
 # Twelve bolted split-plane joints, four distributed around each coordinate plane.
 joints=[]
 for axis in range(3):
  candidates=[]
  other=[i for i in range(3) if i!=axis]
  for a,b in E:
   p=N[a]*RF;q=N[b]*RF
   if p[axis]*q[axis]>1e-6 or abs(p[axis]-q[axis])<1e-5:continue
   f=-p[axis]/(q[axis]-p[axis])
   if not 0<=f<=1:continue
   c=p+(q-p)*f
   if min(abs(c[other[0]]),abs(c[other[1]]))<20:continue
   candidates.append(c)
  for k in range(4):
   angle=math.pi/4+k*math.pi/2;direction=np.zeros(3);direction[other]=[math.cos(angle),math.sin(angle)]
   p=max(candidates,key=lambda c:np.dot(c/np.linalg.norm(c),direction));axisv=np.eye(3)[axis]
   q=p-p/np.linalg.norm(p)*7
   parts.extend([cylinder(2,p-axisv*2,q-axisv*2),cylinder(2,p+axisv*2,q+axisv*2)])
   p=q
   joints.append({'axis':axis,'center':p.tolist(),'screw':'M2 x 16','nut':'M2 DIN 934'})
   parts.append(cylinder(4.5,p-axisv*6,p+axisv*6))
   cutters.append(cylinder(1.1,p-axisv*7,p+axisv*7))
   # Screw-head counterbore; the opposite side uses an accessible loose nut/washer.
   cutters.append(cylinder(2.15,p-axisv*6.1,p-axisv*3.9))
 # Ten radial tube sockets coincide with the nonpolar five-valent icosahedron vertices.
 degree=np.bincount(np.array(E).ravel(),minlength=len(N));major=[n for n,d in zip(N,degree) if d==5 and abs(n[2])<.9]
 for n in major:
  p=n*RF;radial=np.array([p[0],p[1],0]);radial/=np.linalg.norm(radial)
  a=p-radial*10;b=p+radial*3
  parts.append(cylinder(6,a,b));cutters.append(cylinder(4.15,a-radial,p-radial*.5))
  cutters.append(radial_slot(a-radial,p-radial))
  pin=p-radial*4;cutters.append(cylinder(1.1,pin+[0,0,-6],pin+[0,0,6]))
 return parts+posts,cutters,joints,major

def build_frame():
 import subprocess,sys
 subprocess.run([sys.executable,str(ROOT/'cad/frame_mesh.py')],check=True)
 subprocess.run([sys.executable,str(ROOT/'cad/mesh_step.py')],check=True)

def build_spine_and_hubs():
 degree=np.bincount(np.array(E).ravel(),minlength=len(N));major=[n for n,d in zip(N,degree) if d==5 and abs(n[2])<.9]
 spine=cylinder(6,[0,0,-186],[0,0,128]).cut(cylinder(4,[0,0,-187],[0,0,129]))
 spine=spine.cut(cylinder(3,[0,0,-140],[8,0,-140]))
 export('spine-12OD-8ID-314L',spine,'6061 aluminum; deburr 6 mm cable exit',group='metal')
 for level in [-1,1]:
  points=[n*RF for n in major if n[2]*level>0];z=float(np.mean([p[2] for p in points]));hub=cylinder(14,[0,0,z-9],[0,0,z+9]);cuts=[cylinder(6.1,[0,0,z-10],[0,0,z+10])]
  for j,p in enumerate(points):
   d=np.array([p[0],p[1],0]);d/=np.linalg.norm(d)
   hub=hub.fuse(cylinder(6,d*9+[0,0,z],d*23+[0,0,z]))
   cuts.append(cylinder(4.15,d*14+[0,0,z],d*24+[0,0,z]));cuts.append(radial_slot(d*16+[0,0,z],d*24+[0,0,z]));pin=d*18+[0,0,z]
   cuts.append(cylinder(1.1,pin+[0,0,-6],pin+[0,0,6]))
   tube=cylinder(4,d*15+[0,0,z],p-d*.8).cut(cylinder(2,d*14+[0,0,z],p+d))
   for center in [pin,p-d*4]:tube=tube.cut(cylinder(1.1,center+[0,0,-5],center+[0,0,5]))
   export(f'spoke-{level:+d}-{j+1}',tube,'6061 aluminum',group='metal')
  for y in [-10,10]:cuts.append(cylinder(1.65,[-25,y,z],[25,y,z]))
  hub=hub.cut(*cuts).clean()
  for side in [-1,1]:
   # 0.4 mm clamp gap; it closes onto the tube before the halves bottom out.
   clip=cq.Solid.makeBox(40,80,40,V(.2 if side>0 else -40.2,-40,z-20))
   export(f'hub-{level:+d}-half-{side:+d}',hub.intersect(clip).clean())

def build_base():
 # Base bottom -224, top -188. Electronics rest above a removable steel ballast disk.
 body=cylinder(100,[0,0,-224],[0,0,-191]).cut(cylinder(97,[0,0,-221],[0,0,-190]))
 for a in range(0,360,30):
  d=np.array([math.cos(math.radians(a)),math.sin(math.radians(a)),0]);e=np.array([-d[1],d[0],0])
  for z in [-215,-199]:
   # Round radial ventilation ports leave the outer lip intact.
   body=body.cut(cylinder(2.0,d*95+[0,0,z],d*102+[0,0,z]))
 for x,y in [(80,0),(-80,0),(0,80),(0,-80)]:
  body=body.fuse(cylinder(4,[x,y,-221],[x,y,-191]));body=body.cut(cylinder(1.7,[x,y,-199],[x,y,-190]));body=body.cut(hexprism(5.7,-199,2.6,x,y))
 # Bottom-side nuts lock four M3 lid screws; print pockets are loaded from the inside before assembly.
 # Pi Zero hole rectangle 58 x 23; off-center placement clears the stand fasteners.
 for x,y in [(6,-11.5),(64,-11.5),(6,11.5),(64,11.5)]:
  body=body.fuse(cylinder(3,[x,y,-213],[x,y,-207]));body=body.fuse(cylinder(2.5,[x,y,-221],[x,y,-213]));body=body.cut(cylinder(1.1,[x,y,-211],[x,y,-206]))
 # A replaceable panel connector opening, dimensioned for an M8 bulkhead DC inlet envelope.
 body=body.cut(cylinder(4.1,[0,-102,-205],[0,-95,-205]))
 export('base-cup',body.clean(),group='base')
 lid=cylinder(100,[0,0,-191],[0,0,-188])
 for x,y in [(80,0),(-80,0),(0,80),(0,-80)]:lid=lid.cut(cylinder(1.7,[x,y,-192],[x,y,-187]))
 for a in range(0,360,90):
  x,y=17*math.cos(math.radians(a)),17*math.sin(math.radians(a));lid=lid.cut(cylinder(1.7,[x,y,-192],[x,y,-187]))
 lid=lid.cut(cylinder(4,[0,0,-192],[0,0,-187]));export('base-lid',lid,group='base')
 ballast=cylinder(75,[0,0,-220],[0,0,-214]).cut(cylinder(7,[0,0,-221],[0,0,-213]))
 # Keep pi-support columns clear through the purchased/cut ballast plate.
 for x,y in [(6,-11.5),(64,-11.5),(6,11.5),(64,11.5)]:ballast=ballast.cut(cylinder(3.3,[x,y,-221],[x,y,-213]))
 export('ballast-150D-6T',ballast,'mild steel',group='metal')
 collar=cylinder(23,[0,0,-188],[0,0,-184]).fuse(cylinder(18,[0,0,-184],[0,0,-169]))
 collar=collar.cut(cylinder(6.1,[0,0,-186],[0,0,-168]))
 collar=collar.cut(cylinder(4.2,[0,0,-189],[0,0,-185]))
 for y in [-10,10]:collar=collar.cut(cylinder(1.65,[-25,y,-177],[25,y,-177]))
 for a in range(0,360,90):
  x,y=17*math.cos(math.radians(a)),17*math.sin(math.radians(a));collar=collar.cut(cylinder(1.7,[x,y,-189],[x,y,-183]))
 for side in [-1,1]:
  clip=cq.Solid.makeBox(30,60,30,V(.2 if side>0 else -30.2,-30,-190))
  export(f'base-collar-half-{side:+d}',collar.intersect(clip).clean(),group='base')

def build_tiles():
 representatives={}
 for t in D['tiles']:representatives.setdefault(t['type'],t)
 for typ,t in representatives.items():
  plate=prism(t['outline'],-1,1)
  for x,y in t['holes']:plate=plate.cut(cylinder(1.1,[x,y,-2],[x,y,1]))
  export(f'pcb-outline-type-{typ:02}',plate,'FR4 1 mm',group='pcb',stl=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('--only',choices=['frame','base','spine','tiles','all'],default='all');args=p.parse_args()
 if args.only in ['frame','all']:build_frame()
 if args.only in ['base','all']:build_base()
 if args.only in ['spine','all']:build_spine_and_hubs()
 if args.only in ['tiles','all']:build_tiles()
 (OUT/f'cad-audit-{args.only}.json').write_text(json.dumps(REPORT,indent=2))
 print('Exported',len(REPORT),'valid analytic parts',flush=True)
if __name__=='__main__':main()
