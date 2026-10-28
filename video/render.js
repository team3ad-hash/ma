// Renders team3-demandgen.html frame-by-frame to MP4 (H.264 + AAC).
// Usage: node render.js <portrait|landscape|square> [fps] [--stills t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const fmt = process.argv[2] || 'portrait';
const fps = parseInt(process.argv[3] || '30', 10);
const stillsArg = process.argv.indexOf('--stills');
const outDir = path.join(__dirname, 'out');

(async () => {
  const browser = await chromium.launch();
  const sizes = { portrait: [1080, 1920], landscape: [1920, 1080], square: [1080, 1080] };
  const [W, H] = sizes[fmt];
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto('file://' + path.join(__dirname, `team3-demandgen.html?render&format=${fmt}`));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);

  if (stillsArg > 0) {
    for (const t of process.argv[stillsArg + 1].split(',').map(Number)) {
      await page.evaluate(t => window.render(t), t);
      await page.screenshot({ path: path.join(outDir, `still-${fmt}-${t}.png`) });
    }
    await browser.close();
    return;
  }

  const dur = await page.evaluate(() => window.DUR);
  const frames = Math.round(dur * fps);
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-i', path.join(outDir, 'soundtrack.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-c:a', 'aac', '-b:a', '192k', '-shortest',
    path.join(outDir, `team3-demandgen-${fmt}.mp4`)], { stdio: ['pipe', 'ignore', 'inherit'] });

  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log(`done: ${fmt} (${frames} frames)`);
})();
