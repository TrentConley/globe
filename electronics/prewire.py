"""Route regular matrix rows/columns before the general-purpose local router.
Only collision-free segments are added; residual connections are left for routing.
"""
from pathlib import Path
import csv,math,json
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated';mm=p.FromMM
V=lambda a:p.VECTOR2I(mm(a[0]),mm(a[1]))
def xy(v):return (p.ToMM(v.x),p.ToMM(v.y))
def intersects(a,b,r):
 t0,t1=0,1;dx,dy=b[0]-a[0],b[1]-a[1]
 for q,v in [(-dx,a[0]-r[0]),(dx,r[2]-a[0]),(-dy,a[1]-r[1]),(dy,r[3]-a[1])]:
  if abs(q)<1e-10:
   if v<0:return False
  elif q<0:t0=max(t0,v/q)
  else:t1=min(t1,v/q)
  if t0>t1:return False
 return True
def main():
 layout=json.loads((ROOT/'cad/generated/layout.json').read_text());reps={}
 for t in layout['tiles']:reps.setdefault(t['type'],t)
 for typ,t in reps.items():
  path=OUT/f'led-tile-{typ:02}.kicad_pcb';b=p.LoadBoard(str(path));obs=[];fps={f.GetReference():f for f in b.GetFootprints()};added=0
  poly=[(60+x,60-y) for x,y in t['outline']];poly.reverse()
  for f in b.GetFootprints():
   for pad in f.Pads():
    if not pad.GetLayerSet().Contains(p.F_Cu) and not pad.GetLayerSet().Contains(p.B_Cu):continue
    box=pad.GetBoundingBox();lo=xy(box.GetOrigin());hi=xy(box.GetEnd());layers=set(range(4)) if pad.GetAttribute()==p.PAD_ATTRIB_NPTH else {k for k,l in enumerate([p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]) if pad.IsOnLayer(l)}
    obs.append((pad.GetNetname(),layers,(*lo,*hi)))
  def clear(a,z,net,layers,width):
   r=width/2+.105
   for q in (a,z):
    for u,v in zip(poly,poly[1:]+poly[:1]):
     if ((v[0]-u[0])*(q[1]-u[1])-(v[1]-u[1])*(q[0]-u[0]))/math.dist(u,v)<width/2+.26:return False
   for other,ls,bb in obs:
    if (other==net and other) or not layers&ls:continue
    rect=(bb[0]-r,bb[1]-r,bb[2]+r,bb[3]+r)
    if intersects(a,z,rect):return False
   return True
  def track(a,z,net,layer):
   nonlocal added
   if math.dist(a,z)<1e-6:return True
   if not clear(a,z,net,{layer},.1):return False
   tr=p.PCB_TRACK(b);tr.SetStart(V(a));tr.SetEnd(V(z));tr.SetWidth(mm(.1));tr.SetLayer([p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu][layer]);tr.SetNet(b.FindNet(net));b.Add(tr);added+=1
   obs.append((net,{layer},(min(a[0],z[0])-.05,min(a[1],z[1])-.05,max(a[0],z[0])+.05,max(a[1],z[1])+.05)));return True
  rows=list(csv.DictReader((OUT/f'led-tile-{typ:02}-channels.csv').open()));groups={}
  # SW anodes share a horizontal front-side trace for each physical row.
  for row in rows:groups.setdefault(float(row['cell_y_mm']),[]).append(row)
  for y,group in groups.items():
   ends=[]
   for row in sorted(group,key=lambda r:float(r['x_mm'])):
    pad=next(q for q in fps[row['reference']].Pads() if q.GetNumber()=='2');a=xy(pad.GetPosition());z=(a[0],60-y+.72);net=pad.GetNetname()
    if track(a,z,net,0):ends.append(z)
   for a,z in zip(ends,ends[1:]):track(a,z,net,0)
  columns={}
  for row in rows:
   pad=next(q for q in fps[row['reference']].Pads() if q.GetNumber()=='1');a=xy(pad.GetPosition());z=(a[0],a[1]-.72);net=pad.GetNetname()
   if clear(z,z,net,set(range(4)),.5) and clear(a,z,net,{0},.1):
    track(a,z,net,0);via=p.PCB_VIA(b);via.SetPosition(V(z));via.SetWidth(p.F_Cu,mm(.45));via.SetDrill(mm(.2));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet(net));b.Add(via);obs.append((net,set(range(4)),(z[0]-.225,z[1]-.225,z[0]+.225,z[1]+.225)));columns.setdefault(net,[]).append(z)
  for net,points in columns.items():
   points.sort(key=lambda q:q[1])
   for a,z in zip(points,points[1:]):track(a,z,net,1)
  p.SaveBoard(str(path),b);p.ExportSpecctraDSN(b,str(path.with_suffix('.dsn')));s=path.with_suffix('.dsn').read_text().replace('(clearance 25 (type smd_smd))','(clearance 100 (type smd_smd))');path.with_suffix('.dsn').write_text(s);print(typ,'prewired segments',added,flush=True)
if __name__=='__main__':main()
