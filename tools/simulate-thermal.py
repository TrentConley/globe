"""Steady-state thermal network with sensitivity, not a CFD or measured result."""
import json,math
from pathlib import Path
import numpy as np
from scipy.optimize import root
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'engineering/release';R=json.loads((ROOT/'cad/design/requirements.json').read_text());SIGMA=5.670374419e-8
A=4*math.pi*.1525**2

def solve(power,ambient,inside_h=2.0,outside_h=3.0,emissivity=.85):
 ta=ambient+273.15
 # Node 0: homogenized inner globe; node 1: outer shell.
 # Equivalent inside coupling includes gap conduction/convection and long-wave radiation.
 def equations(x):
  inner,outer=x;qin=A*(inside_h*(inner-outer)+emissivity*SIGMA*(inner**4-outer**4))
  qout=A*(outside_h*(outer-ta)+emissivity*SIGMA*(outer**4-ta**4))
  return [qin-power,qout-power]
 s=root(equations,[ta+power,ta+power/2]);assert s.success and np.linalg.norm(equations(s.x))<1e-6
 return {'interior_C':float(s.x[0]-273.15),'surface_C':float(s.x[1]-273.15)}
scenarios=[]
for ambient in [20,25,30,35]:
 for power in [5,10,12,15,20]:scenarios.append({'ambient_C':ambient,'globe_heat_W':power,**solve(power,ambient)})
# Sensitivity bounds include poorer air exchange and lower effective surface emissivity.
sensitivity=[{'inside_h_W_m2K':hi,'outside_h_W_m2K':ho,'emissivity':em,**solve(12,30,hi,ho,em)} for hi,ho,em in [(2,3,.85),(1,2,.7),(.5,1,.6)]]
report={'model':'Two-node steady-state enclosure heat balance with nonlinear radiation','globe_area_m2':A,'assumptions':{'shell_conduction':'neglected in homogenized network; add local material/terrain resistance during test','inside_h_W_m2K':2,'outside_h_W_m2K':3,'emissivity':.85,'ambient_design_C':30,'globe_heat_design_W':12,'base_electronics_allowance_W':3,'total_command_target_W':15},'scenarios':scenarios,'sensitivity_at_12W_30C':sensitivity,'local_hotspot_sensitivity':[{'chip_dissipation_W':p,'theta_JA_C_W':theta,'junction_rise_above_local_board_C':p*theta} for p in [.05,.1,.2] for theta in [40,80,120]],'limits':['No resolved air circulation, board hot spots or direct sunlight','Surface coating emissivity, resin conductivity and LED currents are unmeasured','Sensor trip is 50 C; firmware must blank if sensor becomes invalid','Power monitor and per-sector thermal tests remain mandatory; software PWM is not a calibrated watt limit']}
(OUT/'thermal-analysis.json').write_text(json.dumps(report,indent=2))
fig,ax=plt.subplots(figsize=(9,5),facecolor='#101619');ax.set_facecolor('#101619')
for a,color in [(20,'#6ca5a2'),(25,'#99ad84'),(30,'#e2b676'),(35,'#d08262')]:
 xs=np.linspace(0,22,45);ys=[solve(p,a)['interior_C'] for p in xs];ax.plot(xs,ys,label=f'{a} °C room',color=color)
ax.axhline(50,color='#d36565',ls='--',label='50 °C sensor shutdown');ax.axvline(12,color='#859391',ls=':',label='12 W globe allocation');ax.set(xlabel='Heat inside globe (W)',ylabel='Estimated interior temperature (°C)',title='Thermal screening: uniform enclosure, no local hot spots');ax.tick_params(colors='#dfe6dd');ax.xaxis.label.set_color('#dfe6dd');ax.yaxis.label.set_color('#dfe6dd');ax.title.set_color('#dfe6dd');ax.legend(facecolor='#182328',labelcolor='#e5e6dc',fontsize=9);ax.grid(alpha=.12);fig.tight_layout();fig.savefig(OUT/'thermal-sensitivity.png',dpi=180);print(json.dumps({'design':solve(12,30),'sensitivity':sensitivity},indent=2))
