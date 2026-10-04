"""Package checked A0 artifacts. Never emit full-matrix manufacturing Gerbers."""
from pathlib import Path
import zipfile,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';CAD=ROOT/'cad/generated';checks=ROOT/'engineering/release'
status={'release':'A0','dateUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'physicalFabricationOrTestingPerformed':False,'fullGlobeFabricationReady':False,'requirements':{'diameterMM':305,'terrainExaggeration':25,'visitRadiusMiles':50,'budgetUSD':[1500,4500]},'checks':{'geometrySoftwareTests':16,'deviceSoftwareTests':14,'browserChecks':json.loads((checks/'browser-checks.json').read_text())['checks'],'benchPCB':json.loads((ROOT/'electronics/bench-release/validation.json').read_text()),'manufacturingMeshesChecked':json.loads((checks/'saved-file-checks.json').read_text())['manufacturingMeshesChecked'],'unintendedIntersectionsInCheckedGroupPairs':sum(len(x['intersections']) for x in json.loads((checks/'assembly-intersections.json').read_text()))},'holds':['Full matrix PCB routing incomplete; 122–149 unconnected items per type plus reported violations; no fabrication outputs released','Full-system electrical schematic/ERC, selected LED and module datasheets/pinout/current and real hardware operation unqualified','Real resin/paint light transmission, cell leakage and terrain brightness untested','Printed joint fit/retention, drilled spoke end strength, creep, full-panel warpage and base electronics retention untested','South-polar support tiles excluded; coverage redesign needed','Measured power/thermal/fault/persistence commissioning not performed','Supplier quotations not received; $4500 is an allocation, not a verified purchase price','Cage octant 04 STEP round-trip invalid; checked STL provided instead'],'simulationScope':'Linear rigid-joint beams, two-node heat balance, geometric/sensitivity optics; not measured hardware certification'}
assert status['checks']['unintendedIntersectionsInCheckedGroupPairs']==0
(checks/'release-status.json').write_text(json.dumps(status,indent=2));(OUT/'engineering-checks').mkdir(exist_ok=True)
(OUT/'engineering-checks/release-status.json').write_text(json.dumps(status,indent=2))
files={}
def add(p,name=None):
 if p.is_file():files[name or str(p.relative_to(ROOT))]=p
for folder in ['preview','cad/design','cad/data','docs','firmware','tests','tools','engineering','electronics/reference','electronics/bench-release']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.kicad_prl'):add(p)
for folder in ['cad','electronics']:
 for p in (ROOT/folder).glob('*.py'):add(p)
for name in ['README.md','package.json','package-lock.json','.gitignore']:add(ROOT/name)
for p in CAD.iterdir():
 if p.suffix in ('.stl','.json') or p.suffix=='.step' and not p.name.startswith('cage-octant'):add(p)
for p in (ROOT/'artifacts/assembly').glob('*'):add(p,'assembly/'+p.name)
for p in (ROOT/'electronics/generated').iterdir():
 if p.name.startswith('led-tile-') and p.suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru','.json','.csv'):add(p,'electronics/matrix-candidates-HOLD/'+p.name)
for p in (ROOT/'electronics/generated/Globe.pretty').glob('*'):add(p,'electronics/matrix-candidates-HOLD/Globe.pretty/'+p.name)
add(ROOT/'electronics/generated/fp-lib-table','electronics/matrix-candidates-HOLD/fp-lib-table')
add(ROOT/'electronics/generated/component-envelopes.json','electronics/generated/component-envelopes.json')
# Keep the channel tables in their generator paths for regenerating the prototype viewer.
for p in (ROOT/'electronics/generated').glob('*channels.csv'):add(p)
for p in (OUT/'engineering-assets').glob('*'):add(p,'engineering-assets/'+p.name)
add(OUT/'engineering-report.pdf','engineering-report.pdf');add(OUT/'engineering-report.html','engineering-report.html')
for name in ['engineering.html','index.html','structure.html']:add(OUT/name,name)
start='''Travel Globe A0 — START HERE

Open engineering-report.pdf or docs/engineering-report.md first.
For the included CAD viewer, serve this extracted folder with `python3 -m http.server 4173` and open http://localhost:4173/engineering.html. Mesh fetches need a local server.
The main globe is an engineering prototype, NOT a fabrication release.
Start with the ten-cell optical qualification assembly. Supplier review of the candidate LED and real optical/mechanical tests are still required.

cad/generated: checked STLs plus analytic STEP for stand/metal/cradle/board outlines.
cad/*.py + cad/design: editable parametric definitions, in millimetres.
assembly: actual CAD meshes for the web viewer.
electronics/bench-release: routed 10-cell board, Gerbers/drills/BOM/placement/validation.
electronics/matrix-candidates-HOLD: unfinished full-globe board candidates. DO NOT ORDER.
engineering/release: calculated results, release holds, BOM, wiring and test worksheets.
firmware/install: host/Pico installation and simulation instructions.

No complete globe has been fabricated, electrically commissioned or optically tested.
Large checked cage STEP exports are separate downloads. Octant 04 failed STEP validation; its closed STL is provided.
All simulations have stated assumptions and are not a physical certification.
Third-party attributions/licenses are in docs and electronics/reference.
'''
def archive(path,entries,extra=None):
 manifest={}
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  z.writestr('START-HERE.txt',start if extra is None else extra)
  for name,p in sorted(entries.items()):z.write(p,name);manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
  z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 print(path.name,len(entries),'files',round(path.stat().st_size/1e6,2),'MB',flush=True)
archive(OUT/'engineering-package.zip',files)
small={}
for name in ['prototype-shell-vancouver-25x.stl','prototype-shell-himalaya-25x.stl','prototype-cradle-type-02.stl','prototype-cradle-type-02.step','baffle-type-02.stl','magnet-seat-M2-4mm.stl','magnet-fit-coupon.stl','prototype.json']:
 small['print/'+name]=CAD/name
for folder in ['electronics/bench-release','firmware/ten-cell-bench','electronics/reference','docs/third-party']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:small[str(p.relative_to(ROOT))]=p
for name in ['engineering-report.pdf','engineering-report.html']:
 if (OUT/name).exists():small[name]=OUT/name
for p in (OUT/'engineering-assets').glob('*'):small['engineering-assets/'+p.name]=p
for name in ['acceptance-worksheet.csv','optical-bench-selection.json']:small['checks/'+name]=checks/name
archive(OUT/'optical-prototype-A0.zip',small)
stepout=OUT/'cad-step';stepout.mkdir(exist_ok=True)
for entry in json.loads((CAD/'cad-audit-frame-step.json').read_text()):
 if not entry.get('valid'):continue
 p=CAD/(entry['part']+'.step');archive(stepout/(p.name+'.zip'),{p.name:p},'Checked faceted STEP boundary, millimetres. Editable parameters are in the main engineering source package.\n')
downloads=[]
for p in [OUT/'engineering-package.zip',OUT/'optical-prototype-A0.zip',OUT/'engineering-report.pdf',*sorted(stepout.glob('*.zip'))]:
 if p.exists():downloads.append({'file':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'engineering-downloads.json').write_text(json.dumps({'release':'A0','downloads':downloads},indent=2))
