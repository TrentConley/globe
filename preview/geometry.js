// Shared by the renderer, millimetre STL exporter, and geometry tests.
import {terrainHeightMM,DEFAULT_EXAGGERATION,MAX_EXAGGERATION} from './elevation.js';
export const EARTH_KM = 6371.0088;
export const RADIUS_MM = 152.5;
export const DEG = Math.PI / 180;
export const milesToMM = miles => miles * 1.609344 / EARTH_KM * RADIUS_MM;
export const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
export const dot = (a, b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
export const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
export const normalize = a => { const n = Math.hypot(...a); return a.map(x => x/n); };
export function vector(lat, lon) {
  return [Math.cos(lat*DEG)*Math.sin(lon*DEG), Math.sin(lat*DEG), Math.cos(lat*DEG)*Math.cos(lon*DEG)];
}
export function latLon(p) {
  const n = Math.hypot(...p);
  return {lat: Math.asin(clamp(p[1]/n,-1,1))/DEG, lon: Math.atan2(p[0],p[2])/DEG};
}
export function angle(a,b) { return Math.atan2(Math.hypot(...cross(a,b)), clamp(dot(a,b),-1,1)); }
export function frame(lat,lon) {
  const center=vector(lat,lon), east=[Math.cos(lon*DEG),0,-Math.sin(lon*DEG)];
  return {center,east,north:cross(center,east)};
}
export function localDirection(u,v) { return [Math.cos(v)*Math.sin(u),Math.sin(v),Math.cos(v)*Math.cos(u)]; }
export function worldDirection(local,basis) {
  return local.map((_,i) => local[0]*basis.east[i]+local[1]*basis.north[i]+local[2]*basis.center[i]);
}
export function validateProject(value) {
  const source=value?.version===1 ? value.stops : value?.version===2 ? value.visits : null;
  if (!Array.isArray(source) || source.length>200) throw new Error('Use a globe JSON file with at most 200 visited places.');
  const radiusMiles=value.radiusMiles ?? 50;
  if(typeof radiusMiles!=='number' || !Number.isFinite(radiusMiles) || radiusMiles<25 || radiusMiles>350) throw new Error('Footprint radius must be between 25 and 350 miles.');
  const visits=source.map((p,i) => {
    if (!p || typeof p.name!=='string' || !p.name.trim() || p.name.length>100 || typeof p.lat!=='number' || typeof p.lon!=='number' || !Number.isFinite(p.lat) || !Number.isFinite(p.lon) || Math.abs(p.lat)>90 || Math.abs(p.lon)>180) throw new Error(`Invalid coordinates or fields at place ${i+1}.`);
    return {name:p.name.trim(),lat:p.lat,lon:p.lon};
  });
  return {version:2,visits,radiusMiles};
}
export function createFootprintField(visits,miles) {
  const radius=miles*1.609344/EARTH_KM,outer=Math.cos(radius),inner=Math.cos(radius*0.84);
  const places=visits.map(p=>({p:vector(p.lat,p.lon),lat:p.lat}));
  return (lat,lon)=>{
    const point=vector(lat,lon);let coverage=0;
    for(const place of places) {
      if(Math.abs(place.lat-lat)*DEG>radius)continue;
      const distanceDot=dot(point,place.p);if(distanceDot<=outer)continue;
      const t=clamp((distanceDot-outer)/(inner-outer),0,1);
      coverage=Math.max(coverage,t*t*(3-2*t));if(coverage===1)break;
    }
    return coverage;
  };
}
// The preview and print use one geographic elevation field and the same scale.
export function relief(lat,lon,land,exaggeration=DEFAULT_EXAGGERATION) {
  return land?terrainHeightMM(lat,lon,exaggeration):0;
}
export function createCap({lat=49.2827,lon=-123.1207,span=36,spanX=span,spanY=span,segments=144,radius=RADIUS_MM,skin=1,land=()=>false,exaggeration=DEFAULT_EXAGGERATION}={}) {
  if (segments<2 || !Number.isInteger(segments) || !Number.isFinite(spanX) || !Number.isFinite(spanY) || spanX<=0 || spanX>=90 || spanY<=0 || spanY>=90 || skin<=0 || !Number.isFinite(exaggeration) || exaggeration<0 || exaggeration>MAX_EXAGGERATION) throw new Error('Invalid cap dimensions.');
  const basis=frame(lat,lon), positions=[], uv=[], indices=[], stride=segments+1, layer=stride*stride;
  for(let side=0;side<2;side++) for(let j=0;j<=segments;j++) for(let i=0;i<=segments;i++) {
    const u=(i/segments-0.5)*spanX*DEG, v=(0.5-j/segments)*spanY*DEG;
    const local=localDirection(u,v), geo=latLon(worldDirection(local,basis));
    const r=side ? radius-skin : radius+relief(geo.lat,geo.lon,land(geo.lat,geo.lon),exaggeration);
    positions.push(local[0]*r,local[1]*r,local[2]*r);
    uv.push((geo.lon+180)/360,(geo.lat+90)/180);
  }
  for(let j=0;j<segments;j++) for(let i=0;i<segments;i++) {
    const a=j*stride+i,b=a+1,c=a+stride,d=c+1;
    indices.push(a,c,b,b,c,d,a+layer,b+layer,c+layer,b+layer,d+layer,c+layer);
  }
  const boundary=[];
  for(let i=0;i<segments;i++) boundary.push(i);
  for(let j=0;j<segments;j++) boundary.push(j*stride+segments);
  for(let i=segments;i>0;i--) boundary.push(segments*stride+i);
  for(let j=segments;j>0;j--) boundary.push(j*stride);
  boundary.forEach((a,i)=>{const b=boundary[(i+1)%boundary.length];indices.push(a,b,a+layer,b,b+layer,a+layer);});
  const minZ=Math.min(...positions.filter((_,i)=>i%3===2));
  for(let i=2;i<positions.length;i+=3) positions[i]-=minZ;
  return {positions,uv,indices};
}
export function binarySTL(mesh) {
  const triangles=mesh.indices.length/3, buffer=new ArrayBuffer(84+triangles*50), view=new DataView(buffer);
  new Uint8Array(buffer,0,80).set(new TextEncoder().encode('Travel Globe | millimetres | curved prototype'));
  view.setUint32(80,triangles,true);
  for(let t=0;t<triangles;t++) {
    const p=mesh.indices.slice(t*3,t*3+3).map(index=>mesh.positions.slice(index*3,index*3+3));
    const n=normalize(cross(p[1].map((x,i)=>x-p[0][i]),p[2].map((x,i)=>x-p[0][i])));
    let offset=84+t*50;
    for(const x of [...n,...p.flat()]) {view.setFloat32(offset,x,true);offset+=4;}
  }
  return buffer;
}
