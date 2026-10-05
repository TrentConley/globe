"""Sample A1 supplier review archives, with checked geometry and runtime evidence."""
from pathlib import Path
import csv,json,hashlib,zipfile,html,re
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';CAD=ROOT/'cad/generated';BENCH=ROOT/'electronics/bench-release';REPORT=ROOT/'engineering/release';OUT.mkdir(exist_ok=True)
parts=[('prototype-shell-vancouver-25x.stl',2,'Request Formlabs Clear Resin V5','One clear control and one tint sample; same batch; supplier confirmation pending'),('prototype-shell-himalaya-25x.stl',2,'Same clear resin and process','One clear control and one tint sample; same batch'),('sample-baffle-type-02-clearance.stl',2,'Request Formlabs Black Resin V5','A1 mount clearance; 0.4 mm walls; supplier confirmation and opacity test pending'),('sample-finish-thickness-coupon.stl',2,'Same clear resin as shells','1 / 2 / 3 / 4.75 mm strips; clear control and coating trial'),('prototype-cradle-type-02.stl',1,'PA12 SLS/MJF preferred','Rigid bench fixture; quote alternative separately'),('magnet-seat-M2-4mm.stl',3,'PA12 SLS/MJF','Protect counterseats, pockets and seating rims'),('magnet-fit-coupon.stl',1,'Same process/material as magnet seats','Fit qualification')]
validated={r['file']:r for r in json.loads((REPORT/'manufacturing-mesh-checks.json').read_text())}
geometry=json.loads((REPORT/'sample-geometry-checks.json').read_text())
validated.update({r['file']:r for r in geometry['meshChecks']})
fit=json.loads((REPORT/'sample-fit-checks.json').read_text())
for name,sha in fit['meshSHA256'].items():assert hashlib.sha256((CAD/name).read_bytes()).hexdigest()==sha
firmware=json.loads((REPORT/'sample-firmware-checks.json').read_text())
assert hashlib.sha256((ROOT/'firmware/ten-cell-bench/main.py').read_bytes()).hexdigest()==firmware['firmwareSHA256']
assert hashlib.sha256((ROOT/'firmware/ten-cell-bench/patterns.json').read_bytes()).hexdigest()==firmware['patternsSHA256']
checks=[]
for name,qty,material,note in parts:
 p=CAD/name;sha=hashlib.sha256(p.read_bytes()).hexdigest();assert validated[name]['sha256']==sha;assert validated[name]['watertight'] and validated[name]['connectedSolids']==1;checks.append({'file':name,'sha256':sha,'quantity':qty})
r=json.loads((BENCH/'optical-bench-10-drc.json').read_text());assert not r['violations'] and not r['unconnected_items'];expected=json.loads((REPORT/'saved-file-checks.json').read_text());assert hashlib.sha256((BENCH/'optical-bench-10.kicad_pcb').read_bytes()).hexdigest()==expected['benchPCBsha256']
assert fit['pcbSHA256']==expected['benchPCBsha256']
import io
s=io.StringIO();w=csv.writer(s);w.writerow(['file','quantity','material_process','units','scale','notes'])
for name,qty,material,note in parts:w.writerow([name,qty,material,'mm','100%',note])
print_request='''PRINT QUOTE REQUEST — Travel globe optical sample A1

Please quote the quantities in print-order.csv, with shipping separate. Files are millimetres at 100% scale. This is an engineering test, not a volume order.

Four shells and two stepped witness coupons: request Formlabs Clear Resin V5, one resin/batch and identical post-processing. If unavailable, identify an exact alternative product for separate review. Minimum shell wall is 1 mm; terrain locally thickens it. Witness strips are 1, 2, 3 and 4.75 mm. Please state resin product, optical clarity, UV/yellowing information, orientation, cure and dimensional tolerance. Deliver fully washed/cured, uncoated and undyed.

Two black cell grids: request Formlabs Black Resin V5 or separately identify an alternative. 0.4 mm walls and approximately 1.6 mm openings. Please confirm those features are printable and can be cleaned completely. A1 uses 7.6 mm boss apertures. Black color alone is not evidence of optical opacity; that will be tested. Do not thicken the walls automatically.

Proposed target: +/-0.10 mm or better on mating optical faces. Nominal minimum grid/shell gap is 0.349 mm; no physical fit is yet qualified. State expected tolerance and warpage instead of assuming this target is feasible. Please complete supplier-review.csv and return material technical data sheets. The proposed X-19 Smoke/XF-86 finish is to be tested on the supplied coupons; compatibility is not established.

FABRICATION HOLD: an assumed 0.20 mm-high envelope over the LED copper pads leaves only 0.0127 mm to the grid. This is not a feasible tolerance specification. Actual assembled package/fillet dimensions and positioning tolerances must be reviewed, with local underside grid relief added if needed, before fabrication. The 0.349 mm shell gap does not resolve this separate solder-fit issue.

Cradle/seats/magnet-fit coupon: PA12 preferred, with the seats and magnet-fit coupon printed by the same process. The stepped optical witness coupons remain clear resin. Quote a rigid cradle alternative separately if it saves a minimum charge.

Flag unsupported features before fabrication. Do not rescale, hollow, thicken or modify the geometry without review. Agree support placement to protect the smooth shell interior, seating faces, magnet pockets and cell openings. No sanding/polishing of optical faces without agreement. State any dimensional correction separately.

No order is authorized by this RFQ. The requester will review the quote and manufacturing comments before purchasing.
'''
pcb_request='''PCB ASSEMBLY QUOTE REQUEST — Ten-cell optical bench (sample A1 package, A0 PCB unchanged)

Please quote the minimum economical bare-board quantity and TWO fully assembled boards, with shipping separate. This is the passive ten-channel optical test board, not a full-globe matrix tile.

2 layers; 1.0 mm FR4; nominal 35 µm copper; black soldermask preferred; ordinary lead-free finish. Use the supplied outline, separate PTH/NPTH drills, BOM and placement CSV. Ten LEDs are front-side; ten 1 kohm resistors are rear-side. P0–P9 and GND are wire pads, not parts to populate. Minimum design track 0.15 mm, copper clearance 0.25 mm, via drill 0.30 mm. The checked KiCad project and embedded footprints are included.

The LED APHHS1005SYCK is a candidate. Please verify its current manufacturer datasheet, 1005 metric/0402 imperial dimensions, pad-1 cathode assignment, rotation and amber/yellow color. This is a generic footprint, not a qualified manufacturer-specific land pattern: pads 0.59 x 0.64 mm, centers +/-0.485 mm. See QUALIFICATION.md and complete supplier-review.csv with drawing revision, cathode/tape orientation, package maximums, land pattern, emission direction, electrical/thermal limits, sourcing/stock and reflow profile. Identify any substitute and provide its datasheet for review before fitting. The resistor candidate is RC0603FR-071KL, 1 kohm 1%, 0603 imperial.

Please also provide the expected assembled LED and solder fillet envelope (including package underside, paste height and placement tolerance). The optical grid begins 0.10 mm above the board and an assumed 0.20 mm pad-height envelope has only 0.0127 mm side clearance. Grid relief may be needed before fabrication; this is an open design hold, not a request to meet a 0.013 mm fit tolerance.

Please perform continuity/short and polarity inspection and individual LED operation through the fitted 1 kohm resistors, using a current-limited 3.3 V logic supply. The board has NO 12 V input. Provide the inspection/test result and component traceability/datasheets. Report any DFM issues rather than altering geometry without review.

Only this routed optical-bench-10 board is in scope. Full-globe matrix layouts are unfinished and are not included. No order is authorized by this RFQ; the requester will review the quote first.
'''
def makezip(name,entries,texts):
 manifest={}
 with zipfile.ZipFile(OUT/name,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
  for dest,p in entries.items():data=p.read_bytes();z.writestr(dest,data);manifest[dest]=hashlib.sha256(data).hexdigest()
  for dest,data in texts.items():z.writestr(dest,data);manifest[dest]=hashlib.sha256(data.encode()).hexdigest()
  z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(OUT/name) as z:
  assert z.testzip() is None
  for dest,sha in manifest.items():assert hashlib.sha256(z.read(dest)).hexdigest()==sha
 return {'file':name,'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()}
def csvtext(headers,rows):
 s=io.StringIO();w=csv.writer(s);w.writerow(headers);w.writerows(rows);return s.getvalue()
review_items=[('LED','Manufacturer PDF revision and package maximum dimensions'),('LED','Land pattern matches supplied copper pads'),('LED','Cathode mark, tape orientation and placement rotations'),('LED','Emission direction, wavelength, current/Vf ratings and reflow'),('LED','Distributor, available quantity, lead time and quote date'),('Resistor','Exact part, tolerance, power rating and data sheet'),('Pico','RP2040 per-pin and aggregate GPIO ratings checked against load'),('Printer','Exact clear/black resin and PA12 products and batch'),('Printer','0.4 mm grid walls and 1.6 mm cells printable and cleanable'),('Printer','Mating-face tolerance and warpage; proposed target +/-0.10 mm'),('Printer','Support placement, wash/cure and protected optical/mating faces'),('Printer','1 mm shell wall and magnet-pocket fit'),('Finish','Current X-19/X-20A/XF-86 instructions and resin compatibility advice')]
review_items.insert(5,('Solder fit HOLD','Actual assembled LED/fillet envelope and positioning tolerance; revise grid relief if required; assumed 0.20 mm pad height leaves 0.0127 mm side gap'))
review=csvtext(['category','confirmation_needed','supplier_or_reviewer','response','evidence_file_or_URL','date','status'],[(a,b,'','','','','OPEN') for a,b in review_items])
tests=['As-received dimensions and fit','Uncoated shell transmission','Coupon 1/2/3/4.75 mm transmission','X-19 one/two coats and XF-86 comparison','Coupon handling and adhesion after cure and seven days','Bare-board ten-channel walk and current','Vancouver/Seattle/both recognition','Single-cell neighbor leakage','Thick-terrain comparison','20 removal/refit cycles','One-hour current and temperature','Saved pattern after USB power cycle']
results_csv=csvtext(['test','sample_ID','date','conditions_and_settings','measured_result','photo_or_evidence_file','pass_fail','notes'],[(t,'','','','','','NOT RUN','') for t in tests])
common={'TEST-PLAN.md':ROOT/'docs/sample-plan.md','QUALIFICATION.md':ROOT/'docs/sample-qualification.md'}
for name in ['sample-geometry-checks.json','sample-fit-checks.json','sample-firmware-checks.json']:common['evidence/'+name]=REPORT/name
if (OUT/'sample-test-plan.pdf').exists():common['TEST-PLAN.pdf']=OUT/'sample-test-plan.pdf'
common_texts={'supplier-review.csv':review,'sample-results.csv':results_csv}
entries={'print/'+name:CAD/name for name,*_ in parts};entries.update(common)
for name in ['elevation-data-license.md','elevation.md','sources.md']:entries['licenses/'+name]=ROOT/'docs'/name
rows=[makezip('sample-print-request.zip',entries,{**common_texts,'START-HERE-RFQ.txt':print_request,'print-order.csv':s.getvalue()})]
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
entries.update(common)
wiring='PCB_pad,Pico_GPIO,Pico_physical_header_pin\n'+''.join(f'{i},GP{i},{pin}\n' for i,pin in enumerate([1,2,4,5,6,7,9,10,11,12]))+'GND,GND,3\n'
rows.append(makezip('sample-pcb-request.zip',entries,{**common_texts,'START-HERE-RFQ.txt':pcb_request,'firmware/wiring.csv':wiring}))
record={'sourceRelease':'sample-A1; full globe A0 unchanged','scope':'Revised sample baffle clearance, new finish coupon, hardened bench firmware; PCB unchanged','physicalTested':False,'supplierConfirmed':False,'procurementStatus':'Fabrication hold: solder/grid clearance, LED data sheet, stock, printer capability/material and finish compatibility remain open','solderFitHold':fit['fabricationHold'],'meshChecks':checks,'benchPCBsha256':expected['benchPCBsha256'],'drcViolations':0,'unconnected':0,'firmwareSHA256':firmware['firmwareSHA256'],'downloads':rows}
(OUT/'sample-request-checks.json').write_text(json.dumps(record,indent=2));(REPORT/'sample-request-checks.json').write_text(json.dumps(record,indent=2))
css=re.search(r'<style>(.*?)</style>',(OUT/'engineering-report.html').read_text(),re.S).group(1)
for name,title in [('sample-plan','Manufacture the first sample'),('sample-qualification','Component and material review')]:
 source=(ROOT/'docs'/f'{name}.md').read_text();rendered=markdown.markdown(source,extensions=['tables','fenced_code']).replace('<table>','<div class="table-scroll"><table>').replace('</table>','</table></div>')
 page=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Travel globe — {html.escape(title)}</title><style>{css}</style></head><body><header><a href="index.html">Travel simulator</a><a href="engineering.html">Actual CAD</a><a href="sample-plan.html">Sample plan</a><a href="sample-qualification.html">Material review</a><a href="sample-test-plan.pdf">Sample plan PDF</a></header><main>{rendered}<footer>Sample A1 digital review. No supplier order or physical test has been performed.</footer></main></body></html>'
 (OUT/f'{name}.html').write_text(page)
print(json.dumps(record,indent=2))
