// Usage: node render.cjs <land|port|sq> [fps=60] [start=0] [end=DUR]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
(async () => {
  const [,, aspect = 'land', fpsArg = '60', sArg, eArg] = process.argv;
  const fps = +fpsArg;
  const [W, H] = { land: [1920, 1080], port: [1080, 1920], sq: [1080, 1080] }[aspect];
  const b = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-gpu-vsync'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  p.on('pageerror', e => console.log('PAGEERROR', e.message));
  await p.goto('file://' + path.resolve('index.html') + '?a=' + aspect);
  await p.evaluate(() => window.__ready);
  const DUR = await p.evaluate(() => window.DUR);
  if (aspect === 'land') {
    const data = await p.evaluate(() => { const sp = []; for (let i = 0; i <= window.DUR * 100; i++) sp.push(window.camSpeed(i / 100)); return { sfx: window.SFX, speed: sp }; });
    fs.writeFileSync('audio/events.json', JSON.stringify(data));
  }
  const start = sArg ? +sArg : 0, end = eArg ? +eArg : DUR;
  fs.mkdirSync('out', { recursive: true });
  const outFile = `out/raw_${aspect}.mp4`;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-vf', `tmix=frames=2:weights='1 1',fps=30,noise=alls=6:allf=t+u,format=yuv420p`,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-r', '30', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round((end - start) * fps);
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const t = start + i / fps;
    await p.evaluate(t => window.seek(t), t);
    const buf = await p.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 120 === 0) console.log(aspect, i, '/', N, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
  console.log('done', outFile, ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
