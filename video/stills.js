// Quick review stills: node stills.js <w> <h> t1 t2 ...
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [W, H, ...ts] = process.argv.slice(2).map(Number);
const ROOT = __dirname;
const server = http.createServer((req, res) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); } fs.createReadStream(f).pipe(res); });
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: W, height: H } });
  pg.on('pageerror', e => console.error('pageerror', e)); pg.on('console', m => console.log('console', m.text()));
  await pg.goto(`http://127.0.0.1:${server.address().port}/index.html?w=${W}&h=${H}`);
  await pg.evaluate(() => window.ready);
  fs.mkdirSync('build/stills', { recursive: true });
  for (const t of ts) { await pg.evaluate(t => window.seek(t), t); await pg.screenshot({ path: `build/stills/${W}x${H}_${t}.jpg`, type: 'jpeg', quality: 80 }); }
  await b.close(); server.close();
})();
