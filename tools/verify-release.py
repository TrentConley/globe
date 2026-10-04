"""Independently inspect saved manufacturing meshes, map/config consistency and PCB states."""
from pathlib import Path
import json,hashlib,subprocess,os
import trimesh
ROOT=Path(__file__).resolve().parents[1];CAD=ROOT/'cad/generated';OUT=ROOT/'engineering/release';rows=[]
for p in sorted(CAD.glob('*.stl')):
 m=trimesh.load_mesh(p);valid=m.is_watertight and m.is_winding_consistent and m.volume>0;solids=len(m.split(only_watertight=False));assert valid and solids==1,(p.name,valid,solids)
 rows.append({'file':p.name,'watertight':bool(m.is_watertight),'outwardWinding':bool(m.is_winding_consistent and m.volume>0),'connectedSolids':solids,'volumeMM3':float(m.volume),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'manufacturing-mesh-checks.json').write_text(json.dumps(rows,indent=2))
manifest=json.loads((OUT/'pixel-map.json').read_text());sha=hashlib.sha256((OUT/'pixel-map.npz').read_bytes()).hexdigest();assert sha==manifest['sha256']
for key,ids in manifest['sectors'].items():
 c=json.loads((ROOT/f'firmware/config/sector-{int(key):02}/sector.json').read_text());assert c['sector']==int(key) and c['map_sha256']==sha and sorted(c['tiles'])==sorted(i%16 for i in ids)
assert not any(r['intersections'] for r in json.loads((OUT/'assembly-intersections.json').read_text()))
env=dict(os.environ,XDG_CONFIG_HOME='/tmp/globe-config',XDG_CACHE_HOME='/tmp/globe-cache',XDG_DATA_HOME='/tmp/globe-data');summary=[]
for i in range(6):
 p=ROOT/f'electronics/generated/led-tile-{i:02}.kicad_pcb';target=p.with_name(p.stem+'-drc.json');subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','-o',str(target)],check=True,env=env,stdout=subprocess.DEVNULL);r=json.loads(target.read_text());summary.append({'board':p.name,'boardSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'violations':len(r['violations']),'unconnected':len(r['unconnected_items']),'status':'HOLD: NOT RELEASED FOR FABRICATION'})
(OUT/'matrix-routing-hold.json').write_text(json.dumps(summary,indent=2))
board=ROOT/'electronics/bench-release/optical-bench-10.kicad_pcb';drc=ROOT/'electronics/bench-release/optical-bench-10-drc.json';subprocess.run(['kicad-cli','pcb','drc',str(board),'--format','json','-o',str(drc)],check=True,env=env,stdout=subprocess.DEVNULL);r=json.loads(drc.read_text());assert not r['violations'] and not r['unconnected_items']
result={'manufacturingMeshesChecked':len(rows),'allClosedSingleSolids':True,'pixelMapSHA256':sha,'sectorConfigurationsChecked':len(manifest['sectors']),'benchPCBsha256':hashlib.sha256(board.read_bytes()).hexdigest(),'benchViolations':0,'benchUnconnected':0,'matrixFabricationReleased':False}
(OUT/'saved-file-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
