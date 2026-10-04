"""Conservative inward component envelopes, from placed footprints plus heights.
These are clearance envelopes, not verified manufacturer STEP models.
"""
from pathlib import Path
import pcbnew as p,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated';report={}
for typ in range(6):
 b=p.LoadBoard(str(OUT/f'led-tile-{typ:02}.kicad_pcb'));items=[]
 for f in b.GetFootprints():
  ref=f.GetReference()
  if ref.startswith(('D','H','JP')):continue
  points=[]
  for item in f.GraphicalItems():
   if item.GetClass()=='PCB_SHAPE' and item.GetLayer() in (p.B_Fab,p.F_Fab):
    bb=item.GetBoundingBox();points.extend([(p.ToMM(bb.GetLeft()),p.ToMM(bb.GetTop())),(p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom()))])
  if not points:
   a=f.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);points=[(x-3.5,y-3.5),(x+3.5,y+3.5)]
  low=[min(q[k] for q in points) for k in [0,1]];hi=[max(q[k] for q in points) for k in [0,1]];height=6 if ref=='JP1' else 3.2 if ref.startswith('J') else 1.1 if ref=='U1' else 1.5
  items.append({'ref':ref,'value':f.GetValue(),'low':[low[0]-60,60-hi[1],-1-height],'high':[hi[0]-60,60-low[1],-1]})
 report[typ]=items
(OUT/'component-envelopes.json').write_text(json.dumps(report,indent=2))
