const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const path=require('node:path');
const {URL}=require('node:url');

(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const errors=[];let checks=0;
 const check=(ok,msg)=>{assert.ok(ok,msg);checks++;console.log('PASS '+msg);};
 try{
  const page=await b.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(e.message));
  const r=await page.goto('http://127.0.0.1:4173/build-guide.html');check(r.status()===200,'build guide loads');
  check(await page.locator('h2').count()===13,'all thirteen design sections render');
  check(await page.locator('.toc a').count()===13,'section navigation is complete');
  check(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.complete && i.naturalWidth>0)),'technical diagram loads');
  const links=await page.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
  for(const link of new Set(links)){
   if(link.startsWith('#')){check(await page.locator('[id="'+link.slice(1)+'"]').count()===1,'navigation target '+link.slice(1));continue;}
   if(/^https?:/.test(link))continue;
   const target=new URL(link,'http://127.0.0.1:4173/build-guide.html');
   const response=await page.request.get(target.href);
   check(response.status()===200,'local download/page '+link);
  }
  await page.screenshot({path:'artifacts/build-guide-desktop.png'});
  const phone=await b.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await phone.goto('http://127.0.0.1:4173/build-guide.html');
  check(await phone.evaluate(()=>document.body.scrollWidth===innerWidth),'guide fits a phone without page overflow');
  check(await phone.locator('.table-scroll').evaluateAll(nodes=>nodes.every(n=>n.clientWidth<=390)),'wide engineering tables scroll within phone layout');
  await phone.screenshot({path:'artifacts/build-guide-mobile.png'});
  check(errors.length===0,'no guide runtime errors');
  console.log('Completed '+checks+' guide checks.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
