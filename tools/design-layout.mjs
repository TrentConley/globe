import * as THREE from 'three';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {elevationMeters} from '../preview/elevation.js';
import {METERS_TO_GLOBE_MM} from '../preview/elevation.js';
const req=JSON.parse(await readFile('cad/design/requirements.json'));
const earth=JSON.parse(await readFile('preview/data/land.geojson'));
const polygons=earth.features.flatMap(f=>f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates);
function inside(lon,lat,ring){let yes=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if((a[1]>lat)!==(b[1]>lat)&&lon<(b[0]-a[0])*(lat-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
function land(lat,lon){return polygons.some(r=>inside(lon,lat,r[0])&&!r.slice(1).some(q=>inside(lon,lat,q)));}
const V=(...a)=>new THREE.Vector3(...a),geo=p=>({lat:Math.asin(p.z/p.length())*180/Math.PI,lon:Math.atan2(p.y,p.x)*180/Math.PI});
const g=new THREE.IcosahedronGeometry(1,3),raw=g.attributes.position;
const initial=V().fromBufferAttribute(new THREE.IcosahedronGeometry(1,0).attributes.position,0);
const rotation=new THREE.Quaternion().setFromUnitVectors(initial,V(0,0,1));
const nodes=[],nodeMap=new Map(),faces=[],edges=new Map(),tiles=[];
function node(p){const key=p.toArray().map(v=>v.toFixed(6)).join(',');if(!nodeMap.has(key)){nodeMap.set(key,nodes.length);nodes.push(p.toArray());}return nodeMap.get(key);}
function offset(poly,amount){return poly.map((p,i)=>{const prev=poly[(i+2)%3],next=poly[(i+1)%3];const a=V(prev[0]-p[0],prev[1]-p[1],0).normalize(),b=V(next[0]-p[0],next[1]-p[1],0).normalize();const bis=a.clone().add(b).normalize();return [p[0]+bis.x*amount/Math.sqrt((1-a.dot(b))/2),p[1]+bis.y*amount/Math.sqrt((1-a.dot(b))/2)];});}
function inTri(x,y,t,margin=0){for(let i=0;i<3;i++){const a=t[i],b=t[(i+1)%3];if((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])<margin*Math.hypot(b[0]-a[0],b[1]-a[1]))return false;}return true;}
for(let i=0;i<raw.count;i+=3){
 let ps=[0,1,2].map(k=>V().fromBufferAttribute(raw,i+k).applyQuaternion(rotation).normalize());
 if(ps[1].clone().sub(ps[0]).cross(ps[2].clone().sub(ps[0])).dot(ps[0])<0)[ps[1],ps[2]]=[ps[2],ps[1]];
 const ids=ps.map(node),id=i/3,sector=Math.floor(id/16);faces.push({id,sector,nodes:ids});
 for(let j=0;j<3;j++){const ids2=[ids[j],ids[(j+1)%3]].sort((a,b)=>a-b);edges.set(ids2.join(':'),ids2);}
 const corners=ps.map(p=>p.clone().multiplyScalar(req.pcb_vertex_radius_mm));
 const center=corners.reduce((a,p)=>a.add(p),V()).multiplyScalar(1/3);
 // Start at the longest edge, yielding just a small number of repeated board shapes.
 const lengths=corners.map((p,j)=>p.distanceTo(corners[(j+1)%3]));const first=lengths.indexOf(Math.max(...lengths));
 corners.push(...corners.splice(0,first));
 const ex=corners[1].clone().sub(corners[0]).normalize(),normal=corners[1].clone().sub(corners[0]).cross(corners[2].clone().sub(corners[0])).normalize(),ey=normal.clone().cross(ex);
 const xy=corners.map(p=>{const d=p.clone().sub(center);return [d.dot(ex),d.dot(ey)];});
 const outline=offset(xy,req.pcb_edge_inset_mm),holes=offset(xy,3.4);
 const southKeepout=ps.some(p=>p.z<-.95&&Math.hypot(p.x,p.y)*144.5<9);
 const localToWorld=(x,y,z=0)=>center.clone().addScaledVector(ex,x).addScaledVector(ey,y).addScaledVector(normal,z);
 const points=[];const minY=Math.min(...outline.map(p=>p[1]));
 // Symmetric 2 mm square lattice, one 351-channel driver per tile. Physical rows may fold into logical rows.
 const yStart=Math.ceil((minY+1)/2)*2;let row=0;
 for(let y=yStart;y<=Math.max(...outline.map(p=>p[1]))-1;y+=2,row++){
  for(let col=0;col<22;col++){const x=(col-10.5)*2;if(!inTri(x,y,outline,.9)||holes.some(h=>Math.hypot(x-h[0],y-h[1])<2.5))continue;
   const world=localToWorld(x,y),dir=world.clone().normalize(),ll=geo(dir),r=151.5;
   const p=localToWorld(x,y,.75),b=p.dot(normal),shellZ=-b+Math.sqrt(b*b+r*r-p.lengthSq())+.75;
   points.push({x,y,row,col,lat:ll.lat,lon:ll.lon,land:land(ll.lat,ll.lon),position:world.toArray(),direction:dir.toArray(),inner_z:shellZ});
  }
 }
 // Fold two physical row bands into the chip's 9 switches; each band owns separate CS columns.
 const lower=points.filter(p=>p.row<9).map(p=>p.col),upper=points.filter(p=>p.row>=9).map(p=>p.col);
 const lowMin=Math.min(...lower),lowWidth=Math.max(...lower)-lowMin+1,upMin=Math.min(...upper);
 points.forEach(p=>{p.sw=p.row%9;p.cs=p.row<9?p.col-lowMin:lowWidth+p.col-upMin;if(p.cs>38)throw new Error('CS capacity exceeded');p.channel=p.cs<30?p.sw*30+p.cs:270+p.sw*9+p.cs-30;});
 const populated=!southKeepout&&points.some(p=>p.land);
 const shapeKey=outline.flat().map(v=>Math.abs(v)<.005?'0.00':v.toFixed(2)).join('/');
 tiles.push({id,sector,bus:Math.floor(id%16/4),address:0x30+id%4,shapeKey,southKeepout,populated,center:center.toArray(),ex:ex.toArray(),ey:ey.toArray(),normal:normal.toArray(),outline,holes,leds:points});
}
const sectors=Array.from({length:20},(_,id)=>({id,tiles:tiles.filter(t=>t.sector===id&&t.populated).map(t=>t.id)}));
const types=[...new Set(tiles.map(t=>t.shapeKey))];tiles.forEach(t=>t.type=types.indexOf(t.shapeKey));
const manifest={revision:req.revision,units:'mm',coordinateSystem:'CAD right-handed: +Z north, +X lat0/lon0, +Y lat0/lon90',requirements:req,nodes,edges:[...edges.values()],faces,tiles,sectors,summary:{nodes:nodes.length,edges:edges.size,facets:tiles.length,boardTypes:types.length,populatedTiles:tiles.filter(t=>t.populated).length,leds:tiles.filter(t=>t.populated).reduce((n,t)=>n+t.leds.length,0),landLEDs:tiles.filter(t=>t.populated).reduce((n,t)=>n+t.leds.filter(p=>p.land).length,0),maxLEDsPerTile:Math.max(...tiles.map(t=>t.leds.length)),activeSectors:sectors.filter(s=>s.tiles.length).length,types}};
// Three removable magnetic shell supports per original icosahedron face.
const degree=nodes.map((_,i)=>[...edges.values()].filter(e=>e.includes(i)).length);
manifest.anchors=[];
for(let sector=0;sector<20;sector++){
 const major=[...new Set(faces.filter(f=>f.sector===sector).flatMap(f=>f.nodes))].filter(i=>degree[i]===5);
 const vs=major.map(i=>V(...nodes[i]));if(vs.length!==3)throw new Error('Sector boundary');
 const normals=vs.map((v,i)=>v.clone().cross(vs[(i+1)%3]).normalize());
 const center=vs.reduce((a,v)=>a.add(v),V()).normalize();normals.forEach(n=>{if(n.dot(center)<0)n.negate();});
 const candidates=[];
 for(const t of tiles.filter(t=>t.sector===sector))for(let hole=0;hole<3;hole++){
  const h=t.holes[hole],p=V(...t.center).addScaledVector(V(...t.ex),h[0]).addScaledVector(V(...t.ey),h[1]),dir=p.clone().normalize();
  if(Math.min(...normals.map(n=>n.dot(dir)*152.5))<5)continue;
  candidates.push({tile:t.id,hole,point:p,dir});
 }
 for(const v of vs){const best=candidates.reduce((a,b)=>a.dir.dot(v)>b.dir.dot(v)?a:b);manifest.anchors.push({sector,tile:best.tile,hole:best.hole,pcbPoint:best.point.toArray(),direction:best.dir.toArray(),magnet:'4 mm diameter x 2 mm N52, matched pairs',gap_mm:.2});candidates.splice(candidates.indexOf(best),1);}
}
if(manifest.summary.maxLEDsPerTile>351)throw new Error('Driver channel capacity exceeded');
await mkdir('cad/generated',{recursive:true});await writeFile('cad/generated/layout.json',JSON.stringify(manifest));
await writeFile('engineering/release/layout-summary.json',JSON.stringify(manifest.summary,null,2));
// Regular elevation grid for the Python CAD surface mesher; meters are retained separately from exaggeration.
const elev=[];for(let y=0;y<=360;y++)for(let x=0;x<=720;x++){const lat=-90+y*.5,lon=-180+x*.5;elev.push(land(lat,lon)?Math.max(0,elevationMeters(lat,lon))*METERS_TO_GLOBE_MM*25:0);}
await writeFile('cad/generated/terrain.json',JSON.stringify({width:721,height:361,step:.5,heights_mm:elev}));
console.log(JSON.stringify(manifest.summary,null,2));
