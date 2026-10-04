const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  const page=await b.newPage();
  await page.goto('http://127.0.0.1:4173/build-guide.html');
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete && i.naturalWidth));
  // Make relative file links usable from a downloaded PDF, rather than pointing to the test server.
  await page.evaluate(()=>{
   for(const a of document.querySelectorAll('a[href]')){
    const raw=a.getAttribute('href');if(raw.startsWith('#')||/^https?:/.test(raw))continue;
    a.href=new URL(raw,'https://trentconley.github.io/globe/').href;
   }
  });
  await page.pdf({path:'dist/build-guide.pdf',format:'A4',printBackground:false,margin:{top:'16mm',right:'16mm',bottom:'18mm',left:'16mm'},displayHeaderFooter:true,headerTemplate:'<div></div>',footerTemplate:'<div style="font-size:9px;width:100%;text-align:center;color:#666">Travel Globe · 25× / 50 mi · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
  console.log('Exported print-friendly PDF with public download links.');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
