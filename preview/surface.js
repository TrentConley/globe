import landData from './data/land.geojson';
import {elevationMeters} from './elevation.js';
import {DEG,RADIUS_MM,EARTH_KM,createFootprintField,frame,localDirection,worldDirection,latLon,vector,angle} from './geometry.js';

const W=2048,H=1024;
const canvas=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c;};
const pixelAt=(lat,lon)=>(Math.min(H-1,Math.max(0,Math.floor((90-lat)/180*H)))*W+((Math.floor((lon+180)/360*W)%W+W)%W))*4;
export function makeSurface() {
  const mask=canvas(),ctx=mask.getContext('2d',{willReadFrequently:true});ctx.fillStyle='white';
  for(const f of landData.features) {
    const polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;
    for(const rings of polygons) {
      ctx.beginPath();
      for(const ring of rings)ring.forEach(([lon,lat],i)=>{const x=(lon+180)/360*W,y=(90-lat)/180*H;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
      ctx.fill('evenodd');
    }
  }
  const landPixels=ctx.getImageData(0,0,W,H).data;
  const land=(lat,lon)=>landPixels[pixelAt(lat,lon)+3]>127;
  const color=canvas(),colorCtx=color.getContext('2d'),pixels=colorCtx.createImageData(W,H),terrain=new Float32Array(W*H);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++) {
    const index=y*W+x,offset=index*4,isLand=landPixels[offset+3]>127;
    const h=isLand?Math.max(0,elevationMeters(90-(y+0.5)/H*180,(x+0.5)/W*360-180))/9000:0;terrain[index]=h;
    const c=isLand?58+Math.round(h*18):24;
    pixels.data.set(isLand?[c,c+1,c+2,255]:[c,c+2,c+4,255],offset);
  }
  colorCtx.putImageData(pixels,0,0);
  return {color,land,landPixels,terrain,basePixels:pixels};
}
export function makeFootprints(visits,miles,surface,{led=false,lat=49.2827,lon=-123.1207,landOnly=true}={}) {
  let points=visits,displayMiles=miles;
  if(led) {
    const basis=frame(lat,lon),locations=[];
    for(let col=0;col<6;col++)for(let row=0;row<12;row++) {
      const p=worldDirection(localDirection((col-2.5)*14/146.5,(row-5.5)*(1000/144)/146.5),basis);
      locations.push({p,...latLon(p),on:false});
    }
    const radius=miles*1.609344/EARTH_KM;
    for(const visit of visits) {
      const p=vector(visit.lat,visit.lon);let nearest=null,best=Infinity;
      for(const l of locations){const a=angle(p,l.p);if(a<radius)l.on=true;if(a<best){best=a;nearest=l;}}
      if(nearest && best*RADIUS_MM<8.5)nearest.on=true;
    }
    points=locations.filter(p=>p.on);displayMiles=5/RADIUS_MM*EARTH_KM/1.609344;
  }
  const field=createFootprintField(points,displayMiles),c=canvas(),ctx=c.getContext('2d'),image=ctx.createImageData(W,H),extent=displayMiles*1.609344/EARTH_KM/DEG;
  for(let y=0;y<H;y++) {
    const latitude=90-(y+0.5)/H*180,active=points.some(p=>Math.abs(p.lat-latitude)<=extent);
    for(let x=0;x<W;x++) {
      const offset=(y*W+x)*4,longitude=(x+0.5)/W*360-180;
      const coverage=active && (!landOnly || surface.landPixels[offset+3]>127)?field(latitude,longitude):0;
      const v=Math.round(coverage*255);image.data.set([v,v,v,255],offset);
    }
  }
  ctx.putImageData(image,0,0);
  return {canvas:c,pixels:image.data,sample:(lat,lon)=>(!landOnly || surface.land(lat,lon))?field(lat,lon):0};
}
export function paintHighlights(surface,footprints,intensity) {
  const c=canvas(),ctx=c.getContext('2d'),image=ctx.createImageData(W,H);
  for(let i=0;i<W*H;i++) {
    const offset=i*4,a=footprints.pixels[offset]/255*Math.min(1,intensity*2),shade=0.8+surface.terrain[i]*0.2;
    const gold=[245*shade,160*shade,21*shade];
    for(let j=0;j<3;j++)image.data[offset+j]=surface.basePixels.data[offset+j]*(1-a)+gold[j]*a;
    image.data[offset+3]=255;
  }
  ctx.putImageData(image,0,0);return c;
}
