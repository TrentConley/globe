"""Supplier-specific request archives using the previously checked A0 parts."""
from pathlib import Path
import csv,json,hashlib,zipfile,html,re
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';CAD=ROOT/'cad/generated';BENCH=ROOT/'electronics/bench-release';REPORT=ROOT/'engineering/release';OUT.mkdir(exist_ok=True)
parts=[('prototype-shell-vancouver-25x.stl',2,'Clear untinted SLA/DLP resin','One clear control and one tint sample; same batch'),('prototype-shell-himalaya-25x.stl',2,'Same clear resin and process','One clear control and one tint sample; same batch'),('baffle-type-02.stl',2,'Opaque black SLA/DLP resin','0.4 mm walls, clean all cells; opacity must be tested'),('prototype-cradle-type-02.stl',1,'PA12 SLS/MJF preferred','Rigid bench fixture; quote alternative separately'),('magnet-seat-M2-4mm.stl',3,'PA12 SLS/MJF','Protect counterseats, pockets and seating rims'),('magnet-fit-coupon.stl',1,'Same process/material as magnet seats','Fit qualification')]
validated={r['file']:r for r in json.loads((REPORT/'manufacturing-mesh-checks.json').read_text())}
checks=[]
for name,qty,material,note in parts:
 p=CAD/name;sha=hashlib.sha256(p.read_bytes()).hexdigest();assert validated[name]['sha256']==sha;assert validated[name]['watertight'] and validated[name]['connectedSolids']==1;checks.append({'file':name,'sha256':sha,'quantity':qty})
r=json.loads((BENCH/'optical-bench-10-drc.json').read_text());assert not r['violations'] and not r['unconnected_items'];expected=json.loads((REPORT/'saved-file-checks.json').read_text());assert hashlib.sha256((BENCH/'optical-bench-10.kicad_pcb').read_bytes()).hexdigest()==expected['benchPCBsha256']
import io
s=io.StringIO();w=csv.writer(s);w.writerow(['file','quantity','material_process','units','scale','notes'])
for name,qty,material,note in parts:w.writerow([name,qty,material,'mm','100%',note])
print_request='''PRINT QUOTE REQUEST — Travel globe optical sample A0

Please quote the quantities in print-order.csv, with shipping separate. Files are millimetres at 100% scale. This is an engineering test, not a volume order.

Four shells: clear/untinted SLA or DLP, one resin/batch and identical post-processing. Minimum shell wall is 1 mm; terrain locally thickens it. Please state resin product, optical clarity, UV/yellowing information, orientation, cure and dimensional tolerance. Deliver fully washed/cured, uncoated and undyed.

Two black cell grids: 0.4 mm walls and approximately 1.6 mm openings. Please confirm those features are printable and can be cleaned completely. Black color alone is not evidence of optical opacity; that will be tested. Do not thicken the walls automatically.

Cradle/seats/coupon: PA12 preferred, with the seat and coupon printed by the same process. Quote a rigid cradle alternative separately if it saves a minimum charge.

Flag unsupported features before fabrication. Do not rescale, hollow, thicken or modify the geometry without review. Agree support placement to protect the smooth shell interior, seating faces, magnet pockets and cell openings. No sanding/polishing of optical faces without agreement. State any dimensional correction separately.

No order is authorized by this RFQ. The requester will review the quote and manufacturing comments before purchasing.
'''
pcb_request='''PCB ASSEMBLY QUOTE REQUEST — Ten-cell optical bench A0

Please quote the minimum economical bare-board quantity and TWO fully assembled boards, with shipping separate. This is the passive ten-channel optical test board, not a full-globe matrix tile.

2 layers; 1.0 mm FR4; nominal 35 µm copper; black soldermask preferred; ordinary lead-free finish. Use the supplied outline, separate PTH/NPTH drills, BOM and placement CSV. Ten LEDs are front-side; ten 1 kohm resistors are rear-side. P0–P9 and GND are wire pads, not parts to populate. Minimum design track 0.15 mm, copper clearance 0.25 mm, via drill 0.30 mm. The checked KiCad project and embedded footprints are included.

The LED APHHS1005SYCK is a candidate. Please verify its current manufacturer datasheet, 1005 metric/0402 imperial dimensions, pad-1 cathode assignment, rotation and amber/yellow color. Identify any substitute and provide its datasheet for review before fitting. The resistor candidate is RC0603FR-071KL, 1 kohm 1%, 0603 imperial.

Please perform continuity/short and polarity inspection and individual LED operation through the fitted 1 kohm resistors, using a current-limited 3.3 V logic supply. The board has NO 12 V input. Provide the inspection/test result and component traceability/datasheets. Report any DFM issues rather than altering geometry without review.

Only this routed optical-bench-10 board is in scope. Full-globe matrix layouts are unfinished and are not included. No order is authorized by this RFQ; the requester will review the quote first.
'''
def makezip(name,entries,texts):
 manifest={}
 with zipfile.ZipFile(OUT/name,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for dest,p in entries.items():data=p.read_bytes();z.writestr(dest,data);manifest[dest]=hashlib.sha256(data).hexdigest()
  for dest,data in texts.items():z.writestr(dest,data);manifest[dest]=hashlib.sha256(data.encode()).hexdigest()
  z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(OUT/name) as z:assert z.testzip() is None
 return {'file':name,'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()}
entries={'print/'+name:CAD/name for name,*_ in parts};entries['TEST-PLAN.md']=ROOT/'docs/sample-plan.md'
if (OUT/'sample-test-plan.pdf').exists():entries['TEST-PLAN.pdf']=OUT/'sample-test-plan.pdf'
for name in ['elevation-data-license.md','elevation.md','sources.md']:entries['licenses/'+name]=ROOT/'docs'/name
rows=[makezip('sample-print-request.zip',entries,{'START-HERE-RFQ.txt':print_request,'print-order.csv':s.getvalue()})]
entries={str(p.relative_to(BENCH)):p for p in BENCH.rglob('*') if p.is_file() and p.suffix not in ('.kicad_prl',)}
# Conventional bare-board upload, without PDFs, firmware or project files.
with zipfile.ZipFile(OUT/'sample-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((BENCH/'gerbers').iterdir()):
  if p.suffix in ('.gtl','.gbl','.gtp','.gbp','.gto','.gbo','.gts','.gbs','.gm1','.drl'):z.write(p,p.name)
entries['fabrication-gerbers.zip']=OUT/'sample-gerbers.zip'
for p in (ROOT/'firmware/ten-cell-bench').glob('*'):
 if p.is_file():entries['firmware/'+p.name]=p
for p in (ROOT/'docs/third-party').glob('*'):
 if p.is_file():entries['licenses/'+p.name]=p
for name in ['adafruit-readme.md','adafruit-license.txt']:entries['licenses/'+name]=ROOT/'electronics/reference'/name
entries['TEST-PLAN.md']=ROOT/'docs/sample-plan.md'
if (OUT/'sample-test-plan.pdf').exists():entries['TEST-PLAN.pdf']=OUT/'sample-test-plan.pdf'
wiring='PCB_pad,Pico_GPIO,Pico_physical_header_pin\n'+''.join(f'{i},GP{i},{pin}\n' for i,pin in enumerate([1,2,4,5,6,7,9,10,11,12]))+'GND,GND,3\n'
rows.append(makezip('sample-pcb-request.zip',entries,{'START-HERE-RFQ.txt':pcb_request,'firmware/wiring.csv':wiring}))
record={'sourceRelease':'A0','scope':'Ordering and test plan; manufacturing geometry and electronics unchanged','physicalTested':False,'meshChecks':checks,'benchPCBsha256':expected['benchPCBsha256'],'drcViolations':0,'unconnected':0,'downloads':rows}
(OUT/'sample-request-checks.json').write_text(json.dumps(record,indent=2));(REPORT/'sample-request-checks.json').write_text(json.dumps(record,indent=2))
source=(ROOT/'docs/sample-plan.md').read_text();rendered=markdown.markdown(source,extensions=['tables','fenced_code']).replace('<table>','<div class="table-scroll"><table>').replace('</table>','</table></div>')
css=re.search(r'<style>(.*?)</style>',(OUT/'engineering-report.html').read_text(),re.S).group(1)
page=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Travel globe — manufacture the first sample</title><style>{css}</style></head><body><header><a href="index.html">Travel simulator</a><a href="engineering.html">Actual CAD</a><a href="engineering-report.html">Engineering report</a><a href="sample-test-plan.pdf">Sample plan PDF</a></header><main>{rendered}<footer>Prepared from the checked A0 digital design. No supplier order or physical test has been performed.</footer></main></body></html>'
(OUT/'sample-plan.html').write_text(page)
print(json.dumps(record,indent=2))
