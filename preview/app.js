import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RADIUS_MM,DEG,vector,latLon,normalize,relief,createCap,binarySTL,milesToMM,validateProject} from './geometry.js';
import {makeSurface,makeFootprints,paintHighlights} from './surface.js';
import {elevationMeters,MAX_ELEVATION_METERS,METERS_TO_GLOBE_MM,DEFAULT_EXAGGERATION,MAX_EXAGGERATION} from './elevation.js';

const $=id=>document.getElementById(id),KEY='travel-globe-areas-v2',LEGACY_KEY='travel-globe-study-v1';
const presets={
  vancouver:[['Vancouver',49.2827,-123.1207]],
  west:[['Vancouver',49.2827,-123.1207],['Seattle',47.6062,-122.3321],['Portland',45.5152,-122.6784],['San Francisco',37.7749,-122.4194],['Oakland',37.8044,-122.2712],['San Jose',37.3382,-121.8863],['Los Angeles',34.0522,-118.2437],['Las Vegas',36.1699,-115.1398],['Denver',39.7392,-104.9903]],
  bay:[['San Francisco',37.7749,-122.4194],['Oakland',37.8044,-122.2712],['San Jose',37.3382,-121.8863]],
  europe:[['Lisbon',38.7223,-9.1393],['Barcelona',41.3874,2.1686],['Paris',48.8566,2.3522],['Rome',41.9028,12.4964]]
};
const demoVisits=key=>presets[key].map(([name,lat,lon])=>({name,lat,lon}));
let state={visits:demoVisits('vancouver'),demo:true,radius:50,exaggeration:DEFAULT_EXAGGERATION,terrainRevision:3,brightness:65,landOnly:true,capLat:49.2827,capLon:-123.1207};
let storageOK=true,migrated=false;
try {
  const raw=localStorage.getItem(KEY),legacy=raw?null:localStorage.getItem(LEGACY_KEY);
  if(raw || legacy) {
    const saved=JSON.parse(raw || legacy);
    // Preserve the original v1 storage entry. Only the old illustrative demo is replaced.
    if(raw || !saved.demo) {
      const project=validateProject(raw?{version:2,visits:saved.visits,radiusMiles:saved.radius}:{version:1,stops:saved.stops,radiusMiles:saved.radius});
      const ranges={exaggeration:[0,MAX_EXAGGERATION],brightness:[0,100],capLat:[-90,90],capLon:[-180,180]};
      for(const [key,[min,max]] of Object.entries(ranges))if(typeof saved[key]==='number' && Number.isFinite(saved[key]) && saved[key]>=min && saved[key]<=max)state[key]=saved[key];
      // Upgrade the former default once, without replacing custom terrain or travel settings.
      if(saved.terrainRevision!==3 && [4,12,24].includes(saved.exaggeration))state.exaggeration=DEFAULT_EXAGGERATION;
      if(saved.exaggeration===undefined && saved.height===0)state.exaggeration=0;
      state={...state,visits:project.visits,radius:project.radiusMiles,demo:saved.demo===true,landOnly:saved.landOnly!==false};
      migrated=!raw;
    }
  }
} catch {storageOK=false;}
let toastTimer;
function toast(text) { $('toast').textContent=text;$('toast').style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').style.display='none',5500); }
function save() {
  try{localStorage.setItem(KEY,JSON.stringify(state));storageOK=true;}catch{storageOK=false;}
  $('storage-note').textContent=storageOK?'Saved in this browser. Export a backup to keep or move your travel history.':'Browser storage is unavailable. Export your travels before closing this page.';
}
function download(data,filename,type) {
  const url=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
const scene=new THREE.Scene();scene.background=new THREE.Color('#101619');
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
$('scene').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(38,1,0.1,2500);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=190;controls.maxDistance=1100;
scene.add(new THREE.HemisphereLight(0xcbd1d6,0x242628,1.15));
const keyLight=new THREE.DirectionalLight(0xf4f4f1,4.0);scene.add(keyLight);
const rim=new THREE.DirectionalLight(0xb8c5cc,0.8);rim.position.set(-400,150,-100);scene.add(rim);
const composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
const bloom=new UnrealBloomPass(new THREE.Vector2(1,1),0.18,0.25,1.0);composer.addPass(bloom);composer.addPass(new OutputPass());
const surface=makeSurface();
let coverage,coverageTexture,colorTexture,mesh,mode='globe',adding=false;
const material=new THREE.MeshStandardMaterial({roughness:0.85,metalness:0.10,emissive:0xff9d08,emissiveIntensity:0.3});
const stand=new THREE.Group();
const baseMat=new THREE.MeshStandardMaterial({color:0x303130,roughness:0.65,metalness:0.68});
const base=new THREE.Mesh(new THREE.CylinderGeometry(63,69,8,96),baseMat);base.position.y=-181;stand.add(base);
const stem=new THREE.Mesh(new THREE.CylinderGeometry(5,8,24,32),baseMat);stem.position.y=-165;stand.add(stem);
const rimRing=new THREE.Mesh(new THREE.TorusGeometry(64,0.35,8,96),new THREE.MeshStandardMaterial({color:0x8c7047,metalness:0.8,roughness:0.5}));rimRing.rotation.x=Math.PI/2;rimRing.position.y=-177;stand.add(rimRing);scene.add(stand);

function toGeometry(data,fixDateLine=false) {
  let geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(data.positions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(data.uv,2));geometry.setIndex(data.indices);geometry.computeVertexNormals();
  if(fixDateLine) {
    const indexed=geometry;geometry=indexed.toNonIndexed();indexed.dispose();const uv=geometry.getAttribute('uv');
    for(let i=0;i<uv.count;i+=3) {
      const us=[uv.getX(i),uv.getX(i+1),uv.getX(i+2)];
      if(Math.max(...us)-Math.min(...us)>0.5)for(let j=0;j<3;j++)if(us[j]<0.5)uv.setX(i+j,us[j]+1);
    }
  }
  geometry.computeBoundingSphere();return geometry;
}
function globeGeometry() {
  const width=720,height=360,positions=[],uv=[],indices=[];
  for(let j=0;j<=height;j++)for(let i=0;i<=width;i++) {
    const lat=90-j/height*180,lon=i/width*360-180;
    const r=RADIUS_MM+relief(lat,lon,surface.land(lat,lon),state.exaggeration);
    positions.push(...vector(lat,lon).map(x=>x*r));uv.push(i/width,1-j/height);
  }
  for(let j=0;j<height;j++)for(let i=0;i<width;i++) {const a=j*(width+1)+i,b=a+1,c=a+width+1,d=c+1;if(j>0)indices.push(a,c,b);if(j<height-1)indices.push(b,c,d);}
  return toGeometry({positions,uv,indices});
}
function capOptions(extra={}) {return {lat:state.capLat,lon:state.capLon,land:surface.land,exaggeration:state.exaggeration,...extra};}
function rebuildGeometry() {
  let geometry;
  if(mode==='cap') {
    const capMeshData=createCap(capOptions());geometry=toGeometry(capMeshData,true);geometry.computeBoundingBox();const center=geometry.boundingBox.getCenter(new THREE.Vector3());geometry.translate(-center.x,-center.y,-center.z);
  } else geometry=globeGeometry();
  if(mesh){scene.remove(mesh);mesh.geometry.dispose();}
  mesh=new THREE.Mesh(geometry,material);scene.add(mesh);stand.visible=mode==='globe';
}
function updateFinish() {
  colorTexture?.dispose();colorTexture=new THREE.CanvasTexture(paintHighlights(surface,coverage,state.brightness/100));
  colorTexture.colorSpace=THREE.SRGBColorSpace;colorTexture.wrapS=THREE.RepeatWrapping;colorTexture.anisotropy=renderer.capabilities.getMaxAnisotropy();
  material.map=colorTexture;material.emissiveIntensity=state.brightness/100*0.45;material.needsUpdate=true;
}
function rebuildCoverage() {
  coverage=makeFootprints(state.visits,state.radius,surface,{led:mode==='cap' && $('led').checked,lat:state.capLat,lon:state.capLon,landOnly:state.landOnly});
  coverageTexture?.dispose();coverageTexture=new THREE.CanvasTexture(coverage.canvas);coverageTexture.wrapS=THREE.RepeatWrapping;
  coverageTexture.anisotropy=renderer.capabilities.getMaxAnisotropy();material.emissiveMap=coverageTexture;updateFinish();
}
function visitCenter() {
  if(!state.visits.length)return {lat:state.capLat,lon:state.capLon};
  const sum=state.visits.reduce((s,p)=>vector(p.lat,p.lon).map((x,i)=>x+s[i]),[0,0,0]);
  return Math.hypot(...sum)<1e-6?state.visits[0]:latLon(normalize(sum));
}
function focus() {
  controls.target.set(0,0,0);
  const rect=$('scene').getBoundingClientRect(),fit=Math.max(1,1/(Math.min(1,rect.width/rect.height)*1.25));
  if(mode==='globe') {const p=visitCenter();camera.position.set(...vector(p.lat,p.lon).map(x=>x*660*fit));controls.minDistance=185;controls.maxDistance=Math.max(1100,660*fit*1.5);}
  else {camera.position.set(85*fit,65*fit,230*fit);controls.minDistance=65;controls.maxDistance=Math.max(500,350*fit);}
  camera.up.set(0,1,0);controls.update();
}
function updateLabels() {
  $('radius-value').textContent=`${state.radius} mi`;$('width-note').textContent=`About ${(milesToMM(state.radius)*2).toFixed(1)} mm across on the globe. A soft area around each visit; overlapping areas merge.`;
  $('relief-value').textContent=`${state.exaggeration}×`;$('terrain-note').textContent=`Real elevation, vertically exaggerated. Highest sampled terrain: ${(MAX_ELEVATION_METERS*METERS_TO_GLOBE_MM*state.exaggeration).toFixed(2)} mm above the shell.`;$('brightness-value').textContent=`${state.brightness}%`;
  $('scale-main').textContent=mode==='globe'?'Ø 305 mm':'36° section · ≈ 95 mm across';
  $('scale-detail').textContent=mode==='globe'?'12-inch nominal globe · real elevation relief':`${state.capLat.toFixed(2)}°, ${state.capLon.toFixed(2)}° · fixed terrain · changing visited areas`;
  $('project-kind').textContent=state.demo?'Illustrative places — replace them with your own visits.':'Your travel study · stored on this device';
}
function listVisits() {
  $('visit-count').textContent=`${state.visits.length} ${state.visits.length===1?'place':'places'}`;$('visits').replaceChildren();
  if(!state.visits.length){const p=document.createElement('p');p.className='empty';p.textContent='Your story starts anywhere. Add a place below, or click a point on the globe.';$('visits').append(p);}
  state.visits.forEach((p,i)=>{
    const li=document.createElement('li');
    const name=document.createElement('div');name.className='stop-name';name.textContent=p.name;
    const meta=document.createElement('div');meta.className='stop-meta';meta.textContent=`${p.lat.toFixed(2)}°, ${p.lon.toFixed(2)}°`;
    const remove=document.createElement('button');remove.className='stop-remove';remove.textContent='×';remove.setAttribute('aria-label',`Remove ${p.name}`);
    remove.onclick=()=>{const next=state.visits.map(x=>({...x}));next.splice(i,1);commit(next);};
    li.append(name,meta,remove);
    $('visits').append(li);
  });
}
function commit(visits,demo=false,radiusMiles=state.radius) {
  try{const project=validateProject({version:2,visits,radiusMiles});state.visits=project.visits;state.radius=project.radiusMiles;$('radius').value=state.radius;}catch(e){toast(e.message);return false;}
  state.demo=demo;rebuildCoverage();listVisits();updateLabels();save();return true;
}
function setMode(value) {
  mode=value;$('view-globe').classList.toggle('active',mode==='globe');$('view-cap').classList.toggle('active',mode==='cap');
  $('view-globe').setAttribute('aria-pressed',String(mode==='globe'));$('view-cap').setAttribute('aria-pressed',String(mode==='cap'));
  $('print-controls').hidden=mode!=='cap';$('add-mode').disabled=mode==='cap';
  adding=false;$('add-mode').classList.remove('active');$('add-mode').setAttribute('aria-pressed','false');renderer.domElement.style.cursor='grab';
  rebuildCoverage();rebuildGeometry();updateLabels();focus();
}
$('view-globe').onclick=()=>setMode('globe');$('view-cap').onclick=()=>setMode('cap');$('focus').onclick=focus;
$('load-demo').onclick=()=>{
  if(state.visits.length && !state.demo && !confirm('Replace this travel study with the sample? Export a backup first if you want to keep it.'))return;
  commit(demoVisits($('demo').value),true,50);const c=visitCenter();state.capLat=c.lat;state.capLon=c.lon;$('cap-lat').value=c.lat.toFixed(2);$('cap-lon').value=c.lon.toFixed(2);rebuildCoverage();rebuildGeometry();updateLabels();save();focus();
};
$('add-form').onsubmit=e=>{
  e.preventDefault();const lat=Number($('latitude').value),lon=Number($('longitude').value),name=$('place-name').value.trim();
  if(commit([...state.visits,{name,lat,lon}])){$('place-name').value='';toast('Destination added. Your travel history is saved locally.');}
};
$('clear').onclick=()=>{if(state.visits.length && confirm('Clear all destinations from this browser? Export a backup first to keep them.'))commit([]);};
for(const [id,key] of [['radius','radius'],['relief','exaggeration'],['brightness','brightness']]) {
  $(id).value=state[key];let timer;
  $(id).oninput=()=>{state[key]=Number($(id).value);updateLabels();clearTimeout(timer);timer=setTimeout(()=>{if(key==='radius')rebuildCoverage();else if(key==='brightness')updateFinish();else rebuildGeometry();save();},90);};
}
$('led').onchange=()=>{rebuildCoverage();};
$('land-only').checked=state.landOnly;$('land-only').onchange=()=>{state.landOnly=$('land-only').checked;rebuildCoverage();save();};
for(const [id,key,min,max] of [['cap-lat','capLat',-90,90],['cap-lon','capLon',-180,180]]) {
  $(id).value=state[key];$(id).onchange=()=>{const value=Number($(id).value);if($(id).value==='' || !Number.isFinite(value) || value<min || value>max){$(id).value=state[key];toast('Enter a valid latitude and longitude.');return;}state[key]=value;rebuildCoverage();rebuildGeometry();updateLabels();save();};
}
$('center-cap').onclick=()=>{const c=visitCenter();state.capLat=c.lat;state.capLon=c.lon;$('cap-lat').value=c.lat.toFixed(2);$('cap-lon').value=c.lon.toFixed(2);rebuildCoverage();rebuildGeometry();updateLabels();save();focus();};
$('export-stl').onclick=()=>{
  const cap=createCap(capOptions());download(binarySTL(cap),'globe-shell-light-only-mm.stl','model/stl');
  toast('Shell exported in millimetres. Print in translucent material for the lighting test; STL has no color or lighting.');
};
$('export-carrier').onclick=()=>{download(binarySTL(createCap({lat:state.capLat,lon:state.capLon,radius:144.6,skin:1.6,exaggeration:0})), 'globe-led-carrier-mm.stl','model/stl');toast('Carrier exported. This is a blank curved backing; strip positioning and temporary spacers are described in the build guide.');};
$('export-json').onclick=()=>download(JSON.stringify({version:2,visits:state.visits,radiusMiles:state.radius},null,2),'my-globe-travels.json','application/json');
$('import-json').onclick=()=>$('file-input').click();
$('file-input').onchange=async()=>{
  const file=$('file-input').files[0];if(!file)return;
  try {
    if(file.size>250000)throw new Error('Travel JSON must be smaller than 250 KB.');
    const project=validateProject(JSON.parse(await file.text()));
    if(state.visits.length && !state.demo && !confirm('Replace this travel study with the imported destinations?'))return;
    if(commit(project.visits,false,project.radiusMiles)){focus();toast('Travel history imported. Export a copy whenever you update it.');}
  }catch(e){toast(`Import failed: ${e.message}`);}finally{$('file-input').value='';}
};
$('add-mode').onclick=()=>{adding=!adding;$('add-mode').classList.toggle('active',adding);$('add-mode').setAttribute('aria-pressed',String(adding));renderer.domElement.style.cursor=adding?'crosshair':'grab';if(adding)toast('Click the globe to fill in coordinates, then name and add the place.');};
let down;
renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);
renderer.domElement.addEventListener('pointerup',e=>{
  if(!adding || mode!=='globe' || !down || Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
  const rect=renderer.domElement.getBoundingClientRect(),p=new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,1-(e.clientY-rect.top)/rect.height*2),ray=new THREE.Raycaster();ray.setFromCamera(p,camera);
  const hit=ray.intersectObject(mesh)[0];if(!hit)return;const geo=latLon(hit.point.toArray());$('latitude').value=geo.lat.toFixed(4);$('longitude').value=geo.lon.toFixed(4);$('place-name').focus();toast('Coordinates selected. Name the destination, then add it to your globe.');
});
const resize=()=>{const {width,height}=$('scene').getBoundingClientRect();renderer.setSize(width,height);composer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();};
new ResizeObserver(resize).observe($('scene'));
rebuildCoverage();rebuildGeometry();listVisits();updateLabels();save();focus();resize();$('loading').hidden=true;
// Light from the side in camera space so relief remains legible at every orbit/zoom.
const lightRight=new THREE.Vector3(),lightUp=new THREE.Vector3(),lightFront=new THREE.Vector3();
renderer.setAnimationLoop(()=>{
  controls.update();camera.updateMatrixWorld();
  lightRight.setFromMatrixColumn(camera.matrixWorld,0);lightUp.setFromMatrixColumn(camera.matrixWorld,1);
  lightFront.copy(camera.position).sub(controls.target).normalize();
  keyLight.position.copy(controls.target).addScaledVector(lightFront,350).addScaledVector(lightRight,-650).addScaledVector(lightUp,480);
  rim.position.copy(controls.target).addScaledVector(lightFront,-250).addScaledVector(lightRight,600).addScaledVector(lightUp,150);
  composer.render();
});
// Read-only measurements for inspection and repeatable browser smoke checks.
window.globeStudy={elevationAt:elevationMeters,terrainHeightAt:(lat,lon)=>relief(lat,lon,surface.land(lat,lon),state.exaggeration),coverageAt:(lat,lon)=>coverage.sample(lat,lon),snapshot:()=>JSON.parse(JSON.stringify({...state,mode})),dimensions:()=>({diameterMM:305,capSpanDegrees:36,skinMM:1,footprintDiameterMM:milesToMM(state.radius)*2})};

if(migrated)toast('Saved places recovered. Old connecting lines are no longer shown; the original history is still preserved.');
