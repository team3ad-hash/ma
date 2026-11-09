// ============================================================
//  TEAM 3 — "מגנים עליכם מכל כיוון"  |  single-take blueprint film
//  Deterministic: window.render(t) draws the exact frame at time t.
// ============================================================
'use strict';
const W = innerWidth, H = innerHeight, VERT = H > W;
const U = Math.min(W, H) / 1080;
document.documentElement.style.setProperty('--u', U);
const D2R = Math.PI / 180;
const P = 1500 * (VERT ? 1.4 : 1);          // perspective distance (px)
const SW = Math.round(W * 1.9), SH = Math.round(H * 2.4); // stage (oversized so tilt never shows an edge)
const ZB = VERT ? W / 1250 : W / 1920;       // base zoom so framing adapts per aspect
const TOTAL = 30;

// ---------- helpers ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, t0, d) => clamp((t - t0) / d);
const E = {
  lin: t => t,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inCubic: t => t * t * t,
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inExpo: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
  inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
  outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  outQuint: t => 1 - Math.pow(1 - t, 5),
};
const smooth = (x, a, b) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
// visibility window with fades
const win = (t, a, b, fi = .3, fo = .3) => Math.min(smooth(t, a, a + fi), 1 - smooth(t, b - fo, b));
function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const noise1 = (x, s = 0) => (Math.sin(x * 1.31 + s) * .5 + Math.sin(x * 2.17 + s * 1.7) * .3 + Math.sin(x * 3.73 + s * 2.3) * .2);

const NS = 'http://www.w3.org/2000/svg';
function S(tag, attrs = {}, parent = null) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function D(tag, cls, parent, html) {
  const e = document.createElement(tag); if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  if (parent) parent.appendChild(e); return e;
}

// ---------- DOM ----------
const stage = document.getElementById('stage');
const grid = document.getElementById('grid');
const world = document.getElementById('world');
const cam = document.getElementById('cam');
const defs = document.getElementById('defs');
const typeL = document.getElementById('type');
const hud = document.getElementById('hud');
const endL = document.getElementById('end');
const anchorsL = document.getElementById('anchors');
const fog = document.getElementById('fog');
const flash = document.getElementById('flash');
Object.assign(stage.style, { width: SW + 'px', height: SH + 'px', left: (W - SW) / 2 + 'px', top: (H - SH) / 2 + 'px' });
grid.width = SW; grid.height = SH;
world.setAttribute('width', SW); world.setAttribute('height', SH);
const gctx = grid.getContext('2d');

// defs: glow filters + gradients
defs.innerHTML = `
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glowBig" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="22" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<radialGradient id="coneG" cx="0" cy="0" r="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#4FD8FF" stop-opacity=".55"/><stop offset="1" stop-color="#4FD8FF" stop-opacity="0"/></radialGradient>
<radialGradient id="softGlow"><stop offset="0" stop-color="#3A7BFF" stop-opacity=".55"/><stop offset=".5" stop-color="#22387C" stop-opacity=".25"/><stop offset="1" stop-color="#22387C" stop-opacity="0"/></radialGradient>
<radialGradient id="redGlow"><stop offset="0" stop-color="#FF4D5E" stop-opacity=".7"/><stop offset="1" stop-color="#FF4D5E" stop-opacity="0"/></radialGradient>
<pattern id="hatch" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="14" stroke="#9CC4FF" stroke-opacity=".28" stroke-width="2"/></pattern>
<pattern id="hatchBig" width="60" height="60" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="60" stroke="#9CC4FF" stroke-opacity=".18" stroke-width="5"/></pattern>
`;

// ---------- animation registry ----------
const A = [];
const on = fn => A.push(fn);
const lenCache = new WeakMap();
function L(el) { let l = lenCache.get(el); if (l === undefined) { l = el.getTotalLength ? el.getTotalLength() : 1000; lenCache.set(el, l); } return l; }
function draw(el, t0, d, ease = E.inOutCubic, tOut = null, dOut = .4) {
  el.style.strokeDasharray = '0 1e6';
  on(t => {
    const l = L(el) + 1;
    let p = ease(prog(t, t0, d));
    if (tOut !== null) p *= 1 - E.inCubic(prog(t, tOut, dOut));
    el.style.strokeDasharray = `${l * p} ${l}`;
    el.style.visibility = p <= 0 ? 'hidden' : 'visible';
  });
  return el;
}
function fade(el, t0, d, to = 1, tOut = null, dOut = .4) {
  el.style.opacity = 0;
  on(t => {
    let o = to * E.outCubic(prog(t, t0, d));
    if (tOut !== null) o *= 1 - prog(t, tOut, dOut);
    el.style.opacity = o; el.style.visibility = o <= 0.001 ? 'hidden' : 'visible';
  });
  return el;
}
function pop(el, x, y, t0, d = .45, base = '') {
  on(t => {
    const p = prog(t, t0, d), s = p <= 0 ? 0.001 : E.outBack(p);
    el.setAttribute('transform', `translate(${x},${y}) scale(${s}) ${base}`);
    el.style.visibility = p <= 0 ? 'hidden' : 'visible';
  });
  return el;
}

const C = { line: '#9CC4FF', dim: 'rgba(156,196,255,.45)', faint: 'rgba(156,196,255,.18)', cyan: '#4FD8FF', amber: '#FFB547', red: '#FF4D5E', white: '#F4F8FF', brand: '#22387C', green: '#3DF2A0' };
function stroke(w, col = C.line, extra = {}) { return Object.assign({ fill: 'none', stroke: col, 'stroke-width': w, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, extra); }
function wtext(parent, x, y, str, size, attrs = {}) {
  const e = S('text', Object.assign({ x, y, 'font-size': size, fill: C.line, 'font-family': 'Heebo', 'text-anchor': 'middle', 'dominant-baseline': 'middle' }, attrs), parent);
  e.textContent = str; return e;
}
function mtext(parent, x, y, str, size, attrs = {}) { return wtext(parent, x, y, str, size, Object.assign({ 'font-family': 'IBM Plex Mono', 'letter-spacing': size * .12 }, attrs)); }

// dimension line (technical drawing) with arrow ticks & label
function dimLine(parent, x1, y1, x2, y2, label, t0, d = .6, off = 0, size = 18, col = C.dim, tOut = null) {
  const g = S('g', {}, parent);
  const ang = Math.atan2(y2 - y1, x2 - x1), nx = -Math.sin(ang), ny = Math.cos(ang);
  const ax = x1 + nx * off, ay = y1 + ny * off, bx = x2 + nx * off, by = y2 + ny * off;
  const sw = size / 9;
  if (off) { draw(S('line', stroke(sw * .7, col, { x1, y1, x2: ax + nx * 8, y2: ay + ny * 8 }), g), t0, d * .5, E.outCubic, tOut); draw(S('line', stroke(sw * .7, col, { x1: x2, y1: y2, x2: bx + nx * 8, y2: by + ny * 8 }), g), t0, d * .5, E.outCubic, tOut); }
  draw(S('line', stroke(sw, col, { x1: ax, y1: ay, x2: bx, y2: by }), g), t0, d, E.inOutCubic, tOut);
  const tk = size * .55, dx = Math.cos(ang + Math.PI / 4) * tk, dy = Math.sin(ang + Math.PI / 4) * tk;
  draw(S('line', stroke(sw * 1.2, col, { x1: ax - dx, y1: ay - dy, x2: ax + dx, y2: ay + dy }), g), t0, d * .3, E.outCubic, tOut);
  draw(S('line', stroke(sw * 1.2, col, { x1: bx - dx, y1: by - dy, x2: bx + dx, y2: by + dy }), g), t0 + d * .7, d * .3, E.outCubic, tOut);
  const mx = (ax + bx) / 2, my = (ay + by) / 2;
  let deg = ang / D2R; if (deg > 90 || deg < -90) deg += 180;
  const bg = S('rect', { x: -label.length * size * .36, y: -size * .7, width: label.length * size * .72, height: size * 1.4, fill: '#071022' }, g);
  const tx = mtext(g, 0, 0, label, size, { fill: C.line });
  const lg = S('g', { transform: `translate(${mx},${my}) rotate(${deg})` }, g); lg.appendChild(bg); lg.appendChild(tx);
  fade(lg, t0 + d * .5, .3, 1, tOut);
  return g;
}

// world-anchored HTML label (crisp text following the camera, w/ perspective)
const ANCH = [];
function anchor(html, wx, wy, cls, style, fn) {
  const e = D('div', 'anchor ' + (cls || ''), anchorsL, html);
  if (style) Object.assign(e.style, style);
  ANCH.push({ e, wx, wy, fn }); return e;
}

// ============================================================
//  CAMERA — one continuous move (monotone cubic per channel)
// ============================================================
//            t      x      y      zoom   rot   tilt
const KF = [
  [0.0,   VERT ? 0 : 230,  VERT ? -250 : 0,   2.30,  -12,    0],
  [1.3,   VERT ? 30 : 280,  VERT ? -230 : 10,   1.85,   -6,    4],
  [2.25,  900,   -10,   1.30,   -2,    9],
  [2.75, 1300,   -10,   1.40,    0,   11],
  [3.55, 2050,   -10,   1.40,    2,   13],
  [4.35, 1720,   520,   0.62,    0,   28],
  [5.15, 1600,  1300,   0.66,   -3,   36],
  [5.80, 1090,  1620,   1.25,   -8,   32],
  [6.55, 1060,  1180,   1.15,   -5,   30],
  [7.10, 1150,  1020,   1.20,    1,   30],
  [8.10, 1520,  1380,   0.86,    4,   26],
  [9.50, 1250,  1600,   1.05,    0,   22],
  [10.7, 2550,  1450,   0.50,   -2,   18],
  [12.1, 3650,  1260,   0.36,    4,   26],
  [13.5, 5200,  1300,   0.62,    0,   30],
  [15.1, 5200,  1140,   0.98,   -3,   22],
  [16.3, 5200,  1300,   0.40,    6,   34],
  [17.7, 5320,  1300,   0.165,  14,   44],
  [19.6, 5800,  1260,   0.150,  20,   46],
  [21.05, 7500, 1250,   0.40,    6,   18],
  [22.1, 8200,  1300,   0.90,    0,    0],
  [30.0, 8200,  1300,   0.99,    0,    0],
];
function monotone(xs, ys) {
  const n = xs.length, dx = [], m = [], s = [];
  for (let i = 0; i < n - 1; i++) { dx[i] = xs[i + 1] - xs[i]; s[i] = (ys[i + 1] - ys[i]) / dx[i]; }
  m[0] = s[0]; m[n - 1] = s[n - 2];
  for (let i = 1; i < n - 1; i++) {
    if (s[i - 1] * s[i] <= 0) m[i] = 0;
    else { const w1 = 2 * dx[i] + dx[i - 1], w2 = dx[i] + 2 * dx[i - 1]; m[i] = (w1 + w2) / (w1 / s[i - 1] + w2 / s[i]); }
  }
  return x => {
    if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    const h = dx[i], t = (x - xs[i]) / h, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1];
  };
}
const ts = KF.map(k => k[0]);
const camF = [1, 2, 3, 4, 5].map(c => monotone(ts, KF.map(k => c === 3 ? Math.log(k[c]) : k[c])));
const CAM = { x: 0, y: 0, z: 1, r: 0, tilt: 0 };
function updateCam(t) {
  CAM.x = camF[0](t) + noise1(t * .7, 1) * 6 / Math.max(.3, camF[2](t) ? Math.exp(camF[2](t)) : 1);
  CAM.y = camF[1](t) + noise1(t * .6, 4) * 5;
  CAM.z = Math.exp(camF[2](t)) * ZB;
  CAM.r = camF[3](t) + noise1(t * .5, 7) * .35;
  CAM.tilt = Math.max(0, camF[4](t) + noise1(t * .4, 9) * .5);
  if (VERT) CAM.tilt *= .8;
}
function proj(wx, wy) {
  const dx = wx - CAM.x, dy = wy - CAM.y, cr = Math.cos(CAM.r * D2R), sr = Math.sin(CAM.r * D2R);
  const px = (dx * cr - dy * sr) * CAM.z, py = (dx * sr + dy * cr) * CAM.z;
  const th = CAM.tilt * D2R, s = P / (P - py * Math.sin(th));
  return { x: W / 2 + px * s, y: H / 2 + py * Math.cos(th) * s, s };
}

// ============================================================
//  GRID (infinite multi-level CAD grid on canvas)
// ============================================================
function drawGrid(t) {
  const g = gctx; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, SW, SH);
  const z = CAM.z, cr = Math.cos(-CAM.r * D2R), sr = Math.sin(-CAM.r * D2R);
  let minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
  for (const [sx, sy] of [[-SW / 2, -SH / 2], [SW / 2, -SH / 2], [SW / 2, SH / 2], [-SW / 2, SH / 2]]) {
    const wx = CAM.x + (sx * cr - sy * sr) / z, wy = CAM.y + (sx * sr + sy * cr) / z;
    minx = Math.min(minx, wx); maxx = Math.max(maxx, wx); miny = Math.min(miny, wy); maxy = Math.max(maxy, wy);
  }
  g.setTransform(1, 0, 0, 1, SW / 2, SH / 2); g.rotate(CAM.r * D2R); g.scale(z, z); g.translate(-CAM.x, -CAM.y);
  const intro = smooth(t, 0, .9);
  const levels = [20, 100, 500, 2500];
  for (const sp of levels) {
    const px = sp * z; if (px < 5) continue;
    let a = smooth(px, 6, 70) * (px > 1400 ? 1 - smooth(px, 1400, 2600) : 1);
    a *= (sp >= 500 ? .30 : .16) * intro; if (a < .005) continue;
    g.strokeStyle = `rgba(140,185,255,${a})`; g.lineWidth = (sp >= 500 ? 1.3 : 1) / z;
    g.beginPath();
    for (let x = Math.floor(minx / sp) * sp; x <= maxx; x += sp) { g.moveTo(x, miny); g.lineTo(x, maxy); }
    for (let y = Math.floor(miny / sp) * sp; y <= maxy; y += sp) { g.moveTo(minx, y); g.lineTo(maxx, y); }
    g.stroke();
    if (px > 140 && px < 2200) { // crosses at intersections
      g.strokeStyle = `rgba(170,210,255,${Math.min(.6, a * 2.2)})`; g.lineWidth = 1.4 / z; const c = 7 / z;
      g.beginPath();
      for (let x = Math.floor(minx / sp) * sp; x <= maxx; x += sp) for (let y = Math.floor(miny / sp) * sp; y <= maxy; y += sp) { g.moveTo(x - c, y); g.lineTo(x + c, y); g.moveTo(x, y - c); g.lineTo(x, y + c); }
      g.stroke();
    }
  }
}

// ============================================================
//  WORLD
// ============================================================
const layer = (name) => S('g', { id: name }, cam);
const Lnet = layer('net'), Lhook = layer('hook'), Lelev = layer('elev'), Lplan = layer('plan'), Lsig = layer('sig'), Lcc = layer('cc'), Llogo = layer('logo');

// ---------- A. HOOK — targeting reticle on a home ----------
(() => {
  const g = Lhook;
  const OUT = 2.3;
  draw(S('circle', stroke(2.2, C.line, { cx: 0, cy: 0, r: 120 }), g), -.45, .8, E.outCubic, OUT);
  draw(S('circle', stroke(1.2, C.dim, { cx: 0, cy: 0, r: 185, 'stroke-dasharray': '4 10' }), g), -.35, .9, E.outCubic, OUT);
  draw(S('circle', stroke(1, C.faint, { cx: 0, cy: 0, r: 265 }), g), -.3, 1.0, E.outCubic, OUT);
  const ring = S('g', {}, g);
  for (let i = 0; i < 72; i++) { const a = i * 5 * D2R, r1 = 272, r2 = i % 6 ? 284 : 300; S('line', stroke(i % 6 ? 1 : 2, i % 6 ? C.dim : C.line, { x1: Math.cos(a) * r1, y1: Math.sin(a) * r1, x2: Math.cos(a) * r2, y2: Math.sin(a) * r2 }), ring); }
  fade(ring, -.2, .5, 1, OUT);
  on(t => ring.setAttribute('transform', `rotate(${t * 22})`));
  for (const [x1, y1, x2, y2] of [[-420, 0, -140, 0], [140, 0, 420, 0], [0, -420, 0, -140], [0, 140, 0, 420]]) draw(S('line', stroke(1.6, C.line, { x1, y1, x2, y2 }), g), -.3, .6, E.outExpo, OUT);
  // corner brackets
  const b = 230, k = 50;
  for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) draw(S('path', stroke(3, C.cyan, { d: `M${sx * b},${sy * (b - k)} L${sx * b},${sy * b} L${sx * (b - k)},${sy * b}` }), g), -.1, .45, E.outExpo, OUT);
  // the home in the crosshair
  const house = S('path', stroke(3, C.white, { d: 'M-46,40 L-46,-6 L0,-46 L46,-6 L46,40 Z M-12,40 L-12,10 L12,10 L12,40' }), g);
  draw(house, -.2, .9, E.inOutCubic, OUT);
  const lock = S('circle', stroke(2, C.red, { cx: 0, cy: 0, r: 70 }), g);
  on(t => { const p = prog(t, .55, .5); lock.setAttribute('r', lerp(160, 70, E.outExpo(p))); lock.style.opacity = p > 0 ? (t < OUT ? (Math.sin(t * 18) > -.3 ? 1 : .35) : 0) : 0; });
  const lbl1 = mtext(g, 0, -335, 'TARGET · 31.8928N 34.8113E', 15, { fill: C.cyan }); fade(lbl1, .5, .3, 1, OUT);
  const lbl2 = mtext(g, 0, 335, 'SCAN 01 — RESIDENTIAL / COMMERCIAL', 13, { fill: C.dim }); fade(lbl2, .7, .3, 1, OUT);
})();

// ---------- B. ELEVATIONS — house & business ----------
(() => {
  const g = Lelev, T0 = 1.75, OUT = 4.6;
  // ground
  draw(S('line', stroke(2.5, C.line, { x1: 880, y1: 180, x2: 2460, y2: 180 }), g), T0, 1.2, E.inOutCubic, OUT, .5);
  const gh = S('g', {}, g); for (let x = 890; x < 2460; x += 26) S('line', stroke(1, C.faint, { x1: x, y1: 182, x2: x - 14, y2: 200 }), gh);
  fade(gh, T0 + .5, .5, 1, OUT);
  // HOUSE
  const hs = 2.1;
  draw(S('path', stroke(hs * 1.4, C.white, { d: 'M1040,180 L1040,-60 L1560,-60 L1560,180' }), g), T0 + .1, .6, E.inOutCubic, OUT);
  draw(S('path', stroke(hs * 1.4, C.white, { d: 'M1005,-55 L1300,-235 L1595,-55' }), g), T0 + .35, .55, E.inOutCubic, OUT);
  draw(S('path', stroke(hs, C.line, { d: 'M1440,-140 L1440,-200 L1485,-200 L1485,-112' }), g), T0 + .55, .35, E.inOutCubic, OUT);
  draw(S('rect', stroke(hs, C.line, { x: 1262, y: 50, width: 76, height: 130 }), g), T0 + .5, .45, E.inOutCubic, OUT);
  S('circle', { cx: 1324, cy: 118, r: 4, fill: C.line }, g);
  for (const wx of [1090, 1410]) {
    draw(S('rect', stroke(hs, C.line, { x: wx, y: 0, width: 100, height: 90 }), g), T0 + .6, .4, E.inOutCubic, OUT);
    draw(S('path', stroke(1.2, C.dim, { d: `M${wx + 50},0 L${wx + 50},90 M${wx},45 L${wx + 100},45` }), g), T0 + .8, .3, E.inOutCubic, OUT);
  }
  const hh = S('rect', { x: 1040, y: -60, width: 520, height: 240, fill: 'url(#hatch)' }, g); fade(hh, T0 + .8, .5, .5, OUT);
  dimLine(g, 1040, 180, 1560, 180, '12.40', T0 + .7, .7, 50, 17, C.dim, OUT);
  dimLine(g, 1005, -235, 1005, 180, '8.20', T0 + .8, .7, 40, 17, C.dim, OUT);
  // BUSINESS
  const B0 = 2.55;
  draw(S('path', stroke(hs * 1.4, C.white, { d: 'M1820,180 L1820,-40 L2280,-40 L2280,180' }), g), B0, .55, E.inOutCubic, OUT);
  draw(S('rect', stroke(hs, C.white, { x: 1808, y: -62, width: 484, height: 22 }), g), B0 + .2, .4, E.inOutCubic, OUT);
  draw(S('rect', stroke(hs, C.line, { x: 1860, y: -22, width: 380, height: 44 }), g), B0 + .3, .4, E.inOutCubic, OUT);
  const sign = mtext(g, 2050, 0, 'BUSINESS · עסק', 20, { fill: C.cyan }); fade(sign, B0 + .6, .3, 1, OUT);
  draw(S('path', stroke(hs, C.line, { d: 'M1840,34 L2260,34 L2285,74 L1815,74 Z' }), g), B0 + .35, .45, E.inOutCubic, OUT);
  const aw = S('g', {}, g); for (let x = 1840; x <= 2260; x += 35) S('line', stroke(1.2, C.dim, { x1: x, y1: 34, x2: x - 25 * ((x - 2050) / 210) * .0 + (x - 2050) * .06 + x - x, y2: 74 }), aw);
  for (let i = 0, x = 1840; x <= 2260; x += 35, i++) aw.children[i].setAttribute('x2', x + (x - 2050) * .06);
  fade(aw, B0 + .6, .3, 1, OUT);
  draw(S('rect', stroke(hs, C.line, { x: 1850, y: 88, width: 280, height: 92 }), g), B0 + .45, .4, E.inOutCubic, OUT);
  draw(S('path', stroke(1.2, C.dim, { d: 'M1920,88 L1920,180 M1990,88 L1990,180 M2060,88 L2060,180' }), g), B0 + .6, .3, E.inOutCubic, OUT);
  draw(S('rect', stroke(hs, C.line, { x: 2160, y: 88, width: 90, height: 92 }), g), B0 + .5, .4, E.inOutCubic, OUT);
  const bh = S('rect', { x: 1820, y: -40, width: 460, height: 220, fill: 'url(#hatch)' }, g); fade(bh, B0 + .7, .5, .5, OUT);
  dimLine(g, 1820, 180, 2280, 180, '14.00', B0 + .5, .7, 50, 17, C.dim, OUT);
  // kinetic world labels
  const st = { fontSize: 1 + 'px' };
  anchor('<span class="h900">כל בית.</span>', 1300, 270, 'kin', null, (e, t, p) => kinAnchor(e, t, p, 2.38, 4.5, 64));
  anchor('<span class="h900">כל עסק.</span>', 2050, 270, 'kin', null, (e, t, p) => kinAnchor(e, t, p, 3.23, 4.5, 64));
})();
function kinAnchor(e, t, p, t0, t1, size) {
  const a = E.outExpo(prog(t, t0, .5)), o = a * (1 - smooth(t, t1 - .3, t1));
  e.style.opacity = o; e.style.visibility = o < .01 ? 'hidden' : 'visible';
  e.style.fontSize = size * U * p.s * (CAM.z / ZB / 1.35) + 'px';
  e.style.filter = `blur(${(1 - a) * 10}px)`;
  e.style.transform = `translate(${p.x}px,${p.y}px) translate(-50%,-50%) translateY(${(1 - a) * 40}px) scale(${1 + (1 - a) * .3})`;
  e.style.letterSpacing = (1 - a) * .3 + 'em';
}

// ---------- C. FLOOR PLAN + DEVICES ----------
const PLAN = { x0: 1000, y0: 950, x1: 2300, y1: 1750 };
(() => {
  const g = Lplan, T = 3.95, wall = 18;
  const { x0, y0, x1, y1 } = PLAN;
  const fill = S('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: 'url(#hatch)', opacity: 0 }, g);
  fade(fill, T + .9, .8, .35);
  // outer walls (double line), with gaps for entrance door (1150..1240 bottom)
  const outer = `M1240,${y1} L${x1},${y1} L${x1},${y0} L${x0},${y0} L${x0},${y1} L1150,${y1}`;
  const inner = `M1240,${y1 - wall} L${x1 - wall},${y1 - wall} L${x1 - wall},${y0 + wall} L${x0 + wall},${y0 + wall} L${x0 + wall},${y1 - wall} L1150,${y1 - wall}`;
  draw(S('path', stroke(4.5, C.white, { d: outer }), g), T, 1.1, E.inOutCubic);
  draw(S('path', stroke(2, C.line, { d: inner }), g), T + .15, 1.1, E.inOutCubic);
  // interior walls
  const iw = [
    `M1500,${y0} L1500,1300 M1500,1380 L1500,${y1}`,
    `M1500,1350 L1850,1350 M1930,1350 L${x1},1350`,
    `M1950,${y0} L1950,1150 M1950,1230 L1950,1350`,
  ];
  iw.forEach((d, i) => draw(S('path', stroke(7, C.line, { d }), g), T + .45 + i * .12, .6, E.inOutCubic));
  // windows on top wall
  for (const [a, b] of [[1100, 1300], [1600, 1800], [2040, 2210]]) {
    const wg = S('g', {}, g);
    S('rect', { x: a, y: y0 - 4, width: b - a, height: wall + 8, fill: '#060d20' }, wg);
    S('path', stroke(1.6, C.cyan, { d: `M${a},${y0} L${b},${y0} M${a},${y0 + wall / 2} L${b},${y0 + wall / 2} M${a},${y0 + wall} L${b},${y0 + wall}` }), wg);
    fade(wg, T + .8, .3);
  }
  // doors: arcs
  const doors = [
    `M1150,${y1} L1150,${y1 - 90} A90,90 0 0 1 1240,${y1}`,
    `M1500,1300 L1580,1300 A80,80 0 0 1 1500,1380`,
    `M1850,1350 L1850,1270 A80,80 0 0 1 1930,1350`,
    `M1950,1150 L2030,1150 A80,80 0 0 1 1950,1230`,
  ];
  doors.forEach((d, i) => draw(S('path', stroke(1.6, C.dim, { d }), g), T + .9 + i * .08, .45));
  // furniture
  const furn = [
    ['rect', { x: 1060, y: 1030, width: 70, height: 220, rx: 10 }], ['rect', { x: 1060, y: 1030, width: 22, height: 220, rx: 6 }],
    ['circle', { cx: 1290, cy: 1140, r: 70 }], ['circle', { cx: 1290, cy: 1140, r: 34 }],
    ['rect', { x: 1060, y: 1460, width: 250, height: 60 }], ['rect', { x: 1360, y: 1440, width: 110, height: 110, rx: 8 }],
    ['rect', { x: 1600, y: 1000, width: 200, height: 240, rx: 8 }], ['rect', { x: 1610, y: 1010, width: 85, height: 50, rx: 6 }], ['rect', { x: 1705, y: 1010, width: 85, height: 50, rx: 6 }],
    ['rect', { x: 2020, y: 1010, width: 120, height: 200, rx: 8 }],
    ['rect', { x: 1600, y: 1450, width: 320, height: 80 }], ['circle', { cx: 1760, cy: 1580, r: 32 }],
    ['rect', { x: 2000, y: 1450, width: 240, height: 70 }], ['rect', { x: 2160, y: 1620, width: 100, height: 100 }],
  ];
  furn.forEach(([tag, a], i) => draw(S(tag, Object.assign(stroke(1.4, 'rgba(156,196,255,.55)'), a), g), T + 1.0 + i * .03, .5));
  // room labels
  [['סלון ומטבח', 1250, 1330], ['חדר שינה', 1725, 1290], ['חדר ילדים', 2125, 1290], ['משרד / חנות', 1900, 1640], ['כניסה', 1195, 1690]].forEach(([s, x, y], i) => {
    const e = wtext(g, x, y, s, i === 4 ? 16 : 22, { fill: 'rgba(200,222,255,.75)', 'font-weight': 300 });
    fade(e, T + 1.2 + i * .06, .4);
  });
  // overall dimensions
  dimLine(g, x0, y0, x1, y0, '13.00', T + .8, .8, -70, 20, C.dim);
  dimLine(g, x0, y0, x0, y1, '8.00', T + .9, .8, 70, 20, C.dim);
  dimLine(g, x1, y0, x1, 1350, '4.00', T + 1.0, .6, -60, 18, C.faint);
})();

// devices
const DEV = [];
function device(kind, x, y, aim, t0, name, spec, lx, ly) {
  const g = S('g', {}, Lplan);
  const halo = S('circle', { cx: 0, cy: 0, r: 46, fill: 'url(#softGlow)' }, g);
  const ring = S('circle', stroke(2.2, C.cyan, { cx: 0, cy: 0, r: 30 }), g);
  const sym = S('g', { transform: `rotate(${aim})`, filter: 'url(#glow)' }, g);
  const sc = { stroke: C.white, fill: 'none', 'stroke-width': 3, 'stroke-linejoin': 'round' };
  if (kind === 'cam') { S('rect', Object.assign({ x: -18, y: -9, width: 28, height: 18, rx: 3 }, sc), sym); S('path', Object.assign({ d: 'M10,-7 L20,-11 L20,11 L10,7' }, sc), sym); S('circle', { cx: 0, cy: 0, r: 3, fill: C.red }, sym); }
  if (kind === 'pir') { S('path', Object.assign({ d: 'M-14,8 A14,14 0 0 1 14,8 Z' }, sc), sym); S('line', Object.assign({ x1: -16, y1: 12, x2: 16, y2: 12 }, sc), sym); }
  if (kind === 'siren') { S('path', Object.assign({ d: 'M-14,-8 L-4,-8 L8,-16 L8,16 L-4,8 L-14,8 Z' }, sc), sym); }
  if (kind === 'mag') { S('rect', Object.assign({ x: -16, y: -10, width: 12, height: 20, rx: 2 }, sc), sym); S('rect', Object.assign({ x: 4, y: -10, width: 12, height: 20, rx: 2 }, sc), sym); }
  if (kind === 'pad') { S('rect', Object.assign({ x: -13, y: -17, width: 26, height: 34, rx: 3 }, sc), sym); for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) S('circle', { cx: -6 + i * 6, cy: -4 + j * 6, r: 1.6, fill: C.white }, sym); S('rect', { x: -8, y: -13, width: 16, height: 5, fill: C.cyan }, sym); }
  pop(g, x, y, t0, .5);
  on(t => { const p = (t - t0) % 1.6 / 1.6; ring.setAttribute('r', 30 + (t > t0 + .5 ? p * 26 : 0)); ring.style.opacity = t > t0 + .5 ? (1 - p) * .9 : 1; });
  // callout
  const cg = S('g', {}, Lplan);
  const mx = lx, my = ly;
  const leader = S('path', stroke(1.8, C.cyan, { d: `M${x},${y} L${(x + mx) / 2 + (my - y) * 0},${my} L${mx},${my}` }), cg);
  draw(leader, t0 + .15, .35, E.outCubic);
  const box = S('g', {}, cg);
  const bw = Math.max(name.length * 15 + 40, spec.length * 9.6 + 40), bx = mx < x ? mx - bw : mx;
  S('rect', { x: bx, y: my - 34, width: bw, height: 68, fill: 'rgba(5,12,28,.88)', stroke: C.cyan, 'stroke-width': 1.5 }, box);
  S('rect', { x: mx < x ? bx + bw - 6 : bx, y: my - 34, width: 6, height: 68, fill: C.cyan }, box);
  wtext(box, bx + bw / 2, my - 11, name, 24, { fill: C.white, 'font-weight': 700 });
  mtext(box, bx + bw / 2, my + 17, spec, 13, { fill: C.cyan });
  on(t => { const p = E.outExpo(prog(t, t0 + .3, .45)); box.style.opacity = p; box.setAttribute('transform', `translate(${(mx < x ? 1 : -1) * (1 - p) * -30},0)`); box.style.visibility = p <= 0 ? 'hidden' : 'visible'; });
  DEV.push({ g, x, y, t0, ring, halo });
  return g;
}
// camera FOV cones
function cone(x, y, dir, spread, R, t0, sweep = 9) {
  const g = S('g', {}, Lplan);
  const wedge = (r, a) => { const a0 = (dir - spread / 2) * D2R, a1 = (dir + spread / 2) * D2R; return `M${x},${y} L${x + Math.cos(a0) * r},${y + Math.sin(a0) * r} A${r},${r} 0 0 1 ${x + Math.cos(a1) * r},${y + Math.sin(a1) * r} Z`; };
  const layers = [1, .72, .45].map((k, i) => S('path', { d: wedge(R * k), fill: C.cyan, opacity: [.07, .09, .12][i] }, g));
  const edge = S('path', stroke(1.6, C.cyan, { d: wedge(R), opacity: .8, 'stroke-dasharray': '10 8' }), g);
  const arcs = S('g', {}, g); for (let k = 1; k <= 4; k++) { const r = R * k / 4, a0 = (dir - spread / 2) * D2R, a1 = (dir + spread / 2) * D2R; S('path', stroke(1, C.cyan, { opacity: .35, d: `M${x + Math.cos(a0) * r},${y + Math.sin(a0) * r} A${r},${r} 0 0 1 ${x + Math.cos(a1) * r},${y + Math.sin(a1) * r}` }), arcs); }
  const lab = mtext(g, x + Math.cos(dir * D2R) * (R + 34), y + Math.sin(dir * D2R) * (R + 34), `${spread}°`, 18, { fill: C.cyan });
  on(t => {
    const p = E.outExpo(prog(t, t0, .7)), sw = Math.sin((t - t0) * 1.4) * sweep;
    g.setAttribute('transform', `rotate(${sw} ${x} ${y}) translate(${x} ${y}) scale(${p || .001}) translate(${-x} ${-y})`);
    g.style.visibility = p <= 0 ? 'hidden' : 'visible';
  });
}
function waves(x, y, dir, n, t0, col = C.amber, R = 120, spread = 70) {
  const g = S('g', {}, Lplan); const arcs = [];
  for (let i = 0; i < n; i++) { const a0 = (dir - spread / 2) * D2R, a1 = (dir + spread / 2) * D2R; arcs.push(S('path', stroke(3, col, { d: `M${Math.cos(a0)},${Math.sin(a0)} A1,1 0 0 1 ${Math.cos(a1)},${Math.sin(a1)}`, 'vector-effect': 'non-scaling-stroke' }), g)); }
  on(t => {
    const on_ = t > t0;
    g.style.visibility = on_ ? 'visible' : 'hidden';
    arcs.forEach((a, i) => { const p = ((t - t0) * .9 + i / n) % 1; a.setAttribute('transform', `translate(${x},${y}) scale(${30 + p * R})`); a.style.opacity = on_ ? (1 - p) * .9 * smooth(t, t0, t0 + .3) : 0; });
  });
}
(() => {
  const { x0, y0, x1, y1 } = PLAN;
  // 5.44 cameras
  cone(x0 - 8, y1 + 8, 45, 100, 420, 5.40);
  device('cam', x0 - 8, y1 + 8, 45, 5.40, 'מצלמת אבטחה', 'CAM-01 · 4K · IR 30M', x0 - 170, y1 + 150);
  cone(x1 + 8, y0 - 8, -40, 90, 400, 5.80);
  device('cam', x1 + 8, y0 - 8, -40, 5.80, 'מצלמת IP', 'CAM-02 · 4MP · AI', x1 + 160, y0 - 140);
  // 6.4 alarm: siren + keypad
  waves(x0 - 8, 1110, 180, 4, 6.55, C.amber, 160, 80);
  device('siren', x0 - 8, 1110, 180, 6.40, 'סירנה חיצונית', 'SIREN · 120dB', x0 - 190, 1010);
  device('pad', 1275, y1 - 40, 0, 6.55, 'לוח בקרה', 'PANEL · APP', 1400, y1 + 120);
  // 6.8 detectors
  waves(x0 + 26, y0 + 26, 45, 5, 6.95, C.cyan, 330, 80);
  device('pir', x0 + 26, y0 + 26, -45 + 180, 6.85, 'גלאי נפח', 'PIR · 12M · PET', x0 + 260, y0 - 120);
  device('mag', 1195, y1 + 4, 0, 7.05, 'גלאי מגנטי', 'DOOR · CONTACT', 1020, y1 + 260);
  // 7.6 — measurements: "בדיוק במקום הנכון"
  const g = Lplan, T = 7.65;
  dimLine(g, x0 - 8, y1 + 8, 1195, y1 + 8, '1.95', T + .7, .55, 95, 18, C.cyan);
  dimLine(g, x0 - 8, y1 + 8, x0 - 8, 1110, '3.20', T + .9, .55, 120, 18, C.cyan);
  dimLine(g, x0 + 26, y0 + 26, 1290, 1140, '3.05', T + 1.1, .55, 0, 18, C.cyan);
  // snap crosshair on CAM-01
  const ch = S('g', {}, g);
  S('circle', stroke(2.5, C.amber, { cx: 0, cy: 0, r: 40 }), ch);
  S('path', stroke(2.5, C.amber, { d: 'M-70,0 L-48,0 M48,0 L70,0 M0,-70 L0,-48 M0,48 L0,70' }), ch);
  const angT = mtext(ch, 0, -92, 'Ø 45.0° ✓', 18, { fill: C.amber });
  on(t => {
    const p = prog(t, 8.85, .5), o = win(t, 8.85, 10.6, .15, .4);
    ch.setAttribute('transform', `translate(${x0 - 8},${y1 + 8}) scale(${lerp(2.4, 1, E.outExpo(p))}) rotate(${lerp(90, 0, E.outExpo(p))})`);
    ch.style.opacity = o; ch.style.visibility = o < .01 ? 'hidden' : 'visible';
  });
  // ARMED status — whole plan border glows
  const armed = S('rect', stroke(6, C.green, { x: x0 - 30, y: y0 - 30, width: x1 - x0 + 60, height: y1 - y0 + 60, rx: 18, opacity: 0, filter: 'url(#glow)' }), g);
  draw(armed, 9.45, .9, E.inOutCubic);
  on(t => { armed.style.opacity = t > 9.45 ? .85 : 0; });
  const at = S('g', {}, g); S('rect', { x: x1 - 330, y: y0 - 92, width: 330, height: 50, rx: 25, fill: 'rgba(8,40,30,.9)', stroke: C.green, 'stroke-width': 2 }, at);
  S('circle', { cx: x1 - 300, cy: y0 - 67, r: 8, fill: C.green }, at);
  wtext(at, x1 - 155, y0 - 66, 'המערכת דרוכה · ARMED', 22, { fill: C.green, 'font-weight': 700 });
  fade(at, 9.8, .3);
})();

// ---------- D. SIGNAL to CONTROL CENTER ----------
const CC = { x: 5200, y: 1300 };
const SIGPATH = 'M2300,1500 L2900,1500 L2900,1100 L3900,1100 L3900,1450 L4700,1450';
(() => {
  const g = Lsig;
  const base = S('path', stroke(3, 'rgba(79,216,255,.35)', { d: SIGPATH }), g);
  draw(base, 10.3, 1.6, E.inOutCubic);
  const dash = S('path', stroke(4, C.cyan, { d: SIGPATH, 'stroke-dasharray': '18 26' }), g);
  on(t => { dash.style.strokeDashoffset = -t * 160; dash.style.opacity = smooth(t, 10.8, 11.4); });
  // via nodes
  [[2900, 1500], [2900, 1100], [3900, 1100], [3900, 1450]].forEach(([x, y], i) => {
    const n = S('g', {}, g); S('rect', { x: -10, y: -10, width: 20, height: 20, fill: '#071022', stroke: C.cyan, 'stroke-width': 3 }, n);
    pop(n, x, y, 10.5 + i * .35, .4, 'rotate(45)');
  });
  const tx = mtext(g, 2600, 1462, 'LTE / IP · ENCRYPTED', 20, { fill: C.cyan }); fade(tx, 10.7, .3);
  const tx2 = mtext(g, 3400, 1062, 'UPLINK → 24/7 CENTER', 20, { fill: C.cyan }); fade(tx2, 11.4, .3);
  // pulses
  const sp = S('path', { d: SIGPATH, fill: 'none' }, g);
  for (let i = 0; i < 5; i++) {
    const c = S('circle', { r: 13, fill: '#CFF4FF', filter: 'url(#glow)' }, g);
    on(t => {
      const t0 = 10.6 + i * .55; if (t < t0 || t > 17.5) { c.style.visibility = 'hidden'; return; }
      const p = ((t - t0) / 1.9) % 1, l = L(sp), pt = sp.getPointAtLength(p * l);
      c.style.visibility = 'visible'; c.setAttribute('cx', pt.x); c.setAttribute('cy', pt.y); c.style.opacity = Math.sin(p * Math.PI);
    });
  }
})();
(() => {
  const g = Lcc, { x, y } = CC, T = 11.3;
  const halo = S('circle', { cx: x, cy: y, r: 900, fill: 'url(#softGlow)' }, g); fade(halo, T, 1.2, .8);
  // radar / 24h clock ring
  draw(S('circle', stroke(3, C.line, { cx: x, cy: y, r: 640 }), g), T + .2, 1.4, E.inOutCubic);
  draw(S('circle', stroke(1.4, C.dim, { cx: x, cy: y, r: 700, 'stroke-dasharray': '6 14' }), g), T + .4, 1.4, E.inOutCubic);
  const ticks = S('g', {}, g);
  for (let i = 0; i < 96; i++) { const a = (i / 96) * 2 * Math.PI - Math.PI / 2, big = i % 4 === 0, r1 = 645, r2 = big ? 690 : 665; S('line', stroke(big ? 3 : 1.4, big ? C.line : C.dim, { x1: x + Math.cos(a) * r1, y1: y + Math.sin(a) * r1, x2: x + Math.cos(a) * r2, y2: y + Math.sin(a) * r2 }), ticks); }
  for (let h = 0; h < 24; h += 3) { const a = (h / 24) * 2 * Math.PI - Math.PI / 2; mtext(ticks, x + Math.cos(a) * 750, y + Math.sin(a) * 750, String(h).padStart(2, '0') + ':00', 30, { fill: C.line }); }
  fade(ticks, T + .6, .8);
  const sweep = S('g', {}, g);
  for (let k = 0; k < 6; k++) { const a0 = -k * 6 * D2R, a1 = -(k + 1) * 6 * D2R; S('path', { d: `M${x},${y} L${x + Math.cos(a0) * 640},${y + Math.sin(a0) * 640} A640,640 0 0 0 ${x + Math.cos(a1) * 640},${y + Math.sin(a1) * 640} Z`, fill: C.cyan, opacity: .16 - k * .025 }, sweep); }
  S('line', stroke(3, C.cyan, { x1: x, y1: y, x2: x + 640, y2: y }), sweep);
  on(t => { sweep.setAttribute('transform', `rotate(${(t - T) * 95} ${x} ${y})`); sweep.style.opacity = smooth(t, T + 1, T + 1.6) * (1 - smooth(t, 17, 18)); });
  // building
  const bx0 = x - 470, by0 = y - 330, bw = 940, bh = 660;
  draw(S('rect', stroke(6, C.white, { x: bx0, y: by0, width: bw, height: bh, rx: 6 }), g), T + .5, 1.1, E.inOutCubic);
  draw(S('rect', stroke(2, C.line, { x: bx0 + 18, y: by0 + 18, width: bw - 36, height: bh - 36 }), g), T + .7, 1.1, E.inOutCubic);
  const bf = S('rect', { x: bx0, y: by0, width: bw, height: bh, fill: 'rgba(6,14,34,.92)' }, g); fade(bf, T + .6, .6);
  g.insertBefore(bf, g.lastChild.previousSibling);
  const title = wtext(g, x, by0 - 60, 'מוקד מבצעי · צוות 3', 54, { fill: C.white, 'font-weight': 900 }); fade(title, T + .9, .4);
  const sub = mtext(g, x, by0 + bh + 55, 'OPERATIONS CENTER · 24/7 · 365', 30, { fill: C.cyan }); fade(sub, T + 1.1, .4);
  // video wall: 5x3
  const MW = 150, MH = 86, GX = 22, GY = 20, mx0 = x - (5 * MW + 4 * GX) / 2, my0 = by0 + 50;
  const mon = [];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 5; c++) {
    const mg = S('g', {}, g), mx = mx0 + c * (MW + GX), my = my0 + r * (MH + GY);
    const frame = S('rect', { x: mx, y: my, width: MW, height: MH, fill: 'rgba(20,45,90,.55)', stroke: C.line, 'stroke-width': 2 }, mg);
    // tiny feed content
    const R = rng(r * 7 + c + 3);
    if ((r + c) % 3 === 0) S('path', stroke(1.6, C.dim, { d: `M${mx + 20},${my + 70} L${mx + 20},${my + 40} L${mx + 50},${my + 18} L${mx + 80},${my + 40} L${mx + 80},${my + 70} Z` }), mg);
    else if ((r + c) % 3 === 1) { S('rect', stroke(1.6, C.dim, { x: mx + 18, y: my + 16, width: MW - 36, height: MH - 32 }), mg); S('line', stroke(1.4, C.dim, { x1: mx + 70, y1: my + 16, x2: mx + 70, y2: my + MH - 16 }), mg); }
    else for (let k = 0; k < 4; k++) S('line', stroke(1.4, C.faint, { x1: mx + 12, y1: my + 18 + k * 16, x2: mx + 12 + R() * 120, y2: my + 18 + k * 16 }), mg);
    mtext(mg, mx + 28, my + 12, 'C' + String(r * 5 + c + 1).padStart(2, '0'), 10, { fill: C.cyan });
    S('circle', { cx: mx + MW - 12, cy: my + 12, r: 4, fill: C.red }, mg);
    const t0 = T + 1.0 + (r * 5 + c) * .05;
    fade(mg, t0, .25);
    mon.push({ mg, frame, mx, my });
  }
  // alarm event on monitor #7 → handled
  const ev = mon[7];
  const evr = S('rect', stroke(5, C.red, { x: ev.mx - 6, y: ev.my - 6, width: MW + 12, height: MH + 12 }), g);
  const evt = mtext(g, ev.mx + MW / 2, ev.my + MH / 2, 'ALARM', 22, { fill: C.red, 'font-weight': 700 });
  const ok = S('g', {}, g); S('rect', { x: ev.mx, y: ev.my, width: MW, height: MH, fill: 'rgba(10,60,40,.92)' }, ok); wtext(ok, ev.mx + MW / 2, ev.my + MH / 2, '✓ טופל', 30, { fill: C.green, 'font-weight': 900 });
  on(t => {
    const a = t > 14.2 && t < 15.55; evr.style.opacity = a ? (Math.sin(t * 20) > 0 ? 1 : .3) : 0; evt.style.opacity = a ? 1 : 0;
    const o = smooth(t, 15.55, 15.75); ok.style.opacity = o; ok.style.visibility = o > 0 ? 'visible' : 'hidden';
  });
  // consoles + operators
  for (let k = 0; k < 2; k++) {
    const yy = by0 + 430 + k * 110, rr = 520 - k * 60;
    const d = `M${x - 330 + k * 40},${yy} Q${x},${yy + 70} ${x + 330 - k * 40},${yy}`;
    draw(S('path', stroke(14, 'rgba(156,196,255,.5)', { d }), g), T + 1.4 + k * .15, .6);
    for (let i = 0; i < 5 - k; i++) { const px = x - 260 + k * 50 + i * (520 - k * 100) / (4 - k), py = yy + 50 + (Math.abs(px - x) < 150 ? 12 : 0); const op = S('circle', { cx: px, cy: py + 24, r: 15, fill: C.line }, g); fade(op, T + 1.7 + i * .05, .3); }
  }
})();

// ---------- E. NATIONAL NETWORK + PATROL UNITS ----------
(() => {
  const g = Lnet, R = rng(42), { x: cx, y: cy } = CC;
  const nodes = [];
  let tries = 0;
  while (nodes.length < 170 && tries++ < 5000) {
    const a = R() * Math.PI * 2, rr = Math.sqrt(R()) * 1;
    const x = cx + Math.cos(a) * rr * 4600, y = cy + Math.sin(a) * rr * 2900;
    if (x > PLAN.x0 - 250 && x < PLAN.x1 + 250 && y > PLAN.y0 - 300 && y < PLAN.y1 + 300) continue;
    if (Math.hypot(x - cx, y - cy) < 900) continue;
    if (Math.hypot(x - 8200, y - 1150) < 900) continue;
    if (x > 860 && x < 2480 && y > -320 && y < 360) continue;
    nodes.push({ x, y, d: Math.hypot((x - cx) / 4600, (y - cy) / 2900), biz: R() < .35 });
  }
  const links = S('g', {}, g), dots = S('g', {}, g);
  nodes.forEach((n, i) => {
    const t0 = 12.2 + n.d * 4.2;
    const l = S('line', stroke(4, 'rgba(79,216,255,.22)', { x1: cx, y1: cy, x2: n.x, y2: n.y }), links);
    draw(l, t0 - .4, .6, E.outCubic);
    const s = n.biz ? 26 : 20;
    const e = n.biz ? S('rect', { x: -s, y: -s, width: 2 * s, height: 2 * s, fill: '#071022', stroke: C.cyan, 'stroke-width': 6 }, dots)
      : S('path', { d: `M${-s},${s} L${-s},${-s * .2} L0,${-s * 1.2} L${s},${-s * .2} L${s},${s} Z`, fill: '#071022', stroke: C.white, 'stroke-width': 6 }, dots);
    pop(e, n.x, n.y, t0, .4);
  });
  // ripples on random nodes (events)
  const rip = S('g', {}, g);
  for (let k = 0; k < 14; k++) {
    const n = nodes[Math.floor(R() * nodes.length)], t0 = 15.8 + R() * 4.8, c = S('circle', stroke(8, k % 3 ? C.cyan : C.amber, { cx: n.x, cy: n.y, r: 10 }), rip);
    on(t => { const p = prog(t, t0, 1.4); c.setAttribute('r', 20 + p * 260); c.style.opacity = p > 0 && p < 1 ? (1 - p) * .9 : 0; });
  }
  // highways (smooth curves) + patrol cars
  const roads = [];
  for (let k = 0; k < 7; k++) {
    const a = k / 7 * Math.PI * 2 + R() * .4;
    const pts = []; for (let s = -1; s <= 1.001; s += .25) { const rr = s * 4800; pts.push([cx + Math.cos(a) * rr + Math.sin(s * 3 + k) * 380, cy + Math.sin(a) * rr * .62 + Math.cos(s * 2.3 + k) * 300]); }
    let d = `M${pts[0][0]},${pts[0][1]}`; for (let i = 1; i < pts.length - 1; i++) { const mx = (pts[i][0] + pts[i + 1][0]) / 2, my = (pts[i][1] + pts[i + 1][1]) / 2; d += ` Q${pts[i][0]},${pts[i][1]} ${mx},${my}`; }
    const p = S('path', stroke(10, 'rgba(156,196,255,.22)', { d }), g); draw(p, 14.6 + k * .12, 1.6, E.inOutCubic); roads.push(p);
  }
  g.insertBefore(links, g.firstChild);
  const cars = S('g', {}, g);
  for (let i = 0; i < 18; i++) {
    const road = roads[i % roads.length], spd = (.035 + R() * .03) * (R() < .5 ? 1 : -1), off = R();
    const car = S('g', { filter: 'url(#glow)' }, cars);
    S('path', { d: 'M60,0 L-40,-34 L-22,0 L-40,34 Z', fill: C.amber }, car);
    S('path', { d: 'M60,0 L320,-90 L320,90 Z', fill: C.amber, opacity: .12 }, car);
    on(t => {
      const vis = smooth(t, 15.6 + i * .05, 16.2 + i * .05) * (1 - smooth(t, 21.2, 21.8));
      car.style.visibility = vis > 0 ? 'visible' : 'hidden'; if (vis <= 0) return;
      const l = L(road); let u = ((off + t * spd) % 1 + 1) % 1; u = .06 + u * .88;
      const p0 = road.getPointAtLength(u * l), p1 = road.getPointAtLength(Math.min(l, u * l + (spd > 0 ? 5 : -5)));
      const ang = Math.atan2(p1.y - p0.y, p1.x - p0.x) / D2R;
      car.setAttribute('transform', `translate(${p0.x},${p0.y}) rotate(${ang})`); car.style.opacity = vis;
    });
  }
  on(t => { g.style.opacity = 1 - smooth(t, 21.0, 22.4) * .92; });
  const lab = mtext(g, cx + 1700, cy - 2300, 'PATROL UNITS · LIVE', 120, { fill: C.amber }); fade(lab, 16.4, .5, 1, 21.0, .5);
  const lab2 = mtext(g, cx - 2200, cy + 2500, 'NATIONWIDE COVERAGE', 120, { fill: C.cyan }); fade(lab2, 16.8, .5, 1, 21.0, .5);
})();

// ---------- G. LOGO ----------
const LOGO = { x: 8200, y: 1100, s: 1.0 };
(() => {
  const g = S('g', { transform: `translate(${LOGO.x - 180},${LOGO.y - 172})` }, Llogo), T = 21.15;
  const glow = S('circle', { cx: 180, cy: 172, r: 620, fill: 'url(#softGlow)' }, g); fade(glow, T, 1.2, 1);
  // construction lines
  const cons = S('g', {}, g);
  [[-140, 0, 500, 0], [-140, 344, 500, 344], [0, -120, 0, 464], [360, -120, 360, 464], [180, -160, 180, 504], [-180, 172, 540, 172]].forEach(([x1, y1, x2, y2], i) =>
    draw(S('line', stroke(1.2, C.dim, { x1, y1, x2, y2, 'stroke-dasharray': '8 8' }), cons), T + i * .05, .5, E.outExpo));
  draw(S('circle', stroke(1.2, C.dim, { cx: 180, cy: 172, r: 250 }), cons), T + .1, .7, E.inOutCubic);
  draw(S('circle', stroke(1.2, C.faint, { cx: 180, cy: 172, r: 300, 'stroke-dasharray': '3 9' }), cons), T + .15, .7, E.inOutCubic);
  dimLine(cons, 0, 344, 360, 344, '360', T + .3, .5, 60, 16, C.dim);
  dimLine(cons, 360, 0, 360, 344, '344', T + .35, .5, -60, 16, C.dim);
  on(t => { cons.style.opacity = 1 - smooth(t, 22.6, 23.6); });
  // outline draw then fill
  const ol = S('path', stroke(2.4, C.cyan, { d: window.LOGO_SHAPE, 'fill-rule': 'evenodd' }), g);
  draw(ol, T + .1, .95, E.inOutCubic);
  const fl = S('path', { d: window.LOGO_SHAPE, fill: '#fff', 'fill-rule': 'evenodd' }, g);
  const tx = S('path', { d: window.LOGO_TEXT, fill: C.brand }, g);
  on(t => { const p = smooth(t, T + .75, T + 1.15); fl.style.opacity = p; tx.style.opacity = smooth(t, T + .9, T + 1.25); ol.style.opacity = 1 - smooth(t, T + 1.2, T + 1.8); });
  // light sweep across logo
  const clip = S('clipPath', { id: 'logoClip' }, defs); S('path', { d: window.LOGO_SHAPE, 'clip-rule': 'evenodd' }, clip);
  const sw = S('rect', { x: -200, y: -50, width: 90, height: 460, fill: '#BFEFFF', opacity: .55, 'clip-path': 'url(#logoClip)' }, g);
  on(t => { const p = prog(t, T + 1.25, .9); sw.setAttribute('x', lerp(-200, 460, E.inOutCubic(p))); sw.setAttribute('transform', 'skewX(-18)'); sw.style.opacity = p > 0 && p < 1 ? .5 : 0; });
})();

// ============================================================
//  KINETIC TYPOGRAPHY (screen space)
// ============================================================
const TX = [];
function line(html, pos, opts = {}) {
  const e = D('div', 'line ' + (opts.cls || ''), opts.parent || typeL);
  // split into words and letters (logical order → RTL visual)
  const words = html.split(' ');
  const letters = [];
  words.forEach((w, wi) => {
    const m = w.match(/^\{(\w+)\}(.*)$/); let cls = '', txt = w; if (m) { cls = m[1]; txt = m[2]; }
    const ws = D('span', 'w ' + cls, e); ws.style.display = 'inline-block'; if (!/[\u0590-\u05FF]/.test(txt)) ws.style.direction = 'ltr';
    for (const ch of Array.from(txt)) { const l = D('span', 'l', ws); l.textContent = ch; letters.push({ l, wi }); }
    if (wi < words.length - 1) e.appendChild(document.createTextNode(' '));
  });
  Object.assign(e.style, pos);
  e.style.fontSize = (opts.size || 100) * U + 'px';
  const o = Object.assign({ e, letters, words: words.length, anim: 'rise', stagger: .028, dur: .55, out: 'up', outDur: .35, outStagger: .012, wordTimes: null }, opts);
  TX.push(o); return o;
}
function runText(o, t) {
  const { e, letters, tIn, tOut } = o;
  if (t < tIn - .01 || t > tOut + o.outDur + letters.length * o.outStagger + .05) { e.style.visibility = 'hidden'; return; }
  e.style.visibility = 'visible';
  letters.forEach((L_, i) => {
    const st = o.wordTimes ? o.wordTimes[L_.wi] + (i - letters.findIndex(q => q.wi === L_.wi)) * o.stagger : tIn + i * o.stagger;
    const p = prog(t, st, o.dur), q = prog(t, tOut + i * o.outStagger, o.outDur);
    let tr = '', op = 1, bl = 0;
    if (o.anim === 'rise') { const a = E.outExpo(p); tr = `translateY(${(1 - a) * 70}%) rotate(${(1 - a) * -6}deg)`; op = a; bl = (1 - a) * 8; }
    else if (o.anim === 'slam') { const a = E.outExpo(p); tr = `scale(${lerp(2.6, 1, a)}) translateY(${(1 - a) * -10}%)`; op = smooth(p, 0, .35); bl = (1 - a) * 14; }
    else if (o.anim === 'drop') { const a = E.outBack(p); tr = `translateY(${(1 - a) * -90}%)`; op = smooth(p, 0, .3); bl = (1 - smooth(p, 0, .6)) * 6; }
    else if (o.anim === 'track') { const a = E.outExpo(p); tr = `translateX(${(1 - a) * (i - letters.length / 2) * -18}%)`; op = a; bl = (1 - a) * 6; }
    else if (o.anim === 'flick') { op = p > 0 ? (p < .5 ? (Math.floor(t * 60 + i) % 2 ? .25 : 1) : 1) : 0; }
    if (q > 0) {
      const b = E.inCubic(q);
      if (o.out === 'up') { tr += ` translateY(${-b * 60}%)`; op *= 1 - b; bl += b * 8; }
      else if (o.out === 'blur') { op *= 1 - b; bl += b * 16; tr += ` scale(${1 + b * .3})`; }
      else if (o.out === 'down') { tr += ` translateY(${b * 60}%)`; op *= 1 - b; }
    }
    L_.l.style.transform = tr; L_.l.style.opacity = op; L_.l.style.filter = bl > .2 ? `blur(${bl}px)` : 'none';
  });
}
const vC = 'left:50%;top:50%;';
const center = (top = '50%') => ({ left: '50%', top, transform: 'translate(-50%,-50%)' });

// 0.70 HOOK
line('עדיין חושבים', VERT ? center('36%') : { right: 150 * U + 'px', top: 330 * U + 'px' }, { cls: 'h900', size: VERT ? 150 : 160, anim: 'slam', tIn: .66, tOut: 2.05, wordTimes: [.66, .92], stagger: .022, out: 'blur' });
line('על {cy}המיגון?', VERT ? center('47%') : { right: 150 * U + 'px', top: 520 * U + 'px' }, { cls: 'h900', size: VERT ? 150 : 160, anim: 'slam', tIn: 1.22, tOut: 2.12, wordTimes: [1.22, 1.38], stagger: .022, out: 'blur' });
const hookKick = line('{mono}SECURITY·CHECK·01', VERT ? center('27%') : { right: 156 * U + 'px', top: 270 * U + 'px' }, { cls: 'mono cy', size: 22, anim: 'flick', tIn: .25, tOut: 2.0, stagger: .02, out: 'up' });

// 4.14 "מתחיל בתוכנית."
const plan1 = line('מתחיל בתוכנית.', center(VERT ? '30%' : '50%'), { cls: 'h900 outline', size: VERT ? 130 : 190, anim: 'track', tIn: 4.12, tOut: 5.15, wordTimes: [4.12, 4.42], stagger: .018, dur: .6, out: 'up' });
on(t => { const f = smooth(t, 4.55, 4.9); plan1.e.style.color = `rgba(244,248,255,${f})`; });

// 5.44–7.4 device stack (right / RTL start side)
const stackPos = (i) => VERT ? { right: 70 * U + 'px', top: (250 + i * 120) * U + 'px' } : { right: 120 * U + 'px', top: (300 + i * 118) * U + 'px' };
const st1 = line('{mono}01 מצלמות אבטחה', stackPos(0), { cls: 'h900', size: 86, anim: 'rise', tIn: 5.42, tOut: 7.45, stagger: .02 });
const st2 = line('{mono}02 אזעקה', stackPos(1), { cls: 'h900', size: 86, anim: 'rise', tIn: 6.38, tOut: 7.5, stagger: .02 });
const st3 = line('{mono}03 גלאים', stackPos(2), { cls: 'h900', size: 86, anim: 'rise', tIn: 6.86, tOut: 7.55, stagger: .02 });
for (const s of [st1, st2, st3]) { const m = s.e.querySelector('.mono'); m.style.fontSize = '.32em'; m.style.color = 'var(--cyan)'; m.style.marginLeft = '.6em'; m.style.verticalAlign = 'middle'; }

// 7.6–10 "מתוכננים ומותקנים / בדיוק במקום הנכון"
const lowY = VERT ? '74%' : '76%';
const m1 = line('מתוכננים. ומותקנים.', center(VERT ? '71%' : '16%'), { cls: 'h300', size: VERT ? 78 : 70, anim: 'rise', tIn: 7.58, tOut: 10.05, wordTimes: [7.58, 8.22], stagger: .02, out: 'up' });
const m2 = line('{cy}בדיוק במקום הנכון.', center(VERT ? '78%' : '27%'), { cls: 'h900', size: VERT ? 104 : 110, anim: 'drop', tIn: 8.92, tOut: 10.1, wordTimes: [8.92, 9.3, 9.5], stagger: .018, out: 'up' });
// measuring bracket under "בדיוק"
const brk = D('div', '', typeL); Object.assign(brk.style, { position: 'absolute', height: 18 * U + 'px', borderLeft: '2px solid #FFB547', borderRight: '2px solid #FFB547', borderBottom: '2px solid #FFB547' });
const brkT = D('div', 'mono am', brk, '±0.5 CM'); Object.assign(brkT.style, { position: 'absolute', left: '50%', top: 26 * U + 'px', transform: 'translateX(-50%)', fontSize: 18 * U + 'px', whiteSpace: 'nowrap' });
on(t => {
  const w = m2.e.querySelector('.w'); const r = w.getBoundingClientRect(); const p = E.outExpo(prog(t, 9.15, .5)); const o = win(t, 9.15, 10.0, .1, .3);
  Object.assign(brk.style, { left: r.left + r.width / 2 - r.width * p / 2 + 'px', top: r.bottom + 6 * U + 'px', width: r.width * p + 'px', opacity: o });
});

// 10.48–13.1 "והכול מחובר / למוקד המבצעי / של צוות 3"
const ccPos = (i) => VERT ? center(['18%', '24%', '30%'][i]) : { right: 120 * U + 'px', top: ([250, 300, 425][i]) * U + 'px' };
const c0 = line('{mono}והכול מחובר ←', ccPos(0), { cls: 'cy', size: 40, anim: 'flick', tIn: 10.46, tOut: 13.1, stagger: .03 });
const c1 = line('למוקד המבצעי', ccPos(1), { cls: 'h900', size: VERT ? 110 : 128, anim: 'rise', tIn: 11.3, tOut: 13.15, wordTimes: [11.3, 11.62], stagger: .022 });
const c2 = line('של צוות 3', ccPos(2), { cls: 'h300', size: VERT ? 70 : 76, anim: 'rise', tIn: 12.28, tOut: 13.2, stagger: .025 });

// 13.42 "24/7" decrypt
const big247 = D('div', 'line h900', typeL); Object.assign(big247.style, center(VERT ? '50%' : '49%'), { fontSize: (VERT ? 300 : 330) * U + 'px', direction: 'ltr', letterSpacing: '-.02em', textShadow: '0 0 40px rgba(79,216,255,.55)' });
const k247 = D('div', 'line mono cy', typeL); Object.assign(k247.style, center(VERT ? '62%' : '70%'), { fontSize: 30 * U + 'px' });
on(t => {
  const a = prog(t, 13.4, .25), o = win(t, 13.4, 15.05, .12, .3);
  big247.style.opacity = o; big247.style.visibility = o > 0 ? 'visible' : 'hidden';
  const fin = '24/7'; let s = '';
  const R = rng(Math.floor(t * 30));
  for (let i = 0; i < 4; i++) { const lock = t > 13.42 + i * .12 + .15 || i === 2 && t > 13.5; s += lock ? fin[i] : String(Math.floor(R() * 10)); }
  big247.textContent = s;
  big247.style.transform = `translate(-50%,-50%) scale(${lerp(1.25, 1, E.outExpo(a)) + (t - 13.4) * .02})`;
  big247.style.filter = `blur(${(1 - E.outExpo(a)) * 12}px)`;
  const tt = Math.max(0, t - 13.6), n = Math.floor(tt / .04);
  k247.textContent = 'מוקד פעיל · 24 שעות · 7 ימים · 365 יום'.slice(0, Math.min(40, n));
  k247.style.opacity = win(t, 13.6, 15.05, .05, .3);
});

// 15.1–16.1 "מענה אנושי / תוך שנייה" + timer
const r1 = line('מענה אנושי', center(VERT ? '40%' : '41%'), { cls: 'h900', size: VERT ? 120 : 130, anim: 'rise', tIn: 15.08, tOut: 16.2, wordTimes: [15.08, 15.32], stagger: .02 });
const r2 = line('תוך {cy}שנייה', center(VERT ? '50%' : '57%'), { cls: 'h900', size: VERT ? 120 : 130, anim: 'slam', tIn: 15.55, tOut: 16.25, wordTimes: [15.55, 15.72], stagger: .02, out: 'blur' });
const timer = D('div', 'line mono am', typeL); Object.assign(timer.style, center(VERT ? '60%' : '71%'), { fontSize: 44 * U + 'px', direction: 'ltr' });
on(t => {
  const o = win(t, 15.1, 16.3, .1, .2); timer.style.opacity = o; timer.style.visibility = o > 0 ? 'visible' : 'hidden';
  const v = Math.min(.84, Math.max(0, (t - 15.15) * 1.6));
  timer.textContent = `▶ 00:00:0${v.toFixed(2)} ${v >= .84 ? '✓' : ''}`;
});

// 16.37–17.95 "ניידות סיור בכל הארץ"
const p1 = line('ניידות סיור', center(VERT ? '40%' : '44%'), { cls: 'h900', size: VERT ? 124 : 140, anim: 'rise', tIn: 16.35, tOut: 17.95, wordTimes: [16.35, 16.72], stagger: .02 });
const p2 = line('{am}בכל הארץ', center(VERT ? '50%' : '60%'), { cls: 'h300', size: VERT ? 100 : 110, anim: 'track', tIn: 16.95, tOut: 18.0, stagger: .025 });

// 18.36–21.1 STATS
const statsWrap = D('div', '', typeL); Object.assign(statsWrap.style, { position: 'absolute', inset: 0 });
function stat(num, label, pos, t0, t1, fmt) {
  const box = D('div', '', statsWrap); Object.assign(box.style, { position: 'absolute', textAlign: 'center' }, pos);
  const n = D('div', 'h900', box); Object.assign(n.style, { fontSize: (VERT ? 220 : 230) * U + 'px', lineHeight: .9, direction: 'ltr', textShadow: '0 0 50px rgba(79,216,255,.35)' });
  const bar = D('div', '', box); Object.assign(bar.style, { height: 2 * U + 'px', background: 'var(--cyan)', margin: `${14 * U}px auto` });
  const l = D('div', 'h300', box, label); Object.assign(l.style, { fontSize: 54 * U + 'px', whiteSpace: 'nowrap' });
  on(t => {
    const o = win(t, t0 - .05, t1, .15, .35), p = E.outCubic(prog(t, t0, .9));
    box.style.opacity = o; box.style.visibility = o > 0 ? 'visible' : 'hidden';
    n.textContent = fmt(Math.round(num * p));
    box.style.transform = `translate(-50%,-50%) translateY(${(1 - E.outExpo(prog(t, t0, .6))) * 60 * U}px)`;
    bar.style.width = E.outExpo(prog(t, t0 + .2, .7)) * 100 + '%';
    l.style.letterSpacing = lerp(.4, 0, E.outExpo(prog(t, t0 + .15, .8))) + 'em';
    box.style.filter = `blur(${smooth(t, t1 - .35, t1) * 10}px)`;
  });
}
stat(34, 'שנות ניסיון', VERT ? { left: '50%', top: '34%' } : { left: '70%', top: '46%' }, 18.34, 21.15, v => String(v));
stat(52000, 'לקוחות מרוצים', VERT ? { left: '50%', top: '58%' } : { left: '33%', top: '46%' }, 19.53, 21.15, v => v.toLocaleString('en-US'));
const police = D('div', 'line', typeL, '<span class="chip" style="font-weight:700">✓ מוקד מאושר ע״י משטרת ישראל</span>'); Object.assign(police.style, center(VERT ? '75%' : '74%'), { fontSize: 32 * U + 'px' });
on(t => { const o = win(t, 20.15, 21.15, .2, .3); police.style.opacity = o; police.style.visibility = o > 0 ? 'visible' : 'hidden'; police.style.transform = `translate(-50%,-50%) translateY(${(1 - E.outExpo(prog(t, 20.15, .5))) * 30}px)`; });
// darkening behind stats
const dim = D('div', '', document.getElementById('viewport')); Object.assign(dim.style, { position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%,rgba(3,6,15,.75),rgba(3,6,15,.35))', pointerEvents: 'none' });
document.getElementById('viewport').insertBefore(dim, typeL);
on(t => { dim.style.opacity = win(t, 18.2, 21.2, .4, .5); });

// ============================================================
//  END CARD
// ============================================================
const slog1 = line('מגנים עליכם', center(VERT ? '55.5%' : '61%'), { cls: 'h900', size: VERT ? 112 : 96, anim: 'rise', tIn: 22.48, tOut: 99, stagger: .025, parent: endL });
const slog2 = line('מכל כיוון.', center(VERT ? '62%' : '61%'), { cls: 'h900 cy', size: VERT ? 112 : 96, anim: 'slam', tIn: 23.05, tOut: 99, stagger: .02, parent: endL });
// horizontal layout: two parts on one line → position side by side
if (!VERT) { slog1.e.style.transform = 'translate(-8%,-50%)'; slog1.e.style.left = '50%'; slog2.e.style.left = '50%'; }
on(t => {
  if (VERT) return;
  const w1 = slog1.e.offsetWidth, w2 = slog2.e.offsetWidth, gap = 26 * U, tot = w1 + w2 + gap;
  // RTL: first phrase on the right
  slog1.e.style.transform = `translate(${tot / 2 - w1}px,-50%)`;
  slog2.e.style.transform = `translate(${-tot / 2}px,-50%)`;
});
const cta = D('div', 'cta', endL, `<span>השאירו פרטים לייעוץ והצעת מחיר</span><span style="font-size:1.1em">←</span>`);
Object.assign(cta.style, { top: (VERT ? 77.5 : 79) + '%', fontSize: (VERT ? 46 : 44) * U + 'px', padding: `${20 * U}px ${46 * U}px` });
const phone = D('div', 'line', endL, `<span class="mono" style="letter-spacing:.06em;color:#fff;font-weight:500">073-8010665</span><span style="opacity:.5;margin:0 .6em">|</span><span class="mono" style="letter-spacing:.06em;color:var(--cyan)">team3.co.il</span>`);
Object.assign(phone.style, center(VERT ? '84.5%' : '88.5%'), { fontSize: (VERT ? 40 : 36) * U + 'px', direction: 'ltr' });
const chips = D('div', 'line', endL, ['מצלמות אבטחה', 'מערכות אזעקה', 'מוקד 24/7', 'התקנה מקצועית'].map(s => `<span class="chip">${s}</span>`).join(''));
Object.assign(chips.style, center(VERT ? '69.5%' : '69.5%'), { fontSize: (VERT ? 28 : 24) * U + 'px', color: 'rgba(220,235,255,.9)' });
on(t => {
  const p = E.outBack(prog(t, 24.3, .6)), o = smooth(t, 24.3, 24.55);
  cta.style.opacity = o; cta.style.transform = `translate(-50%,-50%) scale(${.6 + .4 * p})`;
  const pulse = t > 25.2 ? 1 + Math.sin((t - 25.2) * 4) * .018 : 1; if (t > 25.2) cta.style.transform = `translate(-50%,-50%) scale(${pulse})`;
  cta.style.boxShadow = `0 0 ${(60 + Math.sin(t * 4) * 20) * U}px rgba(79,216,255,${.35 + .2 * Math.sin(t * 4)})`;
  const po = smooth(t, 24.7, 25.1); phone.style.opacity = po; phone.style.transform = `translate(-50%,-50%) translateY(${(1 - po) * 20}px)`;
  const co = smooth(t, 25.2, 25.7); chips.style.opacity = co; chips.style.letterSpacing = lerp(.25, 0, E.outExpo(prog(t, 25.2, .8))) + 'em';
  endL.style.visibility = t > 21 ? 'visible' : 'hidden';
});

// ============================================================
//  HUD
// ============================================================
const ci = 34 * U;
[['top', 'right'], ['top', 'left'], ['bottom', 'right'], ['bottom', 'left']].forEach(([v, h]) => {
  const c = D('div', 'corner', hud); c.style[v] = ci + 'px'; c.style[h] = ci + 'px';
  c.style['border' + v[0].toUpperCase() + v.slice(1) + 'Width'] = '2px'; c.style['border' + h[0].toUpperCase() + h.slice(1) + 'Width'] = '2px';
});
const hudR = D('div', 'hudtxt', hud, ''); Object.assign(hudR.style, { top: ci + 14 * U + 'px', right: ci + 64 * U + 'px', direction: 'rtl', fontFamily: 'Heebo', fontWeight: 700, letterSpacing: '.04em', fontSize: 17 * U + 'px', color: '#fff' });
hudR.innerHTML = 'צוות 3 <span style="opacity:.5;margin:0 .5em">|</span> <span style="font-weight:300">תוכנית מיגון לבית ולעסק</span>';
const hudL = D('div', 'hudtxt', hud, ''); Object.assign(hudL.style, { top: ci + 14 * U + 'px', left: ci + 64 * U + 'px', direction: 'ltr' });
const tb = D('div', '', hud); tb.id = 'titleblock';
Object.assign(tb.style, VERT ? { bottom: ci + 24 * U + 'px', left: '50%', transform: 'translateX(-50%)' } : { bottom: ci + 22 * U + 'px', left: '50%', transform: 'translateX(-50%)' });
const tbStage = D('div', '', tb), tbScale = D('div', '', tb), tbXY = D('div', '', tb), tbSheet = D('div', '', tb);
if (VERT) { tbXY.style.display = 'none'; }
const STAGES = [[0, 'אבחון'], [1.75, 'סקר שטח'], [3.95, 'תכנון'], [5.35, 'התקנה'], [10.3, 'חיבור למוקד'], [15.9, 'סיור ותגובה'], [18.2, 'ניסיון']];
function updateHUD(t) {
  const fr = Math.floor(t * 30) % 30, s = Math.floor(t);
  const rec = Math.floor(t * 2) % 2 ? '<span style="color:#FF4D5E">●</span>' : '<span style="opacity:.25">●</span>';
  hudL.innerHTML = `${rec} REC&nbsp;&nbsp;00:00:${String(s).padStart(2, '0')}:${String(fr).padStart(2, '0')}`;
  let si = 0; STAGES.forEach(([tt], i) => { if (t >= tt) si = i; });
  tbStage.innerHTML = `שלב<b>${String(si + 1).padStart(2, '0')} · ${STAGES[si][1]}</b>`;
  tbScale.innerHTML = `SCALE <b style="font-family:'IBM Plex Mono'">1:${Math.round(60 / (CAM.z / ZB))}</b>`;
  tbXY.innerHTML = `X <b style="font-family:'IBM Plex Mono'">${CAM.x.toFixed(0).padStart(5, '0')}</b> Y <b style="font-family:'IBM Plex Mono'">${CAM.y.toFixed(0).padStart(5, '0')}</b>`;
  tbSheet.innerHTML = `גיליון<b style="font-family:'IBM Plex Mono'">${String(si + 1).padStart(2, '0')}/07</b>`;
  const o = smooth(t, .3, .9) * (1 - smooth(t, 21.0, 21.6));
  tb.style.opacity = o; hudR.style.opacity = o; hudL.style.opacity = Math.max(o, 0);
  hud.querySelectorAll('.corner').forEach(c => c.style.opacity = smooth(t, .1, .6) * (1 - smooth(t, 21.0, 21.6) * .6));
}

// ============================================================
//  POST: grain, flash, fog, letterbox breath
// ============================================================
const grainC = document.getElementById('grain');
grainC.width = Math.ceil(W / 2); grainC.height = Math.ceil(H / 2);
const gc = grainC.getContext('2d');
const GR = [];
for (let k = 0; k < 8; k++) { const id = gc.createImageData(grainC.width, grainC.height), R = rng(1000 + k); for (let i = 0; i < id.data.length; i += 4) { const v = R() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } GR.push(id); }
const FLASH = [[.62, .5], [2.36, .18], [4.12, .25], [10.45, .3], [13.38, .45], [18.32, .3], [21.45, .55]];

// ============================================================
//  RENDER
// ============================================================
window.render = function (t) {
  updateCam(t);
  stage.style.transform = `perspective(${P}px) rotateX(${CAM.tilt}deg)`;
  cam.setAttribute('transform', `translate(${SW / 2},${SH / 2}) rotate(${CAM.r}) scale(${CAM.z}) translate(${-CAM.x},${-CAM.y})`);
  drawGrid(t);
  for (const f of A) f(t);
  for (const o of TX) runText(o, t);
  for (const a of ANCH) { const p = proj(a.wx, a.wy); if (a.fn) a.fn(a.e, t, p); else a.e.style.transform = `translate(${p.x}px,${p.y}px) translate(-50%,-50%)`; }
  updateHUD(t);
  fog.style.opacity = clamp(CAM.tilt / 40) * .9;
  let fl = 0; for (const [ft, a] of FLASH) { const d = t - ft; if (d > -.03 && d < .5) fl = Math.max(fl, a * Math.exp(-Math.max(0, d) * 9) * smooth(d, -.03, 0)); }
  flash.style.opacity = fl;
  gc.putImageData(GR[Math.floor(t * 24) % GR.length], 0, 0);
};
window.ready = (async () => { await document.fonts.ready; await new Promise(r => setTimeout(r, 300)); window.render(0); return true; })();
