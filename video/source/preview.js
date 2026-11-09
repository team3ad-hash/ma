const {chromium}=require('playwright');
(async()=>{
  const [w,h]=(process.argv[2]||'1920x1080').split('x').map(Number);
  const times=(process.argv[3]||'1').split(',').map(Number);
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:w,height:h}});
  const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
  await p.goto('file://'+__dirname+'/index.html');await p.evaluate(()=>window.ready);
  for(const t of times){const t0=Date.now();await p.evaluate(t=>window.render(t),t);await p.screenshot({path:`prev/p_${w}x${h}_${String(t).padStart(5,'0')}.jpg`,quality:80});console.log(t,Date.now()-t0,'ms');}
  console.log(errs.join('\n'));await b.close();
})();
