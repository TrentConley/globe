"""Generate reviewable manufacturing outputs only for the DRC-clean optical bench."""
from pathlib import Path
import pcbnew as p,json,csv,subprocess,os,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated';release=ROOT/'electronics/bench-release';release.mkdir(exist_ok=True);path=OUT/'optical-bench-10.kicad_pcb';b=p.LoadBoard(str(path));mm=p.FromMM
for f in b.GetFootprints():
 if f.GetReference().startswith('P') or f.GetReference()=='GND':f.SetAttributes(p.FP_SMD|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
for item in list(b.GetDrawings()):
 if item.GetClass()=='PCB_TEXT':b.Remove(item)
# Labels are masked by copper clearances in the final plot and inspected by DRC.
for i in range(10):
 text=p.PCB_TEXT(b);text.SetText(str(i));text.SetPosition(p.VECTOR2I(mm(60+(i-4.5)*2.2),mm(68.35)));text.SetLayer(p.B_SilkS);text.SetMirrored(True);text.SetTextSize(p.VECTOR2I(mm(.8),mm(.8)));text.SetTextThickness(mm(.08));b.Add(text)
p.SaveBoard(str(path),b)
run=lambda *args:subprocess.run(['kicad-cli',*args],check=True)
run('pcb','drc',str(path),'--format','json','-o',str(OUT/'optical-bench-10-drc.json'))
r=json.loads((OUT/'optical-bench-10-drc.json').read_text())
if r['violations'] or r['unconnected_items']:raise ValueError('Bench fabrication output blocked by DRC')
run('pcb','export','gerbers',str(path),'-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts','--subtract-soldermask','-o',str(release/'gerbers')+'/')
run('pcb','export','drill',str(path),'--excellon-separate-th','--generate-map','--map-format','pdf','-o',str(release/'gerbers')+'/')
run('pcb','export','pos',str(path),'--format','csv','--units','mm','--side','both','--smd-only','--exclude-dnp','-o',str(release/'placement.csv'))
run('pcb','export','svg',str(path),'-l','F.Cu,F.Mask,Edge.Cuts','-o',str(release/'board-front.svg'))
with (release/'bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['references','quantity','value','package','candidate_MPN','qualification'])
 w.writerow(['D1-D10',10,'amber/yellow 590 nm','1005 metric / 0402 imperial','Kingbright APHHS1005SYCK','Supplier must confirm dimensions and pad 1 cathode against current datasheet; candidate not bench-tested'])
 w.writerow(['R1-R10',10,'1 kohm 1% >=0.063W','1608 metric / 0603 imperial','Yageo RC0603FR-071KL','Ordinary 1% 0603 equivalent acceptable'])
subprocess.run(['/usr/bin/python3',str(ROOT/'electronics/audit_bench.py')],check=True)
for name in ['optical-bench-10.kicad_pcb','optical-bench-10.kicad_pro','optical-bench-10.kicad_dru','optical-bench-10-drc.json','optical-bench-10.ses','fp-lib-table']:
 if (OUT/name).exists():shutil.copy2(OUT/name,release/name)
shutil.copytree(OUT/'Globe.pretty',release/'Globe.pretty',dirs_exist_ok=True)
print('Bench outputs generated and net-audited',flush=True)
