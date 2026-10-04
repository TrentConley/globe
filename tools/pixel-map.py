"""Reproducible radial optical apertures and geographic samples. No material calibration."""
from pathlib import Path
import json,hashlib,sys,math
import numpy as np
import shapely
from shapely.geometry import shape
from scipy.spatial import cKDTree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'engineering/release';OUT.mkdir(exist_ok=True)
D=json.loads((ROOT/'cad/generated/layout.json').read_text());geo=json.loads((ROOT/'cad/data/land-10m.geojson').read_text());land_shape=shapely.union_all([shape(f['geometry']) for f in geo['features']]);shapely.prepare(land_shape)
coast_xy=shapely.get_coordinates(land_shape);clat=np.radians(coast_xy[:,1]);clon=np.radians(coast_xy[:,0]);coast_tree=cKDTree(np.column_stack([np.cos(clat)*np.cos(clon),np.cos(clat)*np.sin(clon),np.sin(clat)]))
directions=[];lands=[];visible=[];tiles=[];channels=[];corners=[];radii=[];leds=[]
for t in D['tiles']:
 if not t['populated']:continue
 c,ex,ey,n=[np.array(t[k]) for k in ('center','ex','ey','normal')];d=c@n;anchors={a['hole'] for a in D['anchors'] if a['tile']==t['id']}
 for p in t['leds']:
  samples=np.array([c+ex*(p['x']+dx)+ey*(p['y']+dy)+n*.1 for dy in (-.5333333,0,.5333333) for dx in (-.5333333,0,.5333333)]);dirs=samples/np.linalg.norm(samples,axis=1)[:,None]
  lat=np.degrees(np.arcsin(dirs[:,2]));lon=np.degrees(np.arctan2(dirs[:,1],dirs[:,0]));on_land=shapely.contains_xy(land_shape,lon,lat)|(coast_tree.query(dirs)[0]*152.5<.6);vis=np.ones(9,dtype=bool)
  # Opaque shell bosses/holders extend along the face normal, while the cells fan radially.
  # Shadow envelope conservatively uses the full 3.3 mm holder radius along z=1..inner.
  for hole,h in enumerate(t['holes']):
   zs=[1,2.4] if hole not in anchors else np.linspace(1,11,9)
   radius=1.95 if hole not in anchors else 3.3
   for z in zs:
    projected=dirs*((d+z)/(dirs@n))[:,None]-c
    x=projected@ex;y=projected@ey;vis &= (x-h[0])**2+(y-h[1])**2>radius**2
  directions.append(dirs);lands.append(on_land);visible.append(vis);tiles.append(t['id']);channels.append(p['channel'])
  q=np.array([c+ex*(p['x']+dx)+ey*(p['y']+dy)+n*.1 for dx,dy in [(-.8,-.8),(.8,-.8),(.8,.8),(-.8,.8)]]);q/=np.linalg.norm(q,axis=1)[:,None];corners.append(q)
  leds.append({'tile':t['id'],'channel':p['channel'],'direction':dirs[4].tolist(),'landFraction':float(on_land.mean()),'visibleFraction':float(vis.mean())})
arr={'directions':np.array(directions,dtype=np.float32),'land':np.array(lands),'visible':np.array(visible),'tiles':np.array(tiles,dtype=np.uint16),'channels':np.array(channels,dtype=np.uint16),'corners':np.array(corners,dtype=np.float32)}
path=OUT/'pixel-map.npz';np.savez_compressed(path,**arr);digest=hashlib.sha256(path.read_bytes()).hexdigest()
sectors={s['id']:s['tiles'] for s in D['sectors'] if s['tiles']};manifest={'version':1,'sha256':digest,'sectors':sectors,'sampleCount':9,'description':'Radial aperture geography; opaque hardware shadow envelopes. No scattering or transmission calibration.'}
(OUT/'pixel-map.json').write_text(json.dumps(manifest,indent=2));(OUT/'pixel-preview.json').write_text(json.dumps(leds,separators=(',',':')))
for s,ids in sectors.items():
 target=ROOT/f'firmware/config/sector-{s:02}';target.mkdir(parents=True,exist_ok=True);(target/'sector.json').write_text(json.dumps({'sector':s,'tiles':[i%16 for i in ids],'map_sha256':digest},indent=2))
sys.path.insert(0,str(ROOT/'firmware'));from globe_host.mapper import Mapper
mapper=Mapper(path);cities=[('Vancouver',49.2827,-123.1207),('Seattle',47.6062,-122.3321),('New York',40.7128,-74.006),('Chicago',41.8781,-87.6298),('Los Angeles',34.0522,-118.2437),('Sioux Falls',43.546,-96.7313),('London',51.5074,-.1278),('Tokyo',35.6762,139.6503),('Sydney',-33.8688,151.2093),('Reykjavik',64.1466,-21.9426),('Honolulu',21.3099,-157.8581),('Singapore',1.3521,103.8198),('Kathmandu',27.7172,85.324)]
report=[];city_values={}
for name,lat,lon in cities:
 frames,metrics=mapper.render({'visits':[{'lat':lat,'lon':lon}],'radiusMiles':50,'brightness':1});values=np.array([frames[int(t)][int(ch)]/255 for t,ch in zip(tiles,channels)]);city_values[name]=values
 report.append({'place':name,'lat':lat,'lon':lon,**metrics,'sumFullPixelEquivalent':float(values.sum()),'maximumPWM':int(values.max()*255),'populatedTileIds':sorted(set(np.array(tiles)[values>0].tolist()))})
# Land-area-weighted regular geographic samples: a diagnostic of large blind spots, not travel percentage.
lat,lon=np.meshgrid(np.arange(-89.75,90,.5),np.arange(-179.75,180,.5),indexing='ij');mask=shapely.contains_xy(land_shape,lon,lat);la=np.radians(lat[mask]);lo=np.radians(lon[mask]);points=np.column_stack([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)]);valid=arr['land']&arr['visible'];tree=cKDTree(arr['directions'][valid]);distance=2*np.arcsin(np.minimum(1,tree.query(points)[0]/2))*6371.0088/1.609344;weight=np.cos(la)
result={'status':'GEOMETRIC SAMPLING ONLY; material optics unmeasured','leds':len(tiles),'apertureWidthAtBoardMM':1.6,'pitchAtBoardMM':2,'footprintDiameterMM':2*50*1.609344/6371.0088*152.5,'hardwareShadowedSampleFraction':float(1-arr['visible'].mean()),'landGridSamples':len(distance),'landWeightedSamplesWithin50MilesOfOpenSample':float(weight[distance<=50].sum()/weight.sum()),'landNearestOpenSampleDistanceMilesPercentiles':dict(zip(['50','90','95','99','100'],np.percentile(distance,[50,90,95,99,100]).tolist())),'cityExamples':report,'limits':['Natural Earth 1:10m coastlines use a 0.6 mm sampling allowance for narrow islands; this admits some water near shores.','A nearest-cell visibility floor approximates small footprints within 90 miles at the 50-mile setting; unsupported places are reported. The south support region remains unpopulated in A0.','Scattering, pigment transmission, LED angular output and perceived brightness are not calibrated.','Do not interpret land coverage diagnostics as the percentage of Earth visited.']}
(OUT/'coverage-analysis.json').write_text(json.dumps(result,indent=2))
fig,axes=plt.subplots(2,2,figsize=(11,8),facecolor='#101112');polys=np.stack([np.degrees(np.arctan2(arr['corners'][:,:,1],arr['corners'][:,:,0])),np.degrees(np.arcsin(arr['corners'][:,:,2]))],axis=-1);centers=np.stack([np.degrees(np.arctan2(arr['directions'][:,4,1],arr['directions'][:,4,0])),np.degrees(np.arcsin(arr['directions'][:,4,2]))],axis=-1)
for ax,name in zip(axes.ravel(),['Vancouver','New York','London','Kathmandu']):
 entry=next(r for r in report if r['place']==name);x,y=entry['lon'],entry['lat'];sx=2.3/max(.3,math.cos(math.radians(y)));sy=2.3;sel=(abs(centers[:,0]-x)<sx*1.4)&(abs(centers[:,1]-y)<sy*1.4);values=city_values[name];colors=np.zeros((sel.sum(),4));colors[:,:3]=[.13,.14,.14];colors[:,3]=1;v=values[sel];colors[:,:3]+=v[:,None]*np.array([.86,.46,.06]);ax.add_collection(PolyCollection(polys[sel],facecolors=colors,edgecolors='#070809',linewidths=.3));a=np.linspace(0,2*np.pi,200);ax.plot(x+.724* np.cos(a)/math.cos(math.radians(y)),y+.724*np.sin(a),color='#e8c584',lw=1,ls='--');ax.plot(x,y,'+',color='white',ms=7);ax.set(xlim=(x-sx,x+sx),ylim=(y-sy,y+sy),facecolor='#090a0b');ax.set_title(f"{name} · {entry['litChannels']} commanded LEDs",color='white');ax.tick_params(colors='#a8a8a8');ax.set_aspect(1/max(.3,math.cos(math.radians(y))))
fig.suptitle('50-mile footprints on the actual cell layout\nDashed: requested boundary. Gold: area-sampled PWM before real optical diffusion.',color='white',fontsize=13);fig.tight_layout();fig.savefig(OUT/'coverage-cities.png',dpi=160);plt.close(fig)
print(json.dumps(result,indent=2))
