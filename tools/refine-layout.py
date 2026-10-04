"""Refine hardware coverage with Natural Earth 1:10m islands.
Run after design-layout.mjs. Populate a tile wherever detailed land falls near a
cell; narrow islands retain one sampled cell instead of disappearing entirely.
"""
from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree
import shapely
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'cad/generated/layout.json';d=json.loads(path.read_text());g=json.loads((ROOT/'cad/data/land-10m.geojson').read_text());land=shapely.union_all([shape(f['geometry']) for f in g['features']]);shapely.prepare(land)
coordinates=shapely.get_coordinates(land);lat=np.radians(coordinates[:,1]);lon=np.radians(coordinates[:,0]);coast=cKDTree(np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)]))
for t in d['tiles']:
 pts=np.array([p['direction'] for p in t['leds']]);lats=np.degrees(np.arcsin(pts[:,2]));lons=np.degrees(np.arctan2(pts[:,1],pts[:,0]));inside=shapely.contains_xy(land,lons,lats);near=coast.query(pts)[0]*152.5<1.6
 for p,value in zip(t['leds'],inside|near):p['land']=bool(value)
 t['populated']=bool((inside|near).any()) and not t['southKeepout']
for sector in d['sectors']:sector['tiles']=[t['id'] for t in d['tiles'] if t['sector']==sector['id'] and t['populated']]
d['summary']['populatedTiles']=sum(t['populated'] for t in d['tiles']);d['summary']['leds']=sum(len(t['leds']) for t in d['tiles'] if t['populated']);d['summary']['landLEDs']=sum(sum(p['land'] for p in t['leds']) for t in d['tiles'] if t['populated']);d['coveragePolicy']='1:10m land plus 1.6 mm coastal/island sampling envelope; south support tiles excluded in A0'
path.write_text(json.dumps(d,separators=(',',':')));(ROOT/'engineering/release/layout-summary.json').write_text(json.dumps(d['summary'],indent=2));print(d['summary']['populatedTiles'],d['summary']['leds'])
