/* Team3 · armed security recruitment — continuous-camera blueprint film
   Deterministic: window.seek(t) renders the exact frame for time t. */
(() => {
const qs = new URLSearchParams(location.search);
const A = qs.get('a') || 'land';
document.documentElement.classList.add(A);
const [W, H] = { land: [1920, 1080], port: [1080, 1920], sq: [1080, 1080] }[A];
const DUR = 30;
const $ = s => document.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent && parent.appendChild(e); return e; };
const rng = seed => { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (T, a, b) => clamp((T - a) / (b - a), 0, 1);
const ease = n => gsap.parseEase(n);
const eOut3 = ease('power3.out'), eInOut2 = ease('power2.inOut'), eExpo = ease('expo.out'), eBack = ease('back.out(1.6)');

const SFX = []; window.SFX = SFX;
const frameFns = [];
const tl = gsap.timeline({ paused: true });
const vp = $('#vp');
vp.style.setProperty('--W', W + 'px'); vp.style.setProperty('--H', H + 'px');

/* ---------------------------------------------------------- procedural art */
// sheet zones
(() => {
  const Z = $('#zones'); Z.innerHTML = '<div class="zb"></div>';
  for (let i = 0; i < 8; i++) {
    const c = 120 + 1020 * i + 510;
    for (const side of ['t', 'b']) { const d = document.createElement('div'); d.className = 'zl'; d.textContent = 8 - i; d.style.left = (c - 60) + 'px'; d.style.top = side === 't' ? '0px' : (8400 - 120) + 'px'; Z.appendChild(d); }
    for (const side of ['l', 'r']) { const d = document.createElement('div'); d.className = 'zl'; d.textContent = 'ABCDEFGH'[i]; d.style.top = (c - 60) + 'px'; d.style.left = side === 'l' ? '0px' : (8400 - 120) + 'px'; Z.appendChild(d); }
  }
})();
// scribbles
(() => {
  const S = $('#scribbles'), R = rng(7);
  const words = ['SEC A-A', 'DET. 04', 'Ø 40', 'R 120', '±0.05', 'TYP.', '1:50', 'REV. C', 'EL. +142.00', 'CL', 'GRID 7', 'SHT 01', 'N 32°30′', 'E 35°05′', 'DWG 123088', 'SCALE 1:2500'];
  for (let i = 0; i < 150; i++) {
    const x = 260 + R() * 7880, y = 260 + R() * 7880, k = Math.floor(R() * 6);
    if (k === 0) { const r = 20 + R() * 70; el('circle', { cx: x, cy: y, r }, S); el('path', { d: `M${x - r * 1.4} ${y} H${x + r * 1.4} M${x} ${y - r * 1.4} V${y + r * 1.4}` }, S); }
    else if (k === 1) { const L = 200 + R() * 500; el('path', { d: `M${x} ${y} H${x + L} M${x} ${y - 14} V${y + 14} M${x + L} ${y - 14} V${y + 14}` }, S); el('text', { x: x + L / 2 - 30, y: y - 14 }, S).textContent = Math.round(L * 2.5); }
    else if (k === 2) { el('text', { x, y }, S).textContent = words[Math.floor(R() * words.length)]; }
    else if (k === 3) { const w = 80 + R() * 200, h = 60 + R() * 160; el('rect', { x, y, width: w, height: h }, S); el('path', { d: `M${x} ${y} L${x + w} ${y + h}` }, S); }
    else if (k === 4) { const a = R() * Math.PI * 2, L = 120 + R() * 200; el('path', { d: `M${x} ${y} L${x + Math.cos(a) * L} ${y + Math.sin(a) * L}` }, S); el('circle', { cx: x, cy: y, r: 6 }, S); }
    else { el('path', { d: `M${x - 30} ${y} H${x + 30} M${x} ${y - 30} V${y + 30}` }, S); }
  }
})();
// rifle grade ruler
const gx = i => 80 + i * 114;
(() => {
  const g = $('#gticks');
  for (let i = 0; i < 8; i++) {
    el('path', { class: 'draw', d: `M${gx(i)} 130 V158` }, g);
    el('text', { class: 'mono t-dim fade', x: gx(i), y: 196, 'text-anchor': 'middle' }, g).textContent = '0' + (i + 1);
    if (i < 7) for (let k = 1; k < 4; k++) el('path', { class: 'draw f', d: `M${gx(i) + k * 28.5} 130 V142` }, g);
  }
  $('#gbar').setAttribute('d', `M${gx(2)} 104 H960`);
  $('#g03').setAttribute('x', gx(2) + 70);
})();
// transformer yard
(() => { const g = $('.tyard'); for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) el('rect', { class: 'draw', x: 600 + c * 44, y: 420 + r * 40, width: 30, height: 26 }, g); })();
// gauge
const GC = { x: 450, y: 460 };
const gp = (v, r) => { const th = Math.PI - v / 100 * Math.PI; return [GC.x + r * Math.cos(th), GC.y - r * Math.sin(th)]; };
const garc = (v0, v1, r) => { const a = gp(v0, r), b = gp(v1, r); return `M${a[0]} ${a[1]} A${r} ${r} 0 0 1 ${b[0]} ${b[1]}`; };
(() => {
  const g = $('#gaugeTicks');
  for (let v = 0; v <= 100.01; v += 2.5) {
    const major = Math.abs(v % 10) < .01, a = gp(v, 380), b = gp(v, major ? 340 : 362);
    el('path', { class: 'draw' + (major ? '' : ' f2'), d: `M${a[0]} ${a[1]} L${b[0]} ${b[1]}` }, g);
    if (major) { const p = gp(v, 300); el('text', { class: 'mono t-dim fade', x: p[0], y: p[1] + 9, 'text-anchor': 'middle' }, g).textContent = v; }
  }
  // highlight ticks for range 68-75
  for (const v of [68, 75]) { const a = gp(v, 392), b = gp(v, 326); el('path', { class: 'draw amberS thick', d: `M${a[0]} ${a[1]} L${b[0]} ${b[1]}` }, g); const p = gp(v, 425); el('text', { class: 'mono t-co fade amberT', x: p[0], y: p[1] + 8, 'text-anchor': 'middle' }, g).textContent = v; }
})();
// dial
const dang = h => (h / 24) * Math.PI * 2 - Math.PI / 2;
const dp = (h, r) => [r * Math.cos(dang(h)), r * Math.sin(dang(h))];
const darc = (h0, h1, r) => { const a = dp(h0, r), b = dp(h1, r); const large = (h1 - h0) > 12 ? 1 : 0; return `M${a[0]} ${a[1]} A${r} ${r} 0 ${large} 1 ${b[0]} ${b[1]}`; };
(() => {
  const g = $('#dialTicks');
  for (let h = 0; h < 24; h++) { const major = h % 6 === 0, a = dp(h, 330), b = dp(h, major ? 286 : 306); el('path', { class: 'draw' + (major ? '' : ' f2'), d: `M${a[0]} ${a[1]} L${b[0]} ${b[1]}` }, g); }
  for (const h of [0, 6, 12, 18]) { const p = dp(h, 252); el('text', { class: 'mono t-dim fade', x: p[0], y: p[1] + 9, 'text-anchor': 'middle' }, g).textContent = String(h).padStart(2, '0'); }
  const lab = (id, h) => { const p = dp(h, 392); const t = $(id); t.setAttribute('x', p[0]); t.setAttribute('y', p[1] + 14); };
  lab('#lM', 10); lab('#lE', 18); lab('#lN', 26);
})();
// bonus cells
(() => {
  const s = $('#badge'); s.setAttribute('viewBox', '0 0 900 700');
  $$('#badge text.t-lbl').forEach(t => t.setAttribute('y', 690));
  const g = $('#cells'); const w = 74, gap = (820 - 740) / 9;
  for (let i = 0; i < 10; i++) el('rect', { x: 40 + i * (w + gap), y: 600, width: w, height: 44 }, g);
})();
// wrap site callouts into inner group for scaling
$$('.sco').forEach(g => { const inner = el('g', { class: 'scoi' }); while (g.firstChild) inner.appendChild(g.firstChild); g.appendChild(inner); });

/* ---------------------------------------------------------- stations */
const ST = {};
$$('.st').forEach(s => {
  const id = s.id.replace('s-', '');
  const x = +s.dataset.x, y = +s.dataset.y, rot = +s.dataset.rot;
  s.style.left = x + 'px'; s.style.top = y + 'px';
  s.style.transform = `rotate(${rot}deg) translate(-50%,-50%)`;
  ST[id] = { el: s, x, y, rot };
});

/* ---------------------------------------------------------- initial states */
const isDashed = e => e.classList.contains('cl') || e.classList.contains('dashR') || e.hasAttribute('stroke-dasharray');
$$('.draw').forEach(e => {
  if (isDashed(e)) { e.style.opacity = 0; return; }
  e.setAttribute('pathLength', '1'); e.style.strokeDasharray = '1 1'; e.style.strokeDashoffset = '1'; e.style.opacity = 0;
});
gsap.set('.fade', { opacity: 0 });
gsap.set('.wi, .rti', { yPercent: 118 });
gsap.set('.kicker .kl', { scaleX: 0 });
gsap.set('.reqs .num', { opacity: 0 });
gsap.set('.co text', { opacity: 0 });
gsap.set('.duties li', { opacity: 0, x: -60 });
gsap.set('.scoi', { scale: 0, svgOrigin: '0 0' });
gsap.set('.pin', { scaleX: 0, transformOrigin: '100% 50%' });
gsap.set('.chip', { scale: 0, opacity: 0 });
gsap.set('#m1, #m2, #mdash, .upto, #bn, .bnum .cur', { opacity: 0 });
gsap.set('#jpin', { opacity: 0 });
gsap.set('.tbc', { clipPath: 'inset(0% 0% 0% 100%)' });
gsap.set('.ctaD .logo', { opacity: 0 });
gsap.set('.stamp', { opacity: 0, rotation: -12 });
gsap.set('.kline span', { yPercent: 115 });
gsap.set('#hud', { opacity: 0 });
gsap.set('#car, .truck, #radar', { opacity: 0 });
$$('.st').forEach(s => { s.style.clipPath = 'inset(50% 50% 50% 50%)'; });
$('#s-hook').style.clipPath = 'inset(0% 0% 0% 0%)';
const kinbg = document.createElement('div');
kinbg.style.cssText = 'position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 50%, rgba(2,6,14,.82), rgba(2,6,14,.35) 70%, transparent);opacity:0';
$('#kin').prepend(kinbg);
$('#kin').style.position = 'absolute';
$$('.kline').forEach(k => { k.style.position = 'relative'; });

/* ---------------------------------------------------------- helpers */
const D = sel => typeof sel === 'string' ? $$(sel) : (sel instanceof Element ? [sel] : [...sel]);
function drawIn(sel, t, dur = .8, stagger = .03, ez = 'power2.inOut') {
  const els = D(sel).filter(e => e.classList.contains('draw'));
  const solid = els.filter(e => !isDashed(e)), dashed = els.filter(isDashed);
  if (solid.length) { tl.set(solid, { opacity: 1 }, t); tl.to(solid, { strokeDashoffset: 0, duration: dur, stagger, ease: ez }, t); }
  if (dashed.length) tl.to(dashed, { opacity: 1, duration: dur * .8, stagger, ease: 'none' }, t);
  SFX.push({ t, type: 'draw', dur: dur + stagger * Math.max(0, els.length - 1) });
}
function fadeIn(sel, t, dur = .5, stagger = .03, to = 1) { tl.to(D(sel), { opacity: to, duration: dur, stagger, ease: 'power1.out' }, t); }
function rise(sel, t, stagger = .08, dur = .75) {
  const els = D(sel);
  tl.fromTo(els, { yPercent: 118, rotation: 5 }, { yPercent: 0, rotation: 0, duration: dur, ease: 'expo.out', stagger }, t);
  els.forEach((_, i) => SFX.push({ t: t + i * stagger, type: 'rise' }));
}
function slam(sel, t, from = 1.7) {
  tl.fromTo(D(sel), { opacity: 0, scale: from, filter: 'blur(16px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: .5, ease: 'expo.out' }, t);
  SFX.push({ t, type: 'slam' });
}
function typeOn(elm, t, dur) {
  const chars = [...elm.dataset.text]; elm.textContent = '';
  frameFns.push(T => {
    const n = Math.round(prog(T, t, t + dur) * chars.length);
    elm.textContent = chars.slice(0, n).join('');
    elm.style.setProperty('--caret', (T >= t - .1 && T < t + dur + .7) ? (Math.floor(T * 5) % 2 ? 1 : .15) : 0);
  });
  chars.forEach((c, i) => c !== ' ' && SFX.push({ t: t + (i + .5) / chars.length * dur, type: 'tick' }));
}
function kicker(st, t, dur = .55) {
  const k = $(`#s-${st} .kicker`);
  tl.to(k.querySelector('.kl'), { scaleX: 1, duration: .5, ease: 'expo.out' }, t);
  typeOn(k.querySelector('.type'), t + .12, dur);
}
function plate(st, t) {
  tl.fromTo(ST[st].el, { clipPath: 'inset(50% 50% 50% 50%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: .6, ease: 'expo.out' }, t);
  SFX.push({ t, type: 'plate' });
}
function row(li, t, tc) {
  drawIn(li.querySelector('rect'), t, .35, 0);
  const n = li.querySelector('.num'); if (n) tl.to(n, { opacity: .8, duration: .3 }, t);
  rise(li.querySelector('.rti'), t + .05, 0, .65);
  tl.to(li, { '--ul': 1, duration: .7, ease: 'power2.out' }, t + .1);
  drawIn(li.querySelector('.ck'), tc, .22, 0, 'power3.out');
  SFX.push({ t: tc, type: 'check' });
}
function scramble(elm, t0, t1, final) {
  frameFns.push(T => {
    if (T < t0) { elm.textContent = final.replace(/\d/g, '0'); return; }
    if (T >= t1) { elm.textContent = final; return; }
    const f = Math.floor(T * 30);
    elm.textContent = final.replace(/\d/g, (d, i) => Math.floor(hash(f * 7.3 + i * 13.1) * 10));
  });
  for (let x = t0; x < t1; x += 1 / 15) SFX.push({ t: x, type: 'tick', soft: 1 });
}
const flashes = [], shakes = [];
function flash(t, a = .18) { flashes.push({ t, a }); }

/* ======================================================== 01 HOOK */
$$('#s-hook .hook-cross .draw').forEach(e => { e.style.strokeDashoffset = .5; });
drawIn('#s-hook .hook-cross .draw', 0.0, .9, .05, 'power2.out');
tl.to('#s-hook .hook-cross', { opacity: .35, duration: 1.2 }, 1.2);
kicker('hook', 0.0, .6);
rise($$('#s-hook h1')[0].querySelectorAll('.wi')[0], 0.12);
rise($$('#s-hook h1')[0].querySelectorAll('.wi')[1], 0.78);
drawIn('#s-hook .dim .draw', 0.62, .6);
rise($$('#s-hook h1')[1].querySelectorAll('.wi')[0], 1.10);
rise($$('#s-hook h1')[1].querySelectorAll('.wi')[1], 1.50);
flash(1.5, .12);
tl.to('#hud', { opacity: 1, duration: .8 }, 0.15);

/* ======================================================== 02 RIFLE */
plate('rifle', 2.0);
kicker('rifle', 2.15, .7);
rise('#s-rifle h2 .wi', 2.22, .07);
drawIn('#rifle .rf .draw', 2.05, 1.05, .022);
drawIn('#rifle > .cl', 2.05, .6);
drawIn('#rifle > .dimc', 2.55, .6);
fadeIn('#rifle .t-dim', 2.95);
const rq = $$('#s-rifle .reqs li');
row(rq[0], 2.35, 2.62);
row(rq[1], 2.5, 3.55);
row(rq[2], 3.9, 4.5);
row(rq[3], 4.25, 4.72);
[['#co1', 2.5], ['#co2', 3.0], ['#co3', 3.95], ['#co4', 4.3]].forEach(([s, t]) => { drawIn(`${s} .draw`, t, .45, .05, 'power3.out'); tl.to(`${s} text`, { opacity: 1, duration: .3 }, t + .25); });
drawIn('#grade > .draw:not(#gbar), #gticks .draw', 2.35, .7, .012);
fadeIn('#grade .fade:not(#g03)', 2.6, .4, .02);
// pointer
frameFns.push(T => {
  const p = eOut3(prog(T, 2.62, 3.1));
  const x = lerp(gx(0), gx(2), p) + (T > 3.1 ? Math.sin((T - 3.1) * 18) * 6 * Math.exp(-(T - 3.1) * 5) : 0);
  const g = $('#gptr'); g.setAttribute('transform', `translate(${x} 128)`); g.style.opacity = prog(T, 2.5, 2.7);
});
tl.fromTo('#g03', { opacity: 0, scale: 1.6, svgOrigin: `${gx(2) + 70} 70` }, { opacity: 1, scale: 1, duration: .45, ease: 'expo.out' }, 3.05);
SFX.push({ t: 3.05, type: 'slam', soft: 1 });
drawIn('#gbar', 3.26, .5, 0, 'power2.out');
drawIn('#grade > .amberS:not(#gbar)', 3.68, .2, 0);

/* ======================================================== 03 PROFESSIONALISM */
plate('prof', 4.95);
kicker('prof', 5.05, .6);
rise($$('#prof1 .wi')[0], 5.17);
rise($$('#prof1 .wi')[1], 5.78);
rise($$('#prof2 .wi')[0], 6.10);
rise($$('#prof2 .wi')[1], 6.24);
drawIn('#s-prof .dim .draw', 6.45, .55, .08, 'power3.out');
flash(6.24, .1);

/* ======================================================== 04 SITE */
plate('site', 7.05);
kicker('site', 7.15, .7);
const sw = $$('#s-site h2 .wi');
rise(sw[0], 7.4); rise(sw[1], 7.66); rise(sw[2], 8.02);
const sub = $$('#s-site .sub .wi');
rise(sub[0], 8.5); rise(sub[1], 9.58);
tl.fromTo('#s-site .sub .sep', { opacity: 0 }, { opacity: 1, duration: .3 }, 9.4);
tl.to('#s-site .pin', { scaleX: 1, duration: .55, ease: 'expo.out' }, 11.0);
SFX.push({ t: 11.0, type: 'pop' });
$$('#s-site .duties li').forEach((li, i) => { tl.to(li, { opacity: 1, x: 0, duration: .5, ease: 'expo.out' }, 9.85 + i * .26); SFX.push({ t: 9.85 + i * .26, type: 'tick' }); });
$$('.scoi').forEach((g, i) => tl.to(g, { scale: 1, duration: .5, ease: 'back.out(2)' }, 9.85 + i * .26));
drawIn('#site > rect.f', 7.15, .5, 0);
fadeIn('#site > .t-lbl', 7.4);
drawIn('#site > path.draw:not(#fence):not(#patrol)', 7.4, .9, .03);
drawIn('#fence', 7.45, 1.1, 0, 'power1.inOut');
fadeIn('#site .fenceX', 8.3, .6, 0, .9);
drawIn('#site > rect.draw:not(.f):not(#czone), #site > circle.draw, #site .tyard .draw', 7.9, .7, .025);
drawIn('#site g .draw', 8.3, .5, .02);
drawIn('#czone', 9.6, .6);
fadeIn('#site .t-he', 8.9, .5, .08);
drawIn('#patrol', 8.7, 1.1, 0, 'power1.inOut');
tl.fromTo('#czone', { strokeWidth: 3 }, { strokeWidth: 9, duration: .25, yoyo: true, repeat: 3, ease: 'sine.inOut' }, 10.22);
tl.to('#jpin', { opacity: 1, duration: .2 }, 10.95);
tl.fromTo('#jpin', { y: -60 }, { y: 0, duration: .5, ease: 'bounce.out' }, 10.95);
fadeIn('#jlbl', 11.15);
// procedural site motion
const patrol = $('#patrol'), car = $('#car'), PL = patrol.getTotalLength();
const truckPts = [[500, 900], [500, 640], [430, 640], [380, 600]];
const segLen = truckPts.slice(1).map((p, i) => Math.hypot(p[0] - truckPts[i][0], p[1] - truckPts[i][1]));
const TL = segLen.reduce((a, b) => a + b, 0);
function truckAt(d) { let i = 0; while (i < segLen.length - 1 && d > segLen[i]) { d -= segLen[i]; i++; } const a = truckPts[i], b = truckPts[i + 1], u = clamp(d / segLen[i], 0, 1); return { x: lerp(a[0], b[0], u), y: lerp(a[1], b[1], u), ang: Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI + 90 }; }
const trucks = [{ e: $('#truck1'), t0: 7.9, t1: 10.6 }, { e: $('#truck2'), t0: 9.9, t1: 12.6 }];
frameFns.push(T => {
  // car
  const cp = prog(T, 9.3, 13.0), d = (cp * 1.15 % 1) * PL;
  const p1 = patrol.getPointAtLength(d), p2 = patrol.getPointAtLength(Math.min(PL, d + 2));
  car.setAttribute('transform', `translate(${p1.x} ${p1.y}) rotate(${Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI + 180})`);
  car.style.opacity = prog(T, 9.2, 9.5);
  // trucks + barrier
  let open = 0;
  trucks.forEach(tr => {
    const u = eInOut2(prog(T, tr.t0, tr.t1)), q = truckAt(u * TL);
    tr.e.setAttribute('transform', `translate(${q.x} ${q.y}) rotate(${q.ang})`);
    tr.e.style.opacity = prog(T, tr.t0, tr.t0 + .25) * (q.y < 880 ? 1 : 0.0) + (q.y >= 880 ? prog(T, tr.t0, tr.t0 + .25) : 0);
    const dist = Math.hypot(q.x - 500, q.y - 704);
    open = Math.max(open, 1 - clamp((dist - 60) / 90, 0, 1));
  });
  $('#barrier').setAttribute('transform', `rotate(${-80 * eInOut2(open)} 478 704)`);
  $('#barrier').style.opacity = prog(T, 7.6, 7.9);
  // crane + radar
  $('#crane').setAttribute('transform', `translate(300 520) rotate(${-20 + Math.sin(T * .6) * 35})`);
  const r = $('#radar'); r.setAttribute('transform', `rotate(${(T - 9.9) * 140} 866 122)`); r.style.opacity = prog(T, 10.6, 10.9) * .9;
});

/* ======================================================== 05 SALARY */
plate('sal', 12.05);
kicker('sal', 12.12, .45);
drawIn('#gauge > .draw, #gaugeTicks .draw:not(.amberS)', 12.05, .8, .006);
fadeIn('#gauge .fade:not(.amberT)', 12.4, .4, .006);
drawIn('#gaugeTicks .amberS', 13.0, .3, .9);
fadeIn('#gaugeTicks .amberT', 13.1, .3, .9);
slam('#m1', 12.22, 1.5); scramble($('#m1'), 12.22, 12.95, '68');
slam('#mdash', 13.1, 2);
slam('#m2', 13.26, 1.5); scramble($('#m2'), 13.26, 13.95, '75');
drawIn('#s-sal .dim .draw', 14.0, .5);
rise('#s-sal .unit .wi', 14.06, .32);
const eBackN = ease('back.out(2.2)');
const needleV = T => {
  if (T < 12.3) return 0;
  if (T < 13.0) return 68 * eOut3(prog(T, 12.3, 13.0));
  if (T < 13.3) return 68;
  return lerp(68, 75, eBackN(prog(T, 13.3, 13.95))) + (T > 14 ? Math.sin(T * 2.3) * .4 : 0);
};
frameFns.push(T => {
  const v = needleV(T);
  $('#needle').setAttribute('transform', `translate(${GC.x} ${GC.y}) rotate(${v * 1.8})`);
  $('#needle').style.opacity = prog(T, 12.2, 12.4);
  const b = $('#band'); if (v > 68.2 && T > 13.0) { b.setAttribute('d', garc(68, Math.min(75, v), 240)); b.style.opacity = 1; } else b.style.opacity = 0;
});

/* ======================================================== 06 BONUS */
plate('bon', 15.05);
kicker('bon', 15.15, .6);
slam('.upto', 15.74, 1.8);
slam('#bn', 15.9, 1.4);
slam('.bnum .cur', 16.62, 2);
frameFns.push(T => {
  const v = Math.round(eOut3(prog(T, 15.9, 16.65)) * 10000 / 50) * 50;
  $('#bn').textContent = v.toLocaleString('en-US');
  const n = Math.round(eOut3(prog(T, 15.9, 16.65)) * 10);
  $$('#cells rect').forEach((r, i) => r.classList.toggle('on', i < n));
});
for (let i = 0; i < 10; i++) SFX.push({ t: 15.9 + eOut3inv(i / 10) * .75, type: 'tick' });
function eOut3inv(y) { return 1 - Math.cbrt(1 - y); }
const bw = $$('#s-bon .sub .wi');
[17.02, 17.5, 17.74, 18.22, 18.42].forEach((t, i) => rise(bw[i], t));
fadeIn('#s-bon .foot', 18.3);
drawIn('#badge > .draw:not(.amberS)', 15.15, 1.0, .1);
drawIn('#badge > .amberS', 16.1, .5, .1);
fadeIn('#badge .t-lbl', 15.6);
tl.fromTo('#bdgT', { opacity: 0, scale: 1.6, svgOrigin: '450 390' }, { opacity: 1, scale: 1, duration: .5, ease: 'expo.out' }, 17.74);
SFX.push({ t: 17.74, type: 'slam', soft: 1 });

/* ======================================================== 07 BENEFITS */
plate('ben', 18.65);
kicker('ben', 18.75, .6);
rise('#s-ben h2 .wi', 18.85, .1);
const bl = $$('#s-ben .reqs li');
row(bl[0], 19.0, 19.55);
row(bl[1], 19.98, 20.4);
row(bl[2], 20.62, 21.0);
row(bl[3], 21.34, 22.5);
row(bl[4], 22.0, 22.75);
drawIn('#dial > circle.draw, #dialTicks .draw', 18.85, .8, .01);
fadeIn('#dialTicks .fade', 19.2, .3, .05);
const arcs = [['#arcM', 6, 14, 19.45, '#lM'], ['#arcE', 14, 22, 19.75, '#lE'], ['#arcN', 22, 30, 20.05, '#lN']];
arcs.forEach(a => { fadeIn(a[4], a[3] + .25, .4); SFX.push({ t: a[3], type: 'draw', dur: .5 }); });
frameFns.push(T => {
  arcs.forEach(([id, h0, h1, t]) => { const p = eOut3(prog(T, t, t + .55)); const e = $(id); if (p <= 0) { e.setAttribute('d', ''); return; } e.setAttribute('d', darc(h0, lerp(h0, h1, p) - .0001 + (p >= 1 ? 0 : 0), 200)); });
  const hd = $('#hand'); hd.setAttribute('transform', `rotate(${(T - 19) * 90})`); hd.style.opacity = prog(T, 19.3, 19.6);
});
tl.fromTo('#t247', { opacity: 0, scale: 1.8, svgOrigin: '0 0' }, { opacity: 1, scale: 1, duration: .5, ease: 'expo.out' }, 19.95);
SFX.push({ t: 19.95, type: 'slam', soft: 1 });
tl.to('#ch1', { scale: 1, opacity: 1, duration: .5, ease: 'back.out(2)' }, 21.0);
tl.to('#ch2', { scale: 1, opacity: 1, duration: .5, ease: 'back.out(2)' }, 21.35);
SFX.push({ t: 21.0, type: 'pop' }, { t: 21.35, type: 'pop' });

/* ======================================================== 08 PULLBACK + CTA */
tl.to(kinbg, { opacity: 1, duration: .5 }, 23.25);
[['#k1', 23.42], ['#k2', 23.82], ['#k3', 24.3]].forEach(([s, t]) => { tl.to(`${s} span`, { yPercent: 0, duration: .55, ease: 'expo.out' }, t); SFX.push({ t, type: 'slam' }); });
tl.to('#kin .kline', { scale: 1.5, opacity: 0, filter: 'blur(10px)', duration: .4, ease: 'power2.in', stagger: .04 }, 24.62);
tl.to(kinbg, { opacity: 0, duration: .4 }, 24.7);
plate('cta', 24.55);
$$('.tbc').forEach((c, i) => tl.to(c, { clipPath: 'inset(0% 0% 0% 0%)', duration: .55, ease: 'expo.out' }, 24.8 + i * .07));
tl.fromTo('.ctaD .logo', { opacity: 0, scale: 1.8, filter: 'blur(18px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: .55, ease: 'expo.out' }, 24.86);
SFX.push({ t: 24.86, type: 'slam' });
tl.fromTo('.stamp', { opacity: 0, scale: 3.2 }, { opacity: 1, scale: 1, duration: .28, ease: 'power4.in' }, 25.5);
SFX.push({ t: 25.78, type: 'stamp' });
flash(25.78, .3); shakes.push({ t: 25.78, a: 22 });
frameFns.push(T => {
  const btn = $('.btn');
  const ph = T > 26 ? ((T - 26) % 1.2) / 1.2 : -1;
  btn.style.boxShadow = ph >= 0 ? `0 0 0 ${ph * 34}px rgba(255,182,39,${.55 * (1 - ph)})` : 'none';
  btn.querySelector('svg').style.transform = `translateX(${T > 26 ? -Math.max(0, Math.sin((T - 26) * Math.PI / .6)) * 14 : 0}px)`;
});

/* ---------------------------------------------------------- route line */
const ORDER = ['hook', 'rifle', 'prof', 'site', 'sal', 'bon', 'ben', 'cta'];
const routeTimes = [[1.85, 2.45], [4.75, 5.4], [6.85, 7.5], [11.9, 12.5], [14.95, 15.5], [18.55, 19.1], [22.95, 25.4]];
(() => {
  const pts = ORDER.map(k => [ST[k].x, ST[k].y]);
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    d += ` C${p1[0] + (p2[0] - p0[0]) / 6} ${p1[1] + (p2[1] - p0[1]) / 6} ${p2[0] - (p3[0] - p1[0]) / 6} ${p2[1] - (p3[1] - p1[1]) / 6} ${p2[0]} ${p2[1]}`;
  }
  const R = $('#route');
  el('path', { d, stroke: 'rgba(255,182,39,.12)', 'stroke-width': 40, id: 'routeGlow', pathLength: 1 }, R);
  el('path', { d, stroke: 'rgba(255,182,39,.75)', 'stroke-width': 7, id: 'routeLine', pathLength: 1, 'stroke-linecap': 'round' }, R);
  pts.forEach((p, i) => { el('circle', { cx: p[0], cy: p[1], r: 26, fill: '#ffb627', class: 'rnode' }, R); });
  frameFns.push(T => {
    let pr = 0;
    routeTimes.forEach(([a, b], i) => { if (T >= b) pr = (i + 1) / 7; else if (T > a) pr = (i + eInOut2(prog(T, a, b))) / 7; });
    ['#routeGlow', '#routeLine'].forEach(s => { const e = $(s); e.style.strokeDasharray = '1 1'; e.style.strokeDashoffset = 1 - pr; });
  });
})();

/* ---------------------------------------------------------- camera */
const keys = [
  { t: 0.00, st: 'hook', z: 2.3, tilt: 0, dx: 230, dy: -120 },
  { t: 1.25, st: 'hook', z: 1.0, tilt: 4 },
  { t: 1.85, st: 'hook', z: 1.035, tilt: 5, dx: -60 },
  { t: 2.13, mid: ['hook', 'rifle'], z: .58, tilt: 20, rollAdd: -4 },
  { t: 2.45, st: 'rifle', z: .97, tilt: 6, dx: 50 },
  { t: 4.75, st: 'rifle', z: 1.035, tilt: 3, dx: -40, dy: 30 },
  { t: 5.07, mid: ['rifle', 'prof'], z: .56, tilt: 20 },
  { t: 5.40, st: 'prof', z: 1.0, tilt: 5 },
  { t: 6.85, st: 'prof', z: 1.04, tilt: 3, dy: 20 },
  { t: 7.17, mid: ['prof', 'site'], z: .56, tilt: 20 },
  { t: 7.50, st: 'site', z: .96, tilt: 6 },
  { t: 9.60, st: 'site', z: 1.02, tilt: 8, dx: -30 },
  { t: 11.90, st: 'site', z: 1.035, tilt: 4, dx: 40, dy: 20 },
  { t: 12.20, mid: ['site', 'sal'], z: .56, tilt: 20, rollAdd: 3 },
  { t: 12.50, st: 'sal', z: .98, tilt: 5 },
  { t: 14.95, st: 'sal', z: 1.035, tilt: 3, dx: -30 },
  { t: 15.22, mid: ['sal', 'bon'], z: .58, tilt: 18 },
  { t: 15.50, st: 'bon', z: .98, tilt: 5 },
  { t: 18.55, st: 'bon', z: 1.035, tilt: 3 },
  { t: 18.82, mid: ['bon', 'ben'], z: .56, tilt: 20, rollAdd: -3 },
  { t: 19.10, st: 'ben', z: .98, tilt: 5 },
  { t: 22.95, st: 'ben', z: 1.035, tilt: 3 },
  { t: 23.85, sheet: 1, z: 1.0, tilt: 14 },
  { t: 24.50, sheet: 1, z: 1.12, tilt: 11 },
  { t: 25.40, st: 'cta', z: .97, tilt: 3 },
  { t: 30.00, st: 'cta', z: 1.035, tilt: 1, dx: -20 },
];
function monotone(xs, ys) {
  const n = xs.length, d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d[i] = (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]);
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) { const tau = 3 / Math.sqrt(s); m[i] = tau * a * d[i]; m[i + 1] = tau * b * d[i]; }
  }
  return x => {
    if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    const h = xs[i + 1] - xs[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
  };
}
let CAM = null;
function buildCamera() {
  const PADW = { land: 220, port: 110, sq: 120 }[A], PADH = { land: 190, port: 330, sq: 200 }[A];
  const box = id => { const s = ST[id]; return { x: s.x, y: s.y, w: s.el.offsetWidth + PADW, h: s.el.offsetHeight + PADH, rot: s.rot }; };
  const B = {}; Object.keys(ST).forEach(k => B[k] = box(k));
  const rows = keys.map(k => {
    let cx, cy, w, h, roll;
    if (k.st) { const b = B[k.st]; cx = b.x; cy = b.y; w = b.w; h = b.h; roll = -b.rot; }
    else if (k.mid) { const a = B[k.mid[0]], b = B[k.mid[1]]; cx = (a.x + b.x) / 2; cy = (a.y + b.y) / 2; w = (a.w + b.w) / 2; h = (a.h + b.h) / 2; roll = (-a.rot - b.rot) / 2 + (k.rollAdd || 0); }
    else { cx = 4200; cy = 4200; w = 8900; h = 8900; roll = 0; }
    const r = -roll * Math.PI / 180, dx = k.dx || 0, dy = k.dy || 0;
    cx += dx * Math.cos(r) - dy * Math.sin(r); cy += dx * Math.sin(r) + dy * Math.cos(r);
    const s = Math.min(W / w, H / h) * (k.z || 1);
    return { t: k.t, cx, cy, ls: Math.log(s), roll, tilt: k.tilt || 0 };
  });
  const ts = rows.map(r => r.t);
  const f = {}; ['cx', 'cy', 'ls', 'roll', 'tilt'].forEach(c => f[c] = monotone(ts, rows.map(r => r[c])));
  CAM = T => ({ cx: f.cx(T), cy: f.cy(T), s: Math.exp(f.ls(T)), roll: f.roll(T), tilt: f.tilt(T) });
}
function shakeAt(T) {
  let x = (Math.sin(T * 1.7) + Math.sin(T * 2.9 + 1.3) * .6) * 2.2, y = (Math.sin(T * 2.3 + .5) + Math.sin(T * 3.7 + 2.1) * .5) * 1.8, r = Math.sin(T * 1.1 + .3) * .12;
  shakes.forEach(s => { if (T >= s.t) { const k = Math.exp(-(T - s.t) * 9) * s.a; x += Math.sin((T - s.t) * 70) * k; y += Math.cos((T - s.t) * 83) * k * .8; } });
  return { x, y, r };
}
window.camSpeed = T => { const a = CAM(T), b = CAM(T + 1 / 100); return { v: Math.hypot((b.cx - a.cx) * a.s, (b.cy - a.cy) * a.s) * 100, z: (Math.log(b.s) - Math.log(a.s)) * 100, s: a.s }; };

/* ---------------------------------------------------------- fx canvas */
const cv = $('#fx'); cv.width = W; cv.height = H; const ctx = cv.getContext('2d');
const PR = rng(42);
const parts = [...Array(170)].map(() => ({ x: PR(), y: PR(), d: .25 + PR() * 2.0, a: PR(), amb: PR() < .16 }));
const glyphs = ['03', '+', '₪', '24/7', '×', '08'].map((g, i) => ({ g, x: PR(), y: PR(), d: 2.4 + PR() * 1.2 }));
function drawFX(T, c, vel) {
  ctx.clearRect(0, 0, W, H);
  const span = 1.5, sp = Math.hypot(vel.x, vel.y);
  const wrap = (v, L) => ((v % L) + L) % L;
  for (const p of parts) {
    const k = p.d * .2;
    const sx = wrap(p.x * W * span - c.cx * c.s * k, W * span) - W * (span - 1) / 2;
    const sy = wrap(p.y * H * span - c.cy * c.s * k, H * span) - H * (span - 1) / 2;
    const fg = p.d > 1.75;
    const col = p.amb ? '255,182,39' : '190,215,255';
    const al = fg ? .07 : (.08 + .22 * p.a) * (.6 + .4 * Math.sin(T * 2 + p.a * 9));
    if (sp > 400) {
      const L = Math.min(260, sp * .03 * p.d);
      ctx.strokeStyle = `rgba(${col},${al * .9})`; ctx.lineWidth = fg ? 6 : 1.5;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx - vel.x / sp * L, sy - vel.y / sp * L); ctx.stroke();
    } else {
      ctx.fillStyle = `rgba(${col},${al})`; ctx.beginPath(); ctx.arc(sx, sy, fg ? 8 + p.d * 5 : 1 + p.d * 1.2, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.save(); ctx.lineWidth = 3; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const g of glyphs) {
    const k = g.d * .2, span2 = 2.2;
    const sx = wrap(g.x * W * span2 - c.cx * c.s * k, W * span2) - W * (span2 - 1) / 2;
    const sy = wrap(g.y * H * span2 - c.cy * c.s * k, H * span2) - H * (span2 - 1) / 2;
    ctx.font = `900 ${Math.round(420 * c.s ** .3)}px Heebo`;
    ctx.strokeStyle = 'rgba(169,200,255,.06)'; ctx.strokeText(g.g, sx, sy);
  }
  ctx.restore();
}

/* ---------------------------------------------------------- seek */
const world = $('#world'), light = $('#light'), hud = $('#hud'), flashEl = $('#flash');
const pad2 = n => String(n).padStart(2, '0');
function seek(T) {
  tl.time(Math.min(T, tl.duration()), false);
  if (T > tl.duration()) tl.progress(1);
  frameFns.forEach(f => f(T));
  const c = CAM(T), c0 = CAM(Math.max(0, T - 1 / 60)), sh = shakeAt(T);
  world.style.transform = `translate(${W / 2 + sh.x}px,${H / 2 + sh.y}px) rotateX(${c.tilt}deg) rotateZ(${c.roll + sh.r}deg) scale(${c.s}) translate(${-c.cx}px,${-c.cy}px)`;
  const vel = { x: (c.cx - c0.cx) * c.s * 60, y: (c.cy - c0.cy) * c.s * 60 };
  // rotate velocity into screen space
  const rr = c.roll * Math.PI / 180; const vs = { x: vel.x * Math.cos(rr) - vel.y * Math.sin(rr), y: vel.x * Math.sin(rr) + vel.y * Math.cos(rr) };
  drawFX(T, c, vs);
  const spd = Math.hypot(vs.x, vs.y);
  hud.style.setProperty('--xh', clamp((spd - 300) / 2500, 0, .9));
  light.style.setProperty('--lx', (50 + Math.sin(T * .35) * 18) + '%'); light.style.setProperty('--ly', (40 + Math.cos(T * .27) * 12) + '%');
  $('#hcoord').textContent = `X ${c.cx.toFixed(1).padStart(6, '0')}  Y ${c.cy.toFixed(1).padStart(6, '0')}  Z ${c.s.toFixed(2)}×  R ${c.roll.toFixed(1)}°`;
  const fr = Math.floor(T * 30); $('#htc').textContent = `00:00:${pad2(Math.floor(fr / 30))}:${pad2(fr % 30)}`;
  const bw = 200 * c.s; $('#hsb').style.width = bw + 'px'; $('#hsl').textContent = `1:${Math.round(20 / c.s) * 5}`;
  let fa = 0; flashes.forEach(f => { if (T >= f.t) fa = Math.max(fa, f.a * Math.exp(-(T - f.t) * 10)); }); flashEl.style.opacity = fa;
}
window.seek = seek; window.DUR = DUR; window.ASPECT = A;

window.__ready = (async () => {
  await document.fonts.ready;
  await Promise.all(['300', '400', '700', '900'].map(w => document.fonts.load(`${w} 40px Heebo`, 'אבגד 0123')));
  await document.fonts.load('400 40px "Suez One"', 'מתאימים');
  await document.fonts.load('400 40px "IBM Plex Mono"', 'AB01'); await document.fonts.load('600 40px "IBM Plex Mono"', 'AB01');
  await Promise.all($$('img').map(i => i.complete ? 1 : new Promise(r => { i.onload = r; i.onerror = r; })));
  buildCamera();
  SFX.sort((a, b) => a.t - b.t);
  seek(0);
  // sanity: every word-mask must have an animation
  return true;
})();
if (!navigator.webdriver) { window.__ready.then(() => { const t0 = performance.now(); const loop = () => { const T = ((performance.now() - t0) / 1000) % DUR; seek(T); requestAnimationFrame(loop); }; if (qs.get('play')) loop(); else seek(+qs.get('t') || 0); }); }
})();
