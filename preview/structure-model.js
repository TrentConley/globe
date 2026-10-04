import * as THREE from 'three';
import {vector,latLon,relief,createCap,DEG} from './geometry.js';

export const DIMENSIONS={
  shellRadius:152.5,shellInnerRadius:151.5,frameRadius:135,frameMemberRadius:2,
  pcbVertexRadius:144.5,pcbThickness:1,baseDiameter:200,baseHeight:30,baseCenterY:-201,
  spineDiameter:12,terrain:25,shellSections:12,
};
const V=(x,y,z)=>new THREE.Vector3(x,y,z);
const material=(color,metalness=0,roughness=.7)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
export const palette={
  frame:material(0xaeb8b2,.65,.34),dark:material(0x273136,.3,.55),
  pcb:material(0x267967,.2,.62),chips:material(0x192628,.1,.65),
  gold:material(0xbc9255,.68,.3),baffles:material(0x738289,.15,.62),
  power:material(0xd6a259,.15,.6),data:material(0x65b2b6,.05,.6),
  led:new THREE.MeshStandardMaterial({color:0xe8b568,emissive:0xb27b2e,emissiveIntensity:.25,roughness:.6}),
};
function mesh(geometry,mat,parent){const m=new THREE.Mesh(geometry,mat);parent.add(m);return m;}
function tag(object,part){object.traverse(o=>{if(o.isMesh)o.userData.part=part;});return object;}
function rod(a,b,r,mat,parent){
 const d=b.clone().sub(a),m=mesh(new THREE.CylinderGeometry(r,r,d.length(),10),mat,parent);
 m.position.copy(a).add(b).multiplyScalar(.5);m.quaternion.setFromUnitVectors(V(0,1,0),d.normalize());return m;
}
function tube(points,r,mat,parent){return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points),Math.max(24,points.length*7),r,6,false),mat,parent);}
function box(x,y,z,mat,parent,position){const m=mesh(new THREE.BoxGeometry(x,y,z),mat,parent);if(position)m.position.copy(position);return m;}
function trianglePrism(points,thickness){
 const normal=points[1].clone().sub(points[0]).cross(points[2].clone().sub(points[0])).normalize();
 const center=points.reduce((a,b)=>a.add(b),V(0,0,0)).multiplyScalar(1/3);
 if(normal.dot(center)<0)normal.negate();
 const top=points.map(p=>p.clone()),bottom=points.map(p=>p.clone().addScaledVector(normal,-thickness));
 const vertices=[...top,...bottom],indices=[0,1,2,3,5,4,0,3,1,1,3,4,1,4,2,2,4,5,2,5,0,0,5,3];
 // Points from the icosahedron have outward winding.
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices.flatMap(p=>p.toArray()),3));g.setIndex(indices);g.computeVertexNormals();return {g,normal,center};
}
export function shellPatch(lon0,lon1,lat0,lat1,land,{nx=36,ny=144,closed=true}={}){
 const positions=[],uv=[],indices=[],stride=nx+1,layer=(nx+1)*(ny+1);
 for(let side=0;side<(closed?2:1);side++)for(let y=0;y<=ny;y++)for(let x=0;x<=nx;x++){
  const lat=lat1-(lat1-lat0)*y/ny,lon=lon0+(lon1-lon0)*x/nx;
  const r=side?151.5:152.5+relief(lat,lon,land(lat,lon),25);
  positions.push(...vector(lat,lon).map(v=>v*r));uv.push((lon+180)/360,(lat+90)/180);
 }
 for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){
  const a=y*stride+x,b=a+1,c=a+stride,d=c+1;indices.push(a,c,b,b,c,d);
  if(closed)indices.push(a+layer,b+layer,c+layer,b+layer,d+layer,c+layer);
 }
 if(closed){
  const edge=[];for(let x=0;x<nx;x++)edge.push(x);for(let y=0;y<ny;y++)edge.push(y*stride+nx);
  for(let x=nx;x>0;x--)edge.push(ny*stride+x);for(let y=ny;y>0;y--)edge.push(y*stride);
  edge.forEach((a,i)=>{const b=edge[(i+1)%edge.length];indices.push(a,b,a+layer,b,b+layer,a+layer);});
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();return g;
}
export function buildAssembly(land,shellMaterial){
 const root=new THREE.Group();root.name='Proposed globe assembly (design study)';
 const shell=new THREE.Group(),frame=new THREE.Group(),lighting=new THREE.Group(),electronics=new THREE.Group(),base=new THREE.Group();
 const groups={shell,frame,lighting,electronics,base};for(const [name,g] of Object.entries(groups)){g.name=name;root.add(g);}
 const sections=[];
 for(let i=0;i<12;i++){
  const lon0=-180+i*30+.04,lon1=lon0+29.92,lon=(lon0+lon1)/2;
  const panel=mesh(shellPatch(lon0,lon1,-86,86,land),shellMaterial,shell);
  panel.name='Illustrative outer section '+(i+1);panel.userData={part:'shell',lon,explode:V(...vector(0,lon))};sections.push(panel);
 }
 const polarCovers=[];
 for(const sign of [-1,1]){
  // The lower cap leaves a nominal 13 mm bore for the 12 mm spine.
  const cover=mesh(shellPatch(-180,180,sign<0?-Math.acos(6.5/151.5)/DEG:86,sign<0?-86:90,land,{nx:96,ny:12}),shellMaterial,shell);
  cover.name=sign<0?'South polar cover with spine opening':'North polar cover';cover.userData.part='shell';polarCovers.push({cover,sign});
 }
 // Load path: base -> central spine -> spokes/rings -> carriers -> exterior mounts.
 const spine=mesh(new THREE.CylinderGeometry(6,6,314,32),palette.frame,frame);spine.position.y=-27;
 for(const latitude of [-48,0,48]){
  const a=latitude*DEG,r=135*Math.cos(a),y=135*Math.sin(a);
  const ring=mesh(new THREE.TorusGeometry(r,2,10,100),palette.frame,frame);ring.rotation.x=Math.PI/2;ring.position.y=y;
  const hub=mesh(new THREE.CylinderGeometry(11,11,8,24),palette.dark,frame);hub.position.y=y;
  for(let i=0;i<4;i++){
   const angle=(i*90+15)*DEG;
   rod(V(9*Math.sin(angle),y,9*Math.cos(angle)),V(r*Math.sin(angle),y,r*Math.cos(angle)),1.65,palette.frame,frame);
  }
 }
 for(let k=0;k<4;k++){
  const lon=k*90+15,pts=[];for(let lat=-80;lat<=80;lat+=5)pts.push(V(...vector(lat,lon)).multiplyScalar(135));
  tube(pts,1.7,palette.frame,frame);
 }
 tag(frame,'frame');
 // A complete 320-facet packaging study, not a population/PCB purchasing count.
 const tessellation=new THREE.IcosahedronGeometry(144.5,3),attr=tessellation.getAttribute('position'),tiles=[];
 for(let i=0;i<attr.count;i+=3){
  const corners=[0,1,2].map(k=>V().fromBufferAttribute(attr,i+k));
  // Reserve the south-pole facets around the spine instead of running a PCB through it.
  if(corners.some(p=>p.y<-140&&Math.hypot(p.x,p.z)<7))continue;
  const c=corners.reduce((a,p)=>a.add(p),V()).multiplyScalar(1/3),pts=corners.map(p=>p.clone().sub(c).multiplyScalar(.92).add(c));
  const {g,normal,center}=trianglePrism(pts,1);
  const tile=new THREE.Group();tile.name='Illustrative carrier tile '+(i/3+1);lighting.add(tile);
  const board=mesh(g,palette.pcb,tile);
  const edges=new THREE.LineSegments(new THREE.EdgesGeometry(g),new THREE.LineBasicMaterial({color:0x62a794,transparent:true,opacity:.4}));tile.add(edges);
  // Driver and connector envelopes on the inward face. Their exact footprints are not selected.
  const chip=box(5,5,1.2,palette.chips,tile);
  chip.quaternion.setFromUnitVectors(V(0,0,1),normal);
  chip.position.copy(center).addScaledVector(normal,-1.6);
  const connector=box(4,2,1.5,palette.dark,tile);
  connector.quaternion.copy(chip.quaternion);connector.position.copy(center).lerp(pts[0],.48).addScaledVector(normal,-1.6);
  // A sparse set of emitters identifies the board face; detailed pitch lives in the prototype view.
  const emitGeometry=new THREE.BoxGeometry(1.2,1.2,.7),emitters=new THREE.InstancedMesh(emitGeometry,palette.led,10);
  const matrix=new THREE.Matrix4(),q=new THREE.Quaternion().setFromUnitVectors(V(0,0,1),normal);let n=0;
  for(let a=0;a<4;a++)for(let b=0;b<4-a;b++){
   const u=(a+1)/6,v=(b+1)/6,p=pts[0].clone().multiplyScalar(u).addScaledVector(pts[1],v).addScaledVector(pts[2],1-u-v).addScaledVector(normal,.4);
   matrix.compose(p,q,V(1,1,1));emitters.setMatrixAt(n++,matrix);
  }
  tile.add(emitters);
  const geo=latLon(center.toArray());tile.userData={lon:geo.lon,part:'lighting',direction:center.clone().normalize()};
  tag(tile,'lighting');tiles.push(tile);
 }
 tessellation.dispose();
 // Sector boards and wiring are envelopes/routes, not released electrical CAD.
 for(let i=0;i<4;i++){
  const a=(i*90+45)*DEG,p=V(55*Math.sin(a),i%2?35:-35,55*Math.cos(a));
  const board=box(35,25,1.6,palette.pcb,electronics,p);
  board.lookAt(p.clone().multiplyScalar(2));
  const chip=box(10,10,2,palette.chips,electronics,p.clone().multiplyScalar(.98));chip.quaternion.copy(board.quaternion);
  const cablePoints=[V(5,-176,0),V(10,-100,6),V(12,p.y-20,10),p];
  tube(cablePoints,.8,palette.power,electronics);
  tube([p,V(p.x*1.55,p.y+15,p.z*1.55),V(p.x*2.1,p.y+20,p.z*2.1)],.55,palette.data,electronics);
 }
 tag(electronics,'electronics');
 const foot=mesh(new THREE.CylinderGeometry(100,100,30,96),palette.dark,base);foot.position.y=-201;
 const trim=mesh(new THREE.TorusGeometry(99.5,.7,8,96),palette.gold,base);trim.rotation.x=Math.PI/2;trim.position.y=-186;
 const collar=mesh(new THREE.CylinderGeometry(18,25,8,32),palette.gold,base);collar.position.y=-182;
 const port=box(11,5,2,palette.chips,base,V(0,-201,100));port.name='Provisional low-voltage inlet';
 tag(base,'base');
 return {root,groups,sections,polarCovers,tiles,dimensions:DIMENSIONS};
}
export function buildPrototype(land,shellMaterial){
 const root=new THREE.Group();root.name='39 x 27 mm optical test concept';
 const boardGroup=new THREE.Group(),baffles=new THREE.Group(),shell=new THREE.Group();root.add(boardGroup,baffles,shell);
 // Active array centered at (0,0); board outline from the reference PCB.
 const board=box(39,51.08,1.6,palette.pcb,boardGroup,V(0,6.76,-4.4));
 for(let row=0;row<9;row++)for(let col=0;col<13;col++)box(2,2,.7,palette.led,boardGroup,V((col-6)*3,(4-row)*3,-3.25));
 box(8,8,1.5,palette.chips,boardGroup,V(0,25,-2.85));
 box(7,4,3,palette.dark,boardGroup,V(-12,29,-2.05));
 box(7,4,3,palette.dark,boardGroup,V(12,29,-2.05));
 tag(boardGroup,'sample-board');
 // Fit the baffle tops to the smooth spherical inner surface used by the actual test STL.
 const spanX=2*Math.asin(39/305)/DEG,spanY=2*Math.asin(27/305)/DEG;
 const cap=createCap({spanX,spanY,segments:72,lat:49.2827,lon:-123.1207,land,exaggeration:25});
 const innerLayer=73*73,centerIndex=(36*73+36)*3;
 const minZ=151.5-cap.positions[innerLayer*3+centerIndex+2];
 const innerZ=(x,y)=>Math.sqrt(151.5**2-x*x-y*y)-minZ;
 const wallPositions=[],wallIndices=[];
 function wall(a,b){
  const direction=b.clone().sub(a),side=V(-direction.y,direction.x,0).normalize().multiplyScalar(.18);
  const xy=[a.clone().sub(side),b.clone().sub(side),b.clone().add(side),a.clone().add(side)];
  const start=wallPositions.length/3;
  for(const p of xy)wallPositions.push(p.x,p.y,-2.85);
  for(const p of xy)wallPositions.push(p.x,p.y,innerZ(p.x,p.y)-.15);
  for(const i of [0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7])wallIndices.push(start+i);
 }
 for(let i=0;i<=13;i++)for(let j=0;j<9;j++)wall(V(i*3-19.5,j*3-13.5,0),V(i*3-19.5,(j+1)*3-13.5,0));
 for(let j=0;j<=9;j++)for(let i=0;i<13;i++)wall(V(i*3-19.5,j*3-13.5,0),V((i+1)*3-19.5,j*3-13.5,0));
 const bg=new THREE.BufferGeometry();bg.setAttribute('position',new THREE.Float32BufferAttribute(wallPositions,3));bg.setIndex(wallIndices);bg.computeVertexNormals();
 mesh(bg,palette.baffles,baffles);tag(baffles,'baffles');
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(cap.positions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(cap.uv,2));geometry.setIndex(cap.indices);geometry.computeVertexNormals();
 mesh(geometry,shellMaterial,shell);tag(shell,'sample-shell');
 return {root,boardGroup,baffles,shell,dimensions:{width:39,height:27,pitch:3,cells:117,boardOutline:[39,51.08],baffleWall:.36,baffleGap:.15},
  minZ,innerZ};
}
