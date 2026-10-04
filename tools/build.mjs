import {build} from 'esbuild';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
const [license,elevationLicense]=await Promise.all([readFile('node_modules/three/LICENSE','utf8'),readFile('docs/elevation-data-license.md','utf8')]);
await mkdir('dist',{recursive:true});
for(const page of [
 {app:'app.js',template:'index.html',style:'style.css',outputs:['globe.html','index.html']},
 {app:'structure-app.js',template:'structure.html',style:'structure.css',outputs:['structure.html']},
 {app:'engineering-app.js',template:'engineering.html',style:'engineering.css',outputs:['engineering.html']},
]){
 const result=await build({entryPoints:['preview/'+page.app],bundle:true,minify:true,format:'iife',write:false,loader:{'.geojson':'json'},legalComments:'inline',target:['es2020']});
 const [template,css]=await Promise.all([readFile('preview/'+page.template,'utf8'),readFile('preview/'+page.style,'utf8')]);
 const script=result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script');
 // Insert literally: minified JS may contain replacement tokens such as $&.
 const html=template.replace('<!-- APP_STYLE -->',()=>`<!-- Three.js license:\n${license}\nElevation data distribution license:\n${elevationLicense}\n--><style>${css}</style>`).replace('<!-- APP_SCRIPT -->',()=>`<script>${script}</script>`);
 for(const output of page.outputs)await writeFile('dist/'+output,html);
 console.log(`Built self-contained ${page.outputs.join(', ')} (${Math.round(Buffer.byteLength(html)/1024)} KiB).`);
}
