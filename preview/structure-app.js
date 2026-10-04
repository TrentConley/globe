import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {makeSurface,makeFootprints,paintHighlights} from './surface.js';
import {buildAssembly,buildPrototype} from './structure-model.js';

const $=id=>document.getElementById(id);
const parts={
 shell:{title:'Raised terrain shell',copy:'A translucent printed surface with a charcoal finish. The mountains are real displaced geometry at 25×. Visiting a new place changes its illumination, while the shell stays fixed. The section seams shown here still need joint and light-blocking details.',specs:[['Sea-level outside diameter','305 mm'],['Smooth underside radius','151.5 mm'],['Base wall, radial','1 mm + raised terrain'],['Section layout','12 gores + polar covers']],color:'#797e7a'},
 frame:{title:'Internal support frame',copy:'The base supports a central spine. Spokes connect it to rings, and meridian ribs link the rings. Carrier brackets and shell locating clips still need detailed design; the floating tiles show where those mounts must reach.',specs:[['Spine diameter','12 mm'],['Ring centerline radius','135 mm spherical'],['Ring tube diameter','4 mm'],['Load and joint validation','Pending']],color:'#adb8b2'},
 lighting:{title:'LED carrier tiles',copy:'Small planar boards approximate the sphere. Amber emitters face outward; driver and connector envelopes face inward. The sparse dots identify the light-emitting side, not the final resolution. Full-globe optical baffles are not shown.',specs:[['Packaging study','320 triangular facets'],['PCB corner radius','144.5 mm'],['Board thickness study','1 mm'],['Final surface pitch target','2–2.5 mm']],color:'#4f9f86'},
 electronics:{title:'Sector electronics & wiring',copy:'Four example sector-board envelopes and symbolic cable paths show the interior space claim. Amber lines represent power and blue-green lines represent data. These paths are not a wiring schematic or a complete harness.',specs:[['Controller board envelopes','35 × 25 mm'],['Branches shown','4, illustrative'],['Power architecture','Protected low-voltage branches'],['Final boards & cable restraints','Pending']],color:'#66b4b6'},
 base:{title:'Weighted display base',copy:'A charcoal base and brass-colored collar hold the central spine. The power inlet is a position study. Ballast, fasteners, feet, strain relief and ventilation must be designed around the measured finished mass and heat.',specs:[['Base envelope','Ø 200 × 30 mm'],['Nominal overall height','368.5 mm before relief'],['Globe mounting','Fixed, no motor'],['Tip resistance & thermal tests','Pending']],color:'#b99c6b'},
 'sample-shell':{title:'Small curved terrain sample',copy:'This uses the same Vancouver geometry as the supplied small test STL: a 305 mm globe, a 1 mm radial base wall, and 25× terrain. The gold patch illustrates one 50-mile visit. Its physical brightness and edge spread still need testing.',specs:[['Nominal active area','39 × 27 mm'],['Terrain','Vancouver, 25×'],['Print geometry','Included in build package'],['Finish & optical validation','Pending']],color:'#797e7a'},
 baffles:{title:'Shaped optical cells',copy:'A wall grid separates adjacent emitters. Its upper edges follow the curved shell underside. Gray makes the walls visible here; the actual material should be opaque black. This visualization is not a released printable baffle part: joints, sealing and tolerances need the measured test hardware.',specs:[['Cell pitch','3 mm'],['Wall thickness study','0.36 mm'],['Illustrated top clearance','0.15 mm, to be tested'],['Cells','13 × 9']],color:'#88979e'},
 'sample-board':{title:'Reference LED matrix',copy:'The prototype is based on the Adafruit IS31FL3741 13 × 9 RGB matrix. Board outline and LED-center pitch follow the reference PCB; package heights and connector shapes are simplified. This is the first optical test, not the final globe electronics.',specs:[['Board outline','39 × 51.08 mm'],['LED array','117 emitters, 3 mm pitch'],['LED center span','36 × 24 mm'],['Power & I²C connections','See build-guide wiring']],color:'#4f9f86'},
};
const views={
 cutaway:['A look beneath the surface','A front section of the shell and LED carriers is hidden to expose the proposed frame and electronics. Rotate the globe or select a component.'],
 assembled:['The complete object','The shell closes around the proposed internal assembly. This exterior uses your chosen 25× terrain. The seams and polar openings are still a layout study.'],
 exploded:['How the layers fit together','Pull the outer shell sections and LED carriers away from the central frame. The extra spacing is for inspection; reset the slider to see their intended positions.'],
 frame:['The load-bearing structure','The spine, spokes, rings and ribs outline the support concept. The shell and lighting are hidden. Connections shown as overlapping members still require engineered joints.'],
 prototype:['The first thing to fabricate','A close-up at the real globe curvature: terrain shell, shaped optical cells and the reference LED matrix. Separate the layers to inspect them, or close them to examine the intended stack.'],
};
let mode='cutaway',spread=.6,assembly,prototype,renderer,scene,camera,controls,keyLight;
let renderRequested=false;
function requestRender(){if(!renderRequested){renderRequested=true;requestAnimationFrame(()=>{renderRequested=false;render();});}}
const visibility={shell:true,frame:true,lighting:true,electronics:true,base:true,'sample-shell':true,baffles:true,'sample-board':true};
function inspect(id){const p=parts[id];if(!p)return;$('part-title').textContent=p.title;$('part-copy').textContent=p.copy;$('part-specs').replaceChildren(...p.specs.map(([name,value])=>{const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=name;dd.textContent=value;row.append(dt,dd);return row;}));}
function layers(){const keys=mode==='prototype'?['sample-shell','baffles','sample-board']:mode==='frame'?['frame','electronics','base']:['shell','lighting','frame','electronics','base'];$('layers').replaceChildren(...keys.map(id=>{const label=document.createElement('label');label.className='layer';const input=document.createElement('input');input.type='checkbox';input.checked=visibility[id];input.dataset.layer=id;input.addEventListener('change',()=>{visibility[id]=input.checked;update();inspect(id);});const swatch=document.createElement('i');swatch.className='swatch';swatch.style.background=parts[id].color;label.append(input,swatch,document.createTextNode(parts[id].title));return label;}));}
function update(){
 const sample=mode==='prototype',exploded=mode==='exploded',cutaway=mode==='cutaway';
 assembly.root.visible=!sample;prototype.root.visible=sample;
 for(const [id,g] of Object.entries(assembly.groups))g.visible=visibility[id]&&!(mode==='frame'&&['shell','lighting'].includes(id));
 for(const panel of assembly.sections){panel.visible=!(cutaway&&panel.userData.lon>-30&&panel.userData.lon<90);panel.position.copy(panel.userData.explode).multiplyScalar(exploded?90*spread:0);}
 for(const {cover,sign} of assembly.polarCovers){cover.visible=!cutaway;cover.position.set(0,exploded?sign*70*spread:0,0);}
 for(const tile of assembly.tiles){tile.visible=!(cutaway&&tile.userData.lon>-30&&tile.userData.lon<90);tile.position.copy(tile.userData.direction).multiplyScalar(exploded?35*spread:0);}
 assembly.groups.base.position.y=exploded?-35*spread:0;
 prototype.shell.visible=visibility['sample-shell'];prototype.baffles.visible=visibility.baffles;prototype.boardGroup.visible=visibility['sample-board'];
 prototype.shell.position.z=sample?spread*30:0;prototype.baffles.position.z=sample?spread*13:0;
 $('spread-value').textContent=Math.round(spread*100)+'%';
 requestRender();
}
function resetCamera(){
 if(mode==='prototype'){camera.position.set(63,-79,78);controls.target.set(0,5,8);controls.minDistance=32;controls.maxDistance=320;}
 else if(mode==='assembled'){camera.position.set(-510,290,-340);controls.target.set(0,-27,0);controls.minDistance=230;controls.maxDistance=1600;}
 else {const s=mode==='exploded'?1.28:1;camera.position.set(405*s,225*s,560*s);controls.target.set(0,-27,0);controls.minDistance=230;controls.maxDistance=1600;}
 // Fit both tall and narrow canvases; the preferred view must not clip on phones.
 if(camera.aspect<1){camera.position.sub(controls.target).multiplyScalar(1/Math.max(.56,camera.aspect)).add(controls.target);}
 camera.lookAt(controls.target);controls.update();
}
function view(next){
 mode=next;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===mode)));
 $('view-title').textContent=views[mode][0];$('view-copy').textContent=views[mode][1];$('explode-control').hidden=!['exploded','prototype'].includes(mode);
 $('scale-title').textContent=mode==='prototype'?'39 × 27 mm curved optical test':'305 mm nominal diameter';
 $('scale-note').textContent=mode==='prototype'?'117 LEDs at 3 mm pitch · same 152.5 mm sphere radius':'25× terrain · 200 mm base · dimensions in millimetres';
 layers();update();inspect(mode==='prototype'?'sample-shell':mode==='frame'?'frame':'shell');resetCamera();
}
function render(){
 const forward=camera.position.clone().sub(controls.target).normalize(),right=new THREE.Vector3().crossVectors(camera.up,forward).normalize();
 keyLight.position.copy(controls.target).addScaledVector(forward,350).addScaledVector(right,-600).addScaledVector(camera.up,450);
 controls.update();renderer.render(scene,camera);
}
async function start(){
 renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;renderer.setClearColor(0x101619,0);$('scene').append(renderer.domElement);
 scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,.1,4000);
 controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=true;
 scene.add(new THREE.HemisphereLight(0xd9e3e3,0x344244,1.7));keyLight=new THREE.DirectionalLight(0xfff2dc,3.4);scene.add(keyLight);
 const rim=new THREE.DirectionalLight(0xa5c1d0,1.1);rim.position.set(-450,150,-400);scene.add(rim);
 const surface=makeSurface(),footprints=makeFootprints([{lat:49.2827,lon:-123.1207}],50,surface);
 const color=new THREE.CanvasTexture(paintHighlights(surface,footprints,.65));color.colorSpace=THREE.SRGBColorSpace;color.wrapS=THREE.RepeatWrapping;color.anisotropy=renderer.capabilities.getMaxAnisotropy();
 const glow=new THREE.CanvasTexture(footprints.canvas);glow.wrapS=THREE.RepeatWrapping;
 const material=new THREE.MeshStandardMaterial({map:color,roughness:.85,metalness:.1,emissive:0xff9d08,emissiveMap:glow,emissiveIntensity:.3,side:THREE.DoubleSide});
 assembly=buildAssembly(surface.land,material);prototype=buildPrototype(surface.land,material);scene.add(assembly.root,prototype.root);
 function resize(){const rect=$('scene').getBoundingClientRect();camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();renderer.setSize(rect.width,rect.height);requestRender();}
 controls.addEventListener('change',requestRender);
 new ResizeObserver(resize).observe($('scene'));resize();view('cutaway');
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
 $('spread').addEventListener('input',()=>{spread=Number($('spread').value)/100;update();});$('reset').addEventListener('click',resetCamera);
 const ray=new THREE.Raycaster();let down;
 renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
 renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hits=ray.intersectObject(mode==='prototype'?prototype.root:assembly.root,true).filter(hit=>{let o=hit.object;while(o){if(!o.visible)return false;o=o.parent;}return hit.object.isMesh;});if(hits[0])inspect(hits[0].object.userData.part);});
 $('save-image').addEventListener('click',()=>{render();renderer.domElement.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='globe-'+mode+'-concept.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);},'image/png');});
 requestRender();$('loading').hidden=true;
 window.globeStructure={snapshot:()=>({view:mode,spread,dimensions:assembly.dimensions,prototype:prototype.dimensions,sections:assembly.sections.length,tiles:assembly.tiles.length,visibleSections:assembly.sections.filter(p=>p.visible&&assembly.groups.shell.visible&&assembly.root.visible).length,visibleTiles:assembly.tiles.filter(p=>p.visible&&assembly.groups.lighting.visible&&assembly.root.visible).length,visibility:{...visibility},sampleShellOffset:prototype.shell.position.z,sampleBaffleOffset:prototype.baffles.position.z,prototypeInnerCenter:prototype.innerZ(0,0)}),ready:true};
}
// Let the loading message paint before generating terrain.
requestAnimationFrame(()=>setTimeout(()=>start().catch(error=>{console.error(error);$('loading').textContent='The 3D view could not start. Try a browser with WebGL enabled, or open the build guide for the static cross-section.';}),30));
