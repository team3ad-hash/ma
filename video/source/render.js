const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
  const [w,h]=process.argv[2].split('x').map(Number);const a=+process.argv[3],b=+process.argv[4];const out=process.argv[5];const FPS=60;
  fs.mkdirSync(out,{recursive:true});
  const br=await chromium.launch();const p=await br.newPage({viewport:{width:w,height:h}});
  p.on('pageerror',e=>console.error('ERR',e.message));
  await p.goto('file://'+__dirname+'/index.html');await p.evaluate(()=>window.ready);
  for(let f=a;f<b;f++){const fn=`${out}/f${String(f).padStart(5,'0')}.jpg`;if(fs.existsSync(fn))continue;
    await p.evaluate(t=>window.render(t),f/FPS);await p.screenshot({path:fn,type:'jpeg',quality:94});
    if(f%100===0)console.log(w,h,f);}
  await br.close();
})();
