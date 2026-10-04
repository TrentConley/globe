"""Part counts, harness schedule, mass estimate and budget ceilings from the CAD."""
from pathlib import Path
import json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'engineering/release';CAD=ROOT/'cad/generated';D=json.loads((CAD/'layout.json').read_text());counts={k:sum(t['type']==k and t['populated'] for t in D['tiles']) for k in range(6)}
def write(name,rows):
 with (OUT/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rows=[]
for t in D['tiles']:
 if not t['populated']:continue
 rows.append({'tile':t['id'],'printed_label':f"S{t['sector']:02}-T{t['id']%16:02}",'sector':t['sector'],'board_type':t['type'],'mux_channel':t['bus'],'i2c_address':hex(t['address']),'bridge_exactly_one':f"JP{t['id']%4+1}",'leds':len(t['leds']),'baffle':f"baffle-type-{t['type']:02}.stl"})
write('tile-schedule.csv',rows)
controllers=json.loads((CAD/'controller-mounts.json').read_text());centers={c['sector']:np.array(c['center']) for c in controllers};remaining=set(centers);order=[];p=np.array([6,0,-140])
while remaining:
 sid=min(remaining,key=lambda s:np.linalg.norm(centers[s]-p));order.append(sid);remaining.remove(sid);p=centers[sid]
rows=[];p=np.array([6,0,-140])
for index,sid in enumerate(order):
 q=centers[sid];length=math.ceil((np.linalg.norm(q-p)*1.3+25)/10)*10
 rows.append({'chain_position':index+1,'sector':sid,'previous':'base' if index==0 else order[index-1],'rs485_cut_allowance_mm':length,'termination_120ohm':index==19,'power_fuse_branch':'A' if index<10 else 'B','power_branch_750mA':True,'local_input_PTC_mA':350});p=q
write('sector-harness.csv',rows)
rows=[]
for c in controllers:
 for bus in range(4):
  ts=[t for t in D['tiles'] if t['populated'] and t['sector']==c['sector'] and t['bus']==bus]
  p=np.array(c['center']);ids=[];length=0
  while ts:
   t=min(ts,key=lambda t:np.linalg.norm(np.array(t['center'])-p));d=np.linalg.norm(np.array(t['center'])-p);length+=d*1.2+15;ids.append(t['id']);p=np.array(t['center']);ts.remove(t)
  if ids:rows.append({'sector':c['sector'],'mux_channel':bus,'tile_order':';'.join(map(str,ids)),'approx_total_cable_mm':math.ceil(length),'pullups':'one pair 2.2k to local 3V3','bus_clock_hz':100000,'maximum_target_cable_mm':350})
write('i2c-harness.csv',rows)
# Procurement caps: budget allocation, not fabricated supplier quotations.
allowances=[('226 complete LED tile assemblies',1700,'Includes LEDs, matrix ICs, PCB fabrication and SMT; supplier quote required'),('All printed structural and optical parts',1000,'Batch print PA12 frame/base/carriers and clear/black resin optical parts'),('20 sector controller assemblies',500,'Pico, mux, 3V3 RS485, buck, sensor, diode, PTC, perfboard, passives'),('Base controller, protection and supply',170,'Pi, endurance SD, 5V buck, FRAM, INA260, relay, external certified 12V supply'),('Metal, magnets, fasteners and wiring',330,'Cut/drill aluminum and steel; precrimp cables, M2/M3 hardware, magnets'),('Optical qualification prototype',250,'Small PCB batch, print samples, Pico and finish consumables'),('Contingency',550,'Shipping, tax, failed samples and rework')]
write('budget-allowances.csv',[{'category':a,'maximum_allowance_USD':b,'basis':c,'supplier_quote_received':False} for a,b,c in allowances]);assert sum(b for _,b,_ in allowances)==4500
# Parts and processes. Machine-generated geometry is a nominal manufacturing definition.
parts=[]
for path in sorted(CAD.glob('*audit*.json')):
 try:data=json.loads(path.read_text())
 except ValueError:continue
 if not isinstance(data,list):continue
 for item in data:
  if not isinstance(item,dict) or 'part' not in item or 'material' not in item:continue
  name=item['part']
  if any(x['part']==name for x in parts):continue
  qty=counts[int(name[-2:])] if name.startswith('baffle-type-') else 60 if name=='magnet-seat-M2-4mm' else 3*D['summary']['populatedTiles']-sum(D['tiles'][a['tile']]['populated'] for a in D['anchors'])+sum(not D['tiles'][a['tile']]['populated'] for a in D['anchors']) if name=='pcb-head-spacer-M2' else 1
  material=item['material'];process='SLS/MJF PA12' if material=='PA12' or material.startswith('PA12;') else 'machined purchased metal' if 'aluminum' in material or 'steel' in material else 'SLA/DLP resin' if 'resin' in material else 'PCB / reference geometry'
  parts.append({'part':name,'quantity':qty,'material':material,'process':process,'volume_each_mm3':round(item.get('volume_mm3',0),3),'STL':(CAD/(name+'.stl')).exists(),'STEP':(CAD/(name+'.step')).exists()})
write('parts-manifest.csv',parts)
# Supported mass, using CAD for polymers/boards/metal and explicit electronics/wiring allowances.
mass=[]
for family,prefix,density in [('cage','cage-octant-',1.01e-6),('terrain','terrain-shell-',1.15e-6),('baffles','baffle-type-',1.15e-6),('carriers','controller-carrier-',1.01e-6),('spokes','spoke-',2.7e-6),('spine','spine-',2.7e-6),('hubs','hub-',1.01e-6),('magnet seats','magnet-seat-',1.01e-6),('head spacers','pcb-head-',1.01e-6)]:
 mass.append({'item':family,'kg':sum(p['volume_each_mm3']*p['quantity']*density for p in parts if p['part'].startswith(prefix)),'basis':'CAD volume × assumed density'})
audit=json.loads((CAD/'cad-audit-tiles.json').read_text());mass.append({'item':'tile FR4','kg':sum(p['volume_mm3']*counts[int(p['part'][-2:])]*1.85e-6 for p in audit),'basis':'1 mm FR4; density 1.85 g/cm3'})
for item,kg,basis in [('tile components and solder',D['summary']['populatedTiles']*.0013,'1.3 g allowance per tile'),('complete sector electronics',.4,'20 g per carrier including perfboard'),('magnets and screws',.25,'120 magnets, PCB screws/nuts, split joints and clamps'),('internal harness',.25,'Crimp leads, trunk, ties and slack')]:mass.append({'item':item,'kg':kg,'basis':basis})
(OUT/'mass-estimate.json').write_text(json.dumps({'items':mass,'supportedMassEstimateKg':sum(x['kg'] for x in mass),'structuralScreeningMassKg':3.5,'status':'Estimate, not a measured assembled mass'},indent=2))
print('BOM',D['summary']['populatedTiles'],'tiles',D['summary']['leds'],'LEDs; budget cap $4500; estimated supported mass',sum(x['kg'] for x in mass))
