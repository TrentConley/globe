"""Simple 10-channel, resistor-limited optical board matching the type-02 cradle.
Pico GPIO drives each LED through 1 kohm. No matrix IC or mains supply required.
"""
import json,csv
import pcbnew as p
import generate as g
sel=json.loads((g.ROOT/'engineering/release/optical-bench-selection.json').read_text());t=next(t for t in g.D['tiles'] if t['type']==2);b=p.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(g.mm(1));nc=b.GetDesignSettings().m_NetSettings.GetDefaultNetclass();nc.SetClearance(g.mm(.25));nc.SetTrackWidth(g.mm(.15));nc.SetViaDiameter(g.mm(.6));nc.SetViaDrill(g.mm(.3));nets={};g.net(b,'GND',nets);world=lambda x,y:(60+x,60-y)
outline=[world(*q) for q in t['outline']]
for a,z in zip(outline,outline[1:]+outline[:1]):
 edge=p.PCB_SHAPE();edge.SetShape(p.SHAPE_T_SEGMENT);edge.SetStart(g.pos(*a));edge.SetEnd(g.pos(*z));edge.SetLayer(p.Edge_Cuts);edge.SetWidth(g.mm(.05));b.Add(edge)
for i,(x,y) in enumerate(t['holes']):g.footprint(b,'MountingHole','MountingHole_2.2mm_M2','H'+str(i+1),'M2 clearance',*world(x,y))
rows={int(r['linear_channel']):r for r in csv.DictReader((g.OUT/'led-tile-02-channels.csv').open())}
(g.OUT/'Globe.pretty/WirePad_1.4x2.kicad_mod').write_text('(footprint "WirePad_1.4x2" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd) (pad "1" smd rect (at 0 0) (size 1.4 2) (layers "F.Cu" "F.Mask")))\n')
def wirepad(ref,x,y,net):
 f=p.FootprintLoad(str(g.OUT/'Globe.pretty'),'WirePad_1.4x2');f.SetFPID(p.LIB_ID('Globe','WirePad_1.4x2'));f.SetReference(ref);f.SetValue(ref);f.SetPosition(g.pos(*world(x,y)));b.Add(f);f.Flip(g.pos(*world(x,y)),False);g.pads(f,{'1':net});f.Reference().SetVisible(False);f.Value().SetVisible(False)
for i,ch in enumerate(sel['channels']):
 r=rows[ch];anode=g.net(b,'LED'+str(i),nets);gpio=g.net(b,'GPIO'+str(i),nets);f=g.footprint(b,'LED_SMD','LED_0402_1005Metric','D'+str(i+1),'Amber 590nm 1005',*world(float(r['x_mm']),float(r['y_mm'])));g.pads(f,{'1':nets['GND'],'2':anode});x=(i-4.5)*2.2
 f=g.footprint(b,'Resistor_SMD','R_0603_1608Metric','R'+str(i+1),'1k 1%',*world(x,-6.4),back=True);f.SetOrientationDegrees(90);g.pads(f,{'1':gpio,'2':anode});wirepad('P'+str(i),x,-9.8,gpio)
wirepad('GND',0,-2,nets['GND'])
path=g.OUT/'optical-bench-10.kicad_pcb';p.SaveBoard(str(path),b);p.ExportSpecctraDSN(b,str(path.with_suffix('.dsn')));s=path.with_suffix('.dsn').read_text().replace('(clearance 62.5 (type smd_smd))','(clearance 250 (type smd_smd))');path.with_suffix('.dsn').write_text(s);path.with_suffix('.kicad_dru').write_text('(version 1)\n(rule "Bench fabrication" (constraint clearance (min 0.25mm)) (constraint track_width (min 0.15mm)) (constraint hole_size (min 0.30mm)) (constraint edge_clearance (min 0.25mm)))\n');print('Generated 10-cell bench PCB',flush=True)
