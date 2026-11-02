const { chromium } = require('playwright');
const path = require('path');
(async()=>{
const [,, aspect='land', times='0', out='snap'] = process.argv;
const sizes = { land:[1920,1080], port:[1080,1920], sq:[1080,1080] };
const [W,H] = sizes[aspect];
const b = await chromium.launch({ args:['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport:{ width:W, height:H } });
p.on('console', m => console.log('console:', m.text()));
p.on('pageerror', e => console.log('PAGEERROR', e.message));
await p.goto('file://' + path.resolve('index.html') + '?a=' + aspect);
await p.evaluate(() => window.__ready);
for (const t of times.split(',')) {
  const t0 = Date.now();
  await p.evaluate(t => window.seek(t), +t);
  await p.screenshot({ path: `${out}_${aspect}_${t}.jpg`, type:'jpeg', quality:80 });
  console.log(t, Date.now()-t0, 'ms');
}
await b.close();
})();
