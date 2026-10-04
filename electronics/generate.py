"""KiCad 9 generator. Run with /usr/bin/python3 (pcbnew interpreter).
Derives physical LED placement and channel mapping from the mechanical manifest.
Driver pad map/land pattern follows the published Adafruit IS31FL3741 reference.
"""
from pathlib import Path
import json,xml.etree.ElementTree as ET,math,csv
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated';OUT.mkdir(exist_ok=True)
D=json.loads((ROOT/'cad/generated/layout.json').read_text())
LIB=Path('/usr/share/kicad/footprints')
REF=ROOT/'electronics/reference/adafruit-matrix.sch'
R=ET.parse(REF).getroot();device=R.find('.//deviceset[@name="IS31FL3741"]/devices/device');PIN={pad:c.attrib['pin'] for c in device.findall('.//connect') for pad in c.attrib['pad'].split()}
PKG=R.find('.//package[@name="QFN60_7MM"]')
mm=pcb.FromMM

def layer_set(ids):
 s=pcb.LSET()
 for i in ids:s.AddLayer(i)
 return s

def pos(x,y):return pcb.VECTOR2I(mm(x),mm(y))
def clean_library(library,name):
 source=(LIB/(library+'.pretty')/(name+'.kicad_mod')).read_text();remove=[]
 import re
 for match in re.finditer(r'\((?:fp_line|fp_arc|fp_poly|fp_circle|fp_text)\s',source):
  start=match.start();level=0;quoted=False;escape=False
  for k in range(start,len(source)):
   c=source[k]
   if escape:escape=False;continue
   if c=='\\' and quoted:escape=True;continue
   if c=='"':quoted=not quoted
   if not quoted:
    if c=='(':level+=1
    elif c==')':
     level-=1
     if level==0:break
  block=source[start:k+1]
  if any('"'+layer+'"' in block for layer in ['F.SilkS','B.SilkS']) or (library=='MountingHole' and any('"'+layer+'"' in block for layer in ['F.CrtYd','B.CrtYd'])):remove.append((start,k+1))
 for a,z in reversed(remove):source=source[:a]+source[z:]
 custom=library+'__'+name;source=source.replace('(footprint "'+name+'"','(footprint "'+custom+'"',1)
 path=OUT/'Globe.pretty';path.mkdir(exist_ok=True);(path/(custom+'.kicad_mod')).write_text(source)
 return path,custom

def footprint(board,library,name,reference,value,x,y,back=False):
 libpath,custom=clean_library(library,name);f=pcb.FootprintLoad(str(libpath),custom);f.SetFPID(pcb.LIB_ID('Globe',custom));f.SetReference(reference);f.SetValue(value);f.SetPosition(pos(x,y));board.Add(f)
 if back:f.Flip(pos(x,y),False)
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 return f

def net(board,name,nets):
 if name not in nets:
  n=pcb.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
 return nets[name]
def pads(f,mapping):
 for p in f.Pads():
  if p.GetNumber() in mapping:p.SetNet(mapping[p.GetNumber()])
def custom_driver(board,nets,x,y):
 f=pcb.FOOTPRINT(board);f.SetReference('U1');f.SetValue('IS31FL3741-QFLS4');f.SetFPID(pcb.LIB_ID('Globe','IS31FL3741_QFN60_7mm_EP5.1'));f.SetPosition(pos(x,y));board.Add(f)
 for s in PKG.findall('smd'):
  p=pcb.PAD(f);number=s.attrib['name'];p.SetNumber('61' if number=='THERMAL' else number);p.SetAttribute(pcb.PAD_ATTRIB_SMD);p.SetShape(pcb.PAD_SHAPE_RECT);p.SetSize(pos(float(s.attrib['dx']),float(s.attrib['dy'])));p.SetPosition(pos(x+float(s.attrib['x']),y-float(s.attrib['y'])));p.SetLayerSet(layer_set([pcb.F_Cu,pcb.F_Paste,pcb.F_Mask]));
  # Eagle's pad rotation changes orientation of its dx/dy land.
  angle=float(s.attrib.get('rot','R0').replace('R',''));p.SetOrientationDegrees(-angle)
  pname=PIN[number];nname={'AVCC':'3V3','PVCC':'3V3','GND':'GND','R_EXT':'ISET','ADDR':'ADDR'}.get(pname,pname);p.SetNet(net(board,nname,nets));f.Add(p)
 # Remove full-area paste on the exposed pad; use a windowed paste pattern instead.
 for p in f.Pads():
  if p.GetNumber()=='61':p.SetLayerSet(layer_set([pcb.F_Cu,pcb.F_Mask]))
 for dx in [-1.6,0,1.6]:
  for dy in [-1.6,0,1.6]:
   p=pcb.PAD(f);p.SetAttribute(pcb.PAD_ATTRIB_SMD);p.SetShape(pcb.PAD_SHAPE_RECT);p.SetSize(pos(1.2,1.2));p.SetPosition(pos(x+dx,y+dy));p.SetLayerSet(layer_set([pcb.F_Paste]));f.Add(p)
 pcb.FootprintSave(str(OUT/'Globe.pretty'),f)
 f.Flip(pos(x,y),False);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 return f

def main():
 reps={}
 for t in D['tiles']:reps.setdefault(t['type'],t)
 summary=[]
 for typ,t in reps.items():
  b=pcb.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(mm(1));b.GetDesignSettings().m_MinClearance=mm(.10);b.GetDesignSettings().m_TrackMinWidth=mm(.10);b.GetDesignSettings().m_ViasMinSize=mm(.45);b.GetDesignSettings().m_MinThroughDrill=mm(.20);b.GetDesignSettings().m_CopperEdgeClearance=mm(.25)
  nc=b.GetDesignSettings().m_NetSettings.GetDefaultNetclass();nc.SetClearance(mm(.1));nc.SetTrackWidth(mm(.1));nc.SetViaDiameter(mm(.45));nc.SetViaDrill(mm(.2))
  nets={};origin=(60,60)
  for name in ['GND','3V3','SDA','SCL','SDB','INTB','ADDR','ISET']:net(b,name,nets)
  for i in range(39):net(b,'CS'+str(i+1),nets)
  for i in range(9):net(b,'SW'+str(i+1),nets)
  # No optical-face silkscreen; the dark diffuser sits directly over the emitters.
  # Map CAD +Y upward to KiCad's downward screen coordinates.
  world=lambda x,y:(60+x,60-y)
  outline=[world(*p) for p in t['outline']]
  for a,c in zip(outline,outline[1:]+outline[:1]):
   edge=pcb.PCB_SHAPE();edge.SetShape(pcb.SHAPE_T_SEGMENT);edge.SetStart(pos(*a));edge.SetEnd(pos(*c));edge.SetLayer(pcb.Edge_Cuts);edge.SetWidth(mm(.05));b.Add(edge)
  for i,(x,y) in enumerate(t['holes']):
   h=footprint(b,'MountingHole','MountingHole_2.2mm_M2','H'+str(i+1),'M2 clearance',*world(x,y))
  rows=[]
  def emitter_position(p):
   x,y=p['x'],p['y']
   for _ in range(3):
    for a,c in zip(t['outline'],t['outline'][1:]+t['outline'][:1]):
     dx,dy=c[0]-a[0],c[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L
     distance=min((x+sx-a[0])*nx+(y+sy-a[1])*ny for sx in [-.78,.78] for sy in [-.32,.32])
     if distance<.25:x+=nx*(.251-distance);y+=ny*(.251-distance)
   if math.hypot(x-p['x'],y-p['y'])>.3:raise ValueError('LED shift exceeds optical aperture allowance')
   return x,y
  for i,p in enumerate(t['leds']):
   f=footprint(b,'LED_SMD','LED_0402_1005Metric','D'+str(i+1),'Amber 590 nm, 1005 metric',*world(*emitter_position(p)))
   pads(f,{'1':nets['CS'+str(p['cs']+1)],'2':nets['SW'+str(p['sw']+1)]})
   rows.append({'reference':f.GetReference(),'x_mm':emitter_position(p)[0],'y_mm':emitter_position(p)[1],'cell_x_mm':p['x'],'cell_y_mm':p['y'],'switch':p['sw']+1,'sink':p['cs']+1,'linear_channel':p['channel']})
  u=custom_driver(b,nets,*world(0,4))
  connmap={str(i+1):nets[n] for i,n in enumerate(['3V3','GND','SDA','SCL','SDB','INTB'])}
  for i,x in enumerate([-8.5,8.5]):
   f=footprint(b,'Connector_JST','JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal','J'+str(i+1),'JST SH 6 pin',*world(x,-.6),back=True);pads(f,connmap)
  caps=[(-7.5,4,'1uF'),(7.5,4,'1uF'),(-4.7,8.9,'10uF'),(4.7,8.9,'10uF'),(0,-1.2,'10uF')]
  for i,(x,y,value) in enumerate(caps):
   f=footprint(b,'Capacitor_SMD','C_0603_1608Metric' if value=='1uF' else 'C_0805_2012Metric','C'+str(i+1),value+' 10V X7R',*world(x,y),back=True);pads(f,{'1':nets['3V3'],'2':nets['GND']})
  f=footprint(b,'Resistor_SMD','R_0603_1608Metric','R1','2.2k 1% ISET; reference value, qualify current',*world(-6.0,7),back=True);pads(f,{'1':nets['ISET'],'2':nets['GND']})
  f=footprint(b,'Resistor_SMD','R_0603_1608Metric','R2','100k default shutdown',*world(6.0,7),back=True);pads(f,{'1':nets['SDB'],'2':nets['GND']})
  # Bridge exactly one large solder jumper after assigning the tile's I2C address.
  for i,n in enumerate(['GND','SCL','SDA','3V3']):
   f=footprint(b,'Jumper','SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm','JP'+str(i+1),'BRIDGE ONE: '+hex(0x30+i),*world((i-1.5)*3.6,-6),back=True)
   pads(f,{'1':nets['ADDR'],'2':nets[n]})
  # Pin label and board identity on the inward side; keep silkscreen off the optical face.
  label=pcb.PCB_TEXT(b);label.SetText(f'T{typ}');label.SetPosition(pos(*world(0,max(p[1] for p in t['outline'])-1.8)));label.SetLayer(pcb.B_SilkS);label.SetMirrored(True);label.SetTextSize(pos(.8,.8));label.SetTextThickness(mm(.1));b.Add(label)
  filename=OUT/f'led-tile-{typ:02}.kicad_pcb';pcb.SaveBoard(str(filename),b)
  (OUT/f'led-tile-{typ:02}.kicad_dru').write_text('(version 1)\n(rule "Fabrication minima" (constraint clearance (min 0.10mm)) (constraint track_width (min 0.10mm)) (constraint hole_size (min 0.20mm)) (constraint edge_clearance (min 0.25mm)))\n')
  # Embedded board, footprints, netlist and DSN share the same exact pad-level connectivity.
  pcb.ExportSpecctraDSN(b,str(OUT/f'led-tile-{typ:02}.dsn'))
  with (OUT/f'led-tile-{typ:02}-channels.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  netlist={name:[{'ref':f.GetReference(),'pad':p.GetNumber()} for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()==name] for name in nets}
  (OUT/f'led-tile-{typ:02}-netlist.json').write_text(json.dumps(netlist,indent=2))
  summary.append({'type':typ,'leds':len(rows),'quantity':sum(t0['populated'] and t0['type']==typ for t0 in D['tiles']),'footprints':len(list(b.GetFootprints())),'status':'placed; routing and DRC pending'})
  print(summary[-1],flush=True)
 (OUT/'fp-lib-table').write_text('(fp_lib_table (lib (name "Globe")(type "KiCad")(uri "${KIPRJMOD}/Globe.pretty")(options "")(descr "Globe optical footprints; KiCad library derivatives")))\n')
 (OUT/'boards.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
