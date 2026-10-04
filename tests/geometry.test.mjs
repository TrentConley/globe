import test from 'node:test';
import assert from 'node:assert/strict';
import {vector,latLon,validateProject,createFootprintField,createCap,binarySTL,milesToMM,EARTH_KM,DEG,relief} from '../preview/geometry.js';

import {elevationMeters,terrainHeightMM,METERS_TO_GLOBE_MM} from '../preview/elevation.js';

test('Earth-to-globe scale preserves the 50-mile footprint constraint',()=>{
  assert.ok(Math.abs(milesToMM(50)-1.92610752633)<1e-9);
  assert.equal(milesToMM(100),milesToMM(50)*2);
});
test('Coordinates round-trip in both hemispheres and across the date line',()=>{
  for(const [lat,lon] of [[37.7,-122.4],[-33.8,151.2],[0,179.9],[-89.9,-170]]) {
    const actual=latLon(vector(lat,lon));assert.ok(Math.abs(actual.lat-lat)<1e-8);assert.ok(Math.abs(actual.lon-lon)<1e-8);
  }
});
test('Vancouver lights nearby places while distant Canada and South Dakota stay dark',()=>{
  const coverage=createFootprintField([{lat:49.2827,lon:-123.1207}],50);
  assert.equal(coverage(49.2827,-123.1207),1);
  assert.equal(coverage(49.2488,-122.9805),1); // Burnaby
  for(const [lat,lon] of [[50.6745,-120.3273],[53.5461,-113.4938],[45.5019,-73.5674],[44.3683,-100.351]])assert.equal(coverage(lat,lon),0);
});
test('Distant visits never illuminate their midpoint',()=>{
  const coverage=createFootprintField([{lat:0,lon:0},{lat:0,lon:20}],50);
  assert.equal(coverage(0,0),1);assert.equal(coverage(0,20),1);assert.equal(coverage(0,10),0);
});
test('Overlapping visits form a union independent of order and repeated visits',()=>{
  const a={lat:37.7749,lon:-122.4194},b={lat:37.3382,lon:-121.8863};
  const joined=createFootprintField([a,b],50),reversed=createFootprintField([b,a],50),repeated=createFootprintField([a,b,a],50);
  assert.equal(joined(37.55,-122.15),1);
  for(let lat=36.8;lat<38.5;lat+=0.1)for(let lon=-123.1;lon<-121;lon+=0.1){assert.equal(joined(lat,lon),reversed(lat,lon));assert.equal(joined(lat,lon),repeated(lat,lon));}
});
test('Footprints work across the date line and at the poles',()=>{
  const date=createFootprintField([{lat:0,lon:179.8}],50);
  assert.equal(date(0,-179.9),1);assert.equal(date(0,170),0);
  const pole=createFootprintField([{lat:89.9,lon:0}],50);
  assert.equal(pole(89.9,180),1);assert.equal(pole(88,0),0);
});
test('Coverage has a softened edge and no illumination beyond its configured radius',()=>{
  const c=createFootprintField([{lat:0,lon:0}],50),degrees=50*1.609344/EARTH_KM/DEG;
  assert.equal(c(0,degrees*0.8),1);assert.ok(c(0,degrees*0.92)>0 && c(0,degrees*0.92)<1);
  assert.ok(c(0,degrees)<1e-8);assert.equal(c(0,degrees*1.01),0);
});
test('Version 1 migration preserves places, discards connecting lines, and does not mutate input',()=>{
  const old={version:1,stops:[{name:'A',lat:0,lon:0,connect:false},{name:'B',lat:0,lon:180,connect:true}]};
  const before=JSON.stringify(old),result=validateProject(old);
  assert.equal(JSON.stringify(old),before);
  assert.deepEqual(result,{version:2,radiusMiles:50,visits:[{name:'A',lat:0,lon:0},{name:'B',lat:0,lon:180}]});
});
test('New travel files retain footprint radius and reject malformed or excessive data',()=>{
  const valid={version:2,radiusMiles:75,visits:[{name:'A',lat:0,lon:0}]};
  assert.deepEqual(validateProject(valid),valid);
  for(const value of [null,{version:3,visits:[]},{version:2,visits:[{name:'bad',lat:91,lon:0}]},{version:2,visits:[{name:'bad',lat:0,lon:Infinity}]},{version:2,visits:Array(201).fill(valid.visits[0])},{...valid,radiusMiles:0},{...valid,radiusMiles:'50'}])assert.throws(()=>validateProject(value));
});
function inspect(mesh) {
  const edges=new Map();let volume=0,minArea=Infinity;
  for(let t=0;t<mesh.indices.length;t+=3) {
    const ids=mesh.indices.slice(t,t+3),[a,b,c]=ids.map(i=>mesh.positions.slice(i*3,i*3+3));
    for(let k=0;k<3;k++) {
      const from=ids[k],to=ids[(k+1)%3],key=from<to?`${from}:${to}`:`${to}:${from}`,e=edges.get(key)||{count:0,winding:0};
      e.count++;e.winding+=from<to?1:-1;edges.set(key,e);
    }
    const ab=b.map((x,i)=>x-a[i]),ac=c.map((x,i)=>x-a[i]);
    minArea=Math.min(minArea,Math.hypot(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])/2);
    volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
  }
  for(const e of edges.values()){assert.equal(e.count,2,'Every edge must have two adjacent faces');assert.equal(e.winding,0,'Adjacent faces must have opposite edge winding');}
  assert.ok(volume>0,'Positive volume with outward faces');assert.ok(minArea>1e-9,'No degenerate triangles');
  return volume;
}
test('The production-resolution print shell is closed, outward-facing and full scale',()=>{
  const mesh=createCap({land:()=>true,exaggeration:25});const volume=inspect(mesh);
  const xs=mesh.positions.filter((_,i)=>i%3===0),width=Math.max(...xs)-Math.min(...xs);
  assert.ok(width>94 && width<96);assert.ok(volume>8000 && volume<18000);
  const stl=binarySTL(mesh);assert.equal(new DataView(stl).getUint32(80,true),mesh.indices.length/3);assert.equal(stl.byteLength,84+mesh.indices.length/3*50);
});
test('The reusable shell keeps at least a 1 mm wall across raised land and ocean',()=>{
  const mesh=createCap({segments:36,land:lat=>lat>49.28,exaggeration:40});inspect(mesh);
  const layer=mesh.positions.length/6;
  for(let i=0;i<layer;i++) {
    const a=mesh.positions.slice(i*3,i*3+3),b=mesh.positions.slice((i+layer)*3,(i+layer)*3+3);
    assert.ok(Math.hypot(...a.map((x,j)=>x-b[j]))>=1-1e-9);
  }
  assert.throws(()=>createCap({skin:0}));
});
test('LED carrier is independently closed and has a 1.6 mm wall',()=>{
  const mesh=createCap({segments:24,radius:144.6,skin:1.6,exaggeration:0});inspect(mesh);
  const n=mesh.positions.length/6;
  assert.ok(Math.abs(Math.hypot(...mesh.positions.slice(0,3).map((v,j)=>v-mesh.positions[n*3+j]))-1.6)<1e-9);
});


test('Geographic elevation agrees with independently sampled source coordinates',()=>{
  for(const [lat,lon,meters] of [[28,86,4045.45],[39.7392,-104.9903,1719.60],[28,-81,11.50],[46.5,10,2373.16],[-20,-68,3708.97],[38.5,-98,478.25],[0,-150,-4124.97],[49.2827,-123.1207,186.50]]) {
    assert.ok(Math.abs(elevationMeters(lat,lon)-meters)<1,`Elevation at ${lat}, ${lon}`);
  }
});
test('Terrain sampling is continuous across the date line and converges at each pole',()=>{
  for(const lat of [-89,-40,0,45,89])assert.equal(elevationMeters(lat,-180),elevationMeters(lat,180));
  for(const lat of [-90,90])for(const lon of [-180,-70,0,80,180])assert.equal(elevationMeters(lat,lon),elevationMeters(lat,0));
  assert.ok(Math.abs(elevationMeters(30,179.999999)-elevationMeters(30,-179.999999))<0.1);
});
test('Exaggeration uses actual physical scale and never carves into the sea-level shell',()=>{
  assert.equal(terrainHeightMM(28,86,4),terrainHeightMM(28,86,1)*4);
  assert.ok(Math.abs(8849*METERS_TO_GLOBE_MM-0.2118)<0.001);
  assert.equal(terrainHeightMM(0,-150,12),0);
  assert.equal(relief(28,86,false,4),0);
  assert.equal(relief(28,86,true,0),0);
});
test('Printed relief follows the elevation field and changes only with the terrain setting',()=>{
  const raised=createCap({lat:28,lon:86,segments:4,land:()=>true,exaggeration:4});
  const flat=createCap({lat:28,lon:86,segments:4,land:()=>true,exaggeration:0});
  const center=12*3;
  assert.ok(Math.abs(Math.hypot(...raised.positions.slice(center,center+3).map((v,i)=>v-raised.positions[center+25*3+i]))-1-terrainHeightMM(28,86,4))<1e-8);
  assert.ok(Math.abs(Math.hypot(...flat.positions.slice(center,center+3).map((v,i)=>v-flat.positions[center+25*3+i]))-1)<1e-8);
  for(const exaggeration of [-1,41,NaN,Infinity])assert.throws(()=>createCap({exaggeration}));
});
