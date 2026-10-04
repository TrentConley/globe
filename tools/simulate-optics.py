"""Optical sensitivity study, not a calibrated prediction of appearance."""
from pathlib import Path
import json,math
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
OUT=Path(__file__).resolve().parents[1]/'engineering/release';rng=np.random.default_rng(30525);count=300000
# Uniform rectangular 1.0 x 0.5 mm emitting die, Lambertian hemisphere.
x=rng.uniform(-.5,.5,count);y=rng.uniform(-.25,.25,count);r=np.sqrt(rng.random(count));phi=rng.uniform(0,2*np.pi,count);dz=np.sqrt(1-r*r);dx=r*np.cos(phi);dy=r*np.sin(phi);cases=[]
for distance in [6,8,10,12]:
 top_x=x+distance*dx/dz;top_y=y+distance*dy/dz;accepted=(abs(top_x)<.85)&(abs(top_y)<.85);p=float(accepted.mean());cases.append({'dieToApertureMM':distance,'directLambertianFraction':p,'monteCarlo95PercentHalfWidth':1.96*math.sqrt(p*(1-p)/count)})
attenuation=[]
for mu in [.05,.2,.5,1.0]:
 attenuation.append({'assumedBulkAbsorptionPerMM':mu,'oneMMTransmission':math.exp(-mu),'fourPoint73MMTransmission':math.exp(-mu*4.73),'raisedToFlatRatio':math.exp(-mu*3.73)})
report={'status':'UNMEASURED MATERIAL PARAMETERS; sensitivity study only','raysPerCase':count,'seed':30525,'dieMM':[1,.5],'topOpeningMM':[1.7,1.7],'directLight':cases,'bulkAbsorption':attenuation,'finishTransmissionTestRange':[.05,.4],'scatterSigmaMM':[.1,.3,.6,1.0],'limits':['Opaque cell walls absorb rejected rays; no wall reflections or measured LED angular data.','Square straight-axis cell approximates a local radial channel; real taper and off-axis die positions vary.','Beer–Lambert sweep does not predict resin scattering, surface paint or human perception.','Absolute brightness requires a measured LED/driver/finish test. Do not treat the display rendering as optical validation.']}
(OUT/'optical-sensitivity.json').write_text(json.dumps(report,indent=2))
fig,axs=plt.subplots(1,4,figsize=(12,3.8),facecolor='#101619');pitch=.025;coords=(np.arange(400)-199.5)*pitch;X,Y=np.meshgrid(coords,coords);radius=1.9261;source=(X*X+Y*Y<radius*radius).astype(float)
for ax,sigma in zip(axs,[.1,.3,.6,1.]):
 field=gaussian_filter(source,sigma/pitch);ax.imshow(field,cmap='afmhot',origin='lower',extent=[-5,5,-5,5],vmin=0,vmax=1);ax.set_title(f'Assumed spread σ = {sigma} mm',color='white',fontsize=10);ax.set_xlabel('mm on globe',color='white');ax.tick_params(colors='white');ax.set_yticks([])
fig.suptitle('A 50-mile footprint under four assumed scattering strengths\nRelative brightness only; these material parameters have not been measured.',color='white',fontsize=12);fig.tight_layout();fig.savefig(OUT/'optical-sensitivity.png',dpi=160);print(json.dumps(report,indent=2))
