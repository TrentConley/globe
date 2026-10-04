import grid from './data/elevation-grid.js';

const decoded=Uint8Array.from(atob(grid.samplesBase64),c=>c.charCodeAt(0));
const view=new DataView(decoded.buffer);
const samples=new Int16Array(grid.width*grid.height);
for(let i=0;i<samples.length;i++)samples[i]=view.getInt16(i*2,true);
const clamp=(x,low,high)=>Math.max(low,Math.min(high,x));
const mix=(a,b,t)=>a+(b-a)*t;
const wrap=x=>((x%grid.width)+grid.width)%grid.width;
const northPole=samples.subarray(0,grid.width).reduce((s,x)=>s+x,0)/grid.width;
const southPole=samples.subarray(samples.length-grid.width).reduce((s,x)=>s+x,0)/grid.width;

export const DEFAULT_EXAGGERATION=25;
export const MAX_EXAGGERATION=40;
export const ELEVATION_SOURCE=grid.dataset;
export const MAX_ELEVATION_METERS=grid.maximumMeters;
export const METERS_TO_GLOBE_MM=152.5 / 6371008.8;
export const ELEVATION_RESOLUTION_DEGREES=grid.degreesPerCell;

export function elevationMeters(lat,lon) {
  const gx=(lon+180)/grid.degreesPerCell-0.5;
  const gy=(90-clamp(lat,-90,90))/grid.degreesPerCell-0.5;
  const x=Math.floor(gx),y=clamp(gy,0,grid.height-1),y0=Math.floor(y),y1=Math.min(y0+1,grid.height-1);
  const x0=wrap(x),x1=wrap(x+1),tx=gx-x,ty=y-y0;
  const row0=mix(samples[y0*grid.width+x0],samples[y0*grid.width+x1],tx);
  const row1=mix(samples[y1*grid.width+x0],samples[y1*grid.width+x1],tx);
  const result=mix(row0,row1,ty);
  // Converge all longitudes at each pole rather than creating a seam/fan there.
  if(gy<0)return mix(result,northPole,clamp(-gy*2,0,1));
  if(gy>grid.height-1)return mix(result,southPole,clamp((gy-grid.height+1)*2,0,1));
  return result;
}

export function terrainHeightMM(lat,lon,exaggeration=DEFAULT_EXAGGERATION) {
  // Smooth sea-level shell: bathymetry and below-sea-level depressions are not cut into the wall.
  return Math.max(0,elevationMeters(lat,lon))*METERS_TO_GLOBE_MM*exaggeration;
}
