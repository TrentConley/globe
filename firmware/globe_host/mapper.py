"""Area-sampled geographic footprints, independent of driver layout."""
import math,json
import numpy as np
from scipy.spatial import cKDTree

class Mapper:
 def __init__(self,path):
  self.data=np.load(path);self.directions=self.data['directions'];self.land=self.data['land'];self.tiles=self.data['tiles'];self.channels=self.data['channels'];self.visible=self.data['visible'];self.centers=self.directions[:,4,:];self.eligible=np.flatnonzero((self.land*self.visible).any(axis=1));self.tree=cKDTree(self.centers[self.eligible])
 def render(self,project):
  weights=np.zeros(len(self.tiles));visits=project['visits'];adjusted=[];unsupported=[]
  if visits:
   angles=np.radians([[v['lat'],v['lon']] for v in visits]);lat,lon=angles[:,0],angles[:,1];points=np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
   tree=cKDTree(points);distance=tree.query(self.directions.reshape(-1,3),workers=1)[0];arc=2*np.arcsin(np.minimum(1,distance/2));radius=project['radiusMiles']*1.609344/6371.0088
   q=np.clip((radius-arc)/(radius*.20),0,1);coverage=(q*q*(3-2*q)).reshape(-1,9)*self.land
   weights=(coverage*self.visible).mean(axis=1)
   # Below two cells across, an area average can vanish beside a mounting hole.
   # Preserve a visible local mark within 1.8 radii; never jump across a large blind region.
   distances,nearest=self.tree.query(points)
   for visit,distance,index in zip(visits,distances,nearest):
    arc=2*math.asin(min(1,distance/2));pixel=self.eligible[index]
    if arc<=radius*1.8:
     if weights[pixel]<.65:weights[pixel]=.65;adjusted.append(visit.get('name','unnamed place'))
    else:unsupported.append(visit.get('name','unnamed place'))
  # Pixel union is a maximum/nearest-distance operation. Repeated visits cannot brighten it.
  intensity=weights*project['brightness'];active_sum=float(intensity.sum())
  # A calibrated current limit is required at commissioning. This conservative command budget
  # bounds total PWM sum; it is not a substitute for the supply current sensor.
  budget=4000.0
  factor=min(1,budget/active_sum) if active_sum else 1
  values=np.rint(intensity*factor*255).astype(np.uint8);frames={}
  for tile,channel,value in zip(self.tiles,self.channels,values):
   if int(tile) not in frames:frames[int(tile)]=bytearray(351)
   frames[int(tile)][int(channel)]=int(value)
  return frames,{'litChannels':int(np.count_nonzero(values)),'pwmSum':float(values.sum()/255),'commandLimitScale':factor,'radiusMiles':project['radiusMiles'],'approximatedPlaces':adjusted,'unrepresentedPlaces':unsupported}
