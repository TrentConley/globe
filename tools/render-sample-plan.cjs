// Render the sample instructions after prepare-sample-order.py; rerun that script
// afterward to embed the new PDF in both supplier request packs.
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const {spawn}=require('node:child_process');
(async()=>{
 const server=spawn('python3',['-m','http.server','4174','--bind','127.0.0.1','--directory','dist'],{stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<30;i++){
   try{if((await fetch('http://127.0.0.1:4174/sample-plan.html')).ok)break;}catch{}
   await new Promise(r=>setTimeout(r,100));
  }
  browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const page=await browser.newPage({viewport:{width:1280,height:960}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const name of ['sample-plan','sample-qualification']){
   await page.goto(`http://127.0.0.1:4174/${name}.html`,{waitUntil:'networkidle'});
   assert(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)));
   const targets=await page.locator('a[href],img[src]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')||n.getAttribute('src')));
   for(const t of targets)if(!/^(https?:|#)/.test(t))assert(fs.existsSync(path.join('dist',t)),t);
   await page.setViewportSize({width:390,height:844});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),name+' phone overflow');
   await page.setViewportSize({width:1280,height:960});
  }
  await page.goto('http://127.0.0.1:4174/sample-plan.html',{waitUntil:'networkidle'});
  // Include the full material/component review in the downloadable PDF.
  await page.evaluate(async()=>{
   const response=await fetch('sample-qualification.html');
   if(!response.ok)throw Error('Missing qualification document');
   const document2=new DOMParser().parseFromString(await response.text(),'text/html');
   const section=document.createElement('section');section.style.breakBefore='page';
   section.innerHTML=document2.querySelector('main').innerHTML;
   document.querySelector('main').appendChild(section);
  });
  await page.pdf({path:'dist/sample-test-plan.pdf',format:'A4',printBackground:true,displayHeaderFooter:true,
   headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:8px;width:100%;text-align:center;color:#666">Travel Globe · Sample A1 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
   margin:{top:'15mm',bottom:'18mm',left:'15mm',right:'15mm'}});
  assert.equal(errors.length,0);
  console.log('Combined sample/review PDF generated; both pages pass image, link and phone layout checks');
 }finally{if(browser)await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
