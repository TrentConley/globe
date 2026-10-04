// Reproducible scale calculations and small print-service test pieces. Millimetres.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createCap,binarySTL,DEG,RADIUS_MM,EARTH_KM,milesToMM,createFootprintField,vector,latLon} from '../preview/geometry.js';
import {MAX_ELEVATION_METERS,METERS_TO_GLOBE_MM} from '../preview/elevation.js';
const out='artifacts/engineering';await mkdir(out,{recursive:true});
for(const name of ['prototype-bom.csv','optical-test-log.csv'])await writeFile(out+'/'+name,await readFile('engineering/'+name));
const earth=JSON.parse(await readFile('preview/data/land.geojson','utf8'));
const polygons=earth.features.flatMap(f=>f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates);
function inside(lon,lat,ring){let yes=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if((a[1]>lat)!==(b[1]>lat) && lon<(b[0]-a[0])*(lat-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
const land=(lat,lon)=>polygons.some(rings=>inside(lon,lat,rings[0]) && !rings.slice(1).some(r=>inside(lon,lat,r)));
function audit(mesh){
 const n=mesh.positions.length/3,edges=new Map();let volume=0;const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
 for(let i=0;i<n;i++)for(let d=0;d<3;d++){lo[d]=Math.min(lo[d],mesh.positions[i*3+d]);hi[d]=Math.max(hi[d],mesh.positions[i*3+d]);}
 for(let t=0;t<mesh.indices.length;t+=3){const ids=mesh.indices.slice(t,t+3),[a,b,c]=ids.map(i=>mesh.positions.slice(i*3,i*3+3));
  for(let k=0;k<3;k++){const x=ids[k],y=ids[(k+1)%3],key=x<y?`${x}:${y}`:`${y}:${x}`,e=edges.get(key)||[0,0];e[0]++;e[1]+=x<y?1:-1;edges.set(key,e);}
  volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
 }
 if([...edges.values()].some(([count,winding])=>count!==2 || winding!==0)||volume<=0)throw new Error('Invalid closed print geometry');
 return {triangles:mesh.indices.length/3,boundsMM:hi.map((v,i)=>Number((v-lo[i]).toFixed(4))),volumeMM3:Number(volume.toFixed(4))};
}
const exports=[];
const spanX=2*Math.asin(39/(2*RADIUS_MM))/DEG,spanY=2*Math.asin(27/(2*RADIUS_MM))/DEG;
for(const [name,exaggeration,lat,lon] of [['matrix-shell-vancouver-25x-mm.stl',25,49.2827,-123.1207],['matrix-shell-himalayas-25x-mm.stl',25,28,86],['matrix-shell-smooth-mm.stl',0,49.2827,-123.1207]]){
 const mesh=createCap({spanX,spanY,segments:72,lat,lon,skin:1,land,exaggeration});
 await writeFile(`${out}/${name}`,new Uint8Array(binarySTL(mesh)));exports.push({file:name,...audit(mesh),description:'Closed optical test shell; nominal 39 x 27 mm projected sea-level bounds; supports and finish not included.'});
}
// Simple slabs are control samples; no optical or mechanical performance is asserted.
for(const thickness of [0.6,0.8,1.0,1.2]){
 const positions=[0,0,0,30,0,0,30,30,0,0,30,0,0,0,thickness,30,0,thickness,30,30,thickness,0,30,thickness];
 const indices=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7];
 const mesh={positions,indices};const name=`flat-coupon-${thickness.toFixed(1)}mm.stl`;
 await writeFile(`${out}/${name}`,new Uint8Array(binarySTL(mesh)));exports.push({file:name,...audit(mesh)});
}
const area=4*Math.PI*RADIUS_MM**2,diameter=milesToMM(50)*2;
const pitches=[2,2.5,3,6.944444,10];
const counts=pitches.map(p=>({pitchMM:p,footprintPixelsAcross:diameter/p,wholeSphereSquareCellEstimate:area/(p*p),landAreaLowerBoundEstimate:area*0.29/(p*p),nearestCenterWorstCaseMM:p/Math.sqrt(2)}));
const calc={status:'Engineering study, not a released full-globe manufacturing design',diameterAtSeaLevelMM:305,terrainExaggeration:25,radiusMiles:50,footprintRadiusMM:milesToMM(50),footprintDiameterMM:diameter,highestGridElevationM:MAX_ELEVATION_METERS,highestGridReliefMM:MAX_ELEVATION_METERS*METERS_TO_GLOBE_MM*25,solidBackShellMaximumRadialWallMM:1+MAX_ELEVATION_METERS*METERS_TO_GLOBE_MM*25,areaMM2:area,pitchStudy:counts,prototype:{matrixPitchMM:3,columns:13,rows:9,nominalActiveCellBoundsMM:[39,27],boardOutlineMM:[39,51.08],flatSourceToSphericalShellCornerSagMM:RADIUS_MM-Math.sqrt(RADIUS_MM**2-19.5**2-13.5**2)},powerExamples:[0.05,0.1,0.2,0.5].map(i=>({activePixels:20000,averageCurrentPerLEDmA:i,ledBranchCurrentA:20000*i/1000,railPowerAt3V3W:3.3*20000*i/1000})),exports};
await writeFile(`${out}/calculations.json`,JSON.stringify(calc,null,2));
await writeFile(`${out}/pixel-pitch-study.csv`,'pitch_mm,footprint_pixels_across,whole_sphere_square_cell_estimate,land_area_lower_bound,nearest_center_worst_case_mm\n'+counts.map(x=>Object.values(x).join(',')).join('\n')+'\n');
// Optics are intentionally absent: this is the requested footprint sampled on a 3 mm board.
const center=vector(49.2827,-123.1207),east=[Math.cos(-123.1207*DEG),0,-Math.sin(-123.1207*DEG)];
const north=[center[1]*east[2]-center[2]*east[1],center[2]*east[0]-center[0]*east[2],center[0]*east[1]-center[1]*east[0]];
const field=createFootprintField([{lat:49.2827,lon:-123.1207}],50),rows=[];
for(let row=0;row<9;row++)for(let col=0;col<13;col++){
 const x=(col-6)*3,y=(4-row)*3;let value=0;
 for(let iy=0;iy<5;iy++)for(let ix=0;ix<5;ix++){
  const sx=x+((ix+.5)/5-.5)*3,sy=y+((iy+.5)/5-.5)*3,z=Math.sqrt(RADIUS_MM**2-sx*sx-sy*sy);
  const geo=latLon(center.map((v,i)=>v*z+east[i]*sx+north[i]*sy));if(land(geo.lat,geo.lon))value+=field(geo.lat,geo.lon)/25;
 }
 rows.push({col,row,xMM:x,yMM:y,coverage:Number(value.toFixed(5))});
}
await writeFile(`${out}/vancouver-13x9-test-pattern.json`,JSON.stringify({description:'Land-clipped, area-sampled 50-mile footprint on a 3 mm matrix. Alignment at the center of a 305 mm sphere. This is a command pattern, not simulated diffusion.',rows},null,2));
console.log(JSON.stringify({footprintDiameterMM:diameter,reliefMM:calc.highestGridReliefMM,prototypeCornerSagMM:calc.prototype.flatSourceToSphericalShellCornerSagMM,exports},null,2));
