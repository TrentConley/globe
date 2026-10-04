"""Independent pad/net and placement check from the saved KiCad text file."""
from pathlib import Path
import re,json,csv
ROOT=Path(__file__).resolve().parents[1]
def parse(source):
 stack=[];root=None
 for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',source):
  if token=='(':
   item=[]
   if stack:stack[-1].append(item)
   stack.append(item)
  elif token==')':
   root=stack.pop()
  else:stack[-1].append(json.loads(token) if token.startswith('"') else token)
 return root
def audit():
 root=parse((ROOT/'electronics/generated/optical-bench-10.kicad_pcb').read_text());refs={}
 for item in root:
  if not isinstance(item,list) or item[0]!='footprint':continue
  ref=next(x[2] for x in item if isinstance(x,list) and x[:2]==['property','Reference']);pads={}
  for pad in item:
   if isinstance(pad,list) and pad[0]=='pad':
    net=next((x[2] for x in pad if isinstance(x,list) and x[0]=='net'),None)
    if net:pads[pad[1]]=net
  refs[ref]=pads
 for i in range(10):
  assert refs['D'+str(i+1)]=={'1':'GND','2':'LED'+str(i)}
  assert set(refs['R'+str(i+1)].values())=={'GPIO'+str(i),'LED'+str(i)}
  assert refs['P'+str(i)]=={'1':'GPIO'+str(i)}
 r=json.loads((ROOT/'electronics/generated/optical-bench-10-drc.json').read_text());assert not r['violations'] and not r['unconnected_items']
 release=ROOT/'electronics/bench-release';rows=list(csv.DictReader((release/'placement.csv').open()));assert len(rows)==20;assert {r['Ref'] for r in rows}=={f'{p}{i}' for p in ['D','R'] for i in range(1,11)}
 (release/'validation.json').write_text(json.dumps({'drcViolations':0,'unconnectedItems':0,'assemblyComponents':20,'channelsAudited':10,'physicalTested':False,'scope':'10-cell optical bench only; full globe matrix boards are not released'},indent=2));print('Bench saved-file connectivity and DRC audit passed')
if __name__=='__main__':audit()
