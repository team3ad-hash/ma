import numpy as np, subprocess, wave
SR = 48000; T = 30.0; N = int(SR * T); VO_OFF = 0.70
rng = np.random.default_rng(7)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N); FX = np.zeros(N)  # FX -> reverb send

def env_adsr(n, a, d, s, r, sus_len):
    a, d, r = int(a * SR), int(d * SR), int(r * SR); sl = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False), np.full(sl, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]
def onepole_lp(x, fc):
    fc = np.broadcast_to(fc, x.shape); y = np.zeros_like(x); a = 1 - np.exp(-2 * np.pi * fc / SR); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y
def lp_fast(x, fc):  # 2x one-pole, constant cutoff, vectorised via lfilter-like recursion in numpy
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def saw(f, tt): return 2 * ((f * tt) % 1) - 1
def add(sig, t0, gain=1.0, pan=0.0, send=0.0):
    i = int(t0 * SR); n = min(len(sig), N - i)
    if n <= 0 or i < 0: return
    s = sig[:n] * gain
    L[i:i + n] += s * np.sqrt(.5 * (1 - pan)) * 1.414 / 1.414; R[i:i + n] += s * np.sqrt(.5 * (1 + pan)) * 1.414 / 1.414
    FX[i:i + n] += s * send

# ---------- drone bed ----------
def drone():
    f0 = 55.0
    x = np.zeros(N)
    for f, a in [(f0, 1), (f0 * 1.003, .7), (f0 * 1.5, .35), (f0 * 2, .3), (f0 * 2.997, .12)]:
        x += a * saw(f, t)
    x = lp_fast(x, 380)
    lfo = .75 + .25 * np.sin(2 * np.pi * .13 * t)
    e = np.interp(t, [0, .3, 4, 10, 18, 21.3, 21.5, 30], [0, .45, .55, .7, .8, .9, 0, 0]) * lfo
    return x * e * .12
d = drone(); L += d; R += d

# ---------- chord pads (strings-ish) ----------
NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
CHORDS = [  # t0, t1, midi notes
    (10.40, 13.40, [41, 53, 57, 60, 65]),      # F
    (13.38, 16.30, [48, 55, 60, 64, 67]),      # C
    (16.30, 18.32, [43, 55, 59, 62, 67]),      # G
    (18.32, 21.45, [45, 57, 60, 64, 69]),      # Am
    (21.45, 30.00, [33, 45, 57, 61, 64, 69, 73, 76]),  # A major (resolution)
]
for (a, b, notes) in CHORDS:
    n = int((b - a + 1.2) * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for k, m in enumerate(notes):
        f = NOTE(m)
        for dt in (-.08, .0, .08):
            x += saw(f * 2 ** (dt / 12), tt + rng.random()) * (.5 if m < 50 else .32)
    x = lp_fast(x, 1400 if a < 21 else 2600)
    sus = b - a
    e = env_adsr(n, .6 if a < 21 else .05, .3, .85, 1.2, sus)
    if a >= 21: e *= np.interp(tt, [0, 6, 8.55], [1.2, .9, 0])
    vol = {10.40: .055, 13.38: .06, 16.30: .065, 18.32: .075, 21.45: .11}[a]
    xs = x * e * vol
    add(xs, a - .2, 1, -.25, .5); add(np.roll(xs, 300), a - .2, 1, .25, .5)

# ---------- pulse bass (8ths @100bpm) ----------
BPM = 100; step = 60 / BPM / 2
BASS = [(4.10, 10.40, 33), (10.40, 13.40, 29), (13.38, 16.30, 36), (16.30, 18.32, 31), (18.32, 21.30, 33)]
for (a, b, m) in BASS:
    k = 0; tk = a
    while tk < b:
        n = int(.26 * SR); tt = np.arange(n) / SR; f = NOTE(m + (12 if k % 4 == 3 else 0))
        x = saw(f, tt) + .5 * saw(f * 1.005, tt)
        prog = (tk - 4.1) / 17
        x = lp_fast(x, 220 + 900 * prog + 600 * (k % 2 == 0)) * np.exp(-tt * 9) * (.16 + .1 * prog)
        x += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * .22
        add(x, tk, 1, 0, .05); tk += step; k += 1

# ---------- clock ticks ----------
tk = 1.75; k = 0
while tk < 21.3:
    n = int(.03 * SR); tt = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 5000) * np.exp(-tt * 260) * (.10 if k % 2 == 0 else .05)
    if tk > 10.4: x *= 1.2
    add(x, tk, 1, .35 if k % 2 else -.35, .2); tk += step / 2 if tk > 13.38 else step; k += 1

# ---------- hits ----------
def hit(t0, size=1.0):
    n = int(2.6 * SR); tt = np.arange(n) / SR
    f = 38 + 90 * np.exp(-tt * 14); ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-tt * 2.2) * .9
    nz = lp_fast(rng.standard_normal(n), 2400) * np.exp(-tt * 9) * .5
    cr = hp(rng.standard_normal(n), 3000) * np.exp(-tt * 30) * .25
    add((sub + nz + cr) * size, t0, .55, 0, .6)
for (tt0, s) in [(.62, .8), (.66, .4), (.92, .35), (1.22, .55), (2.36, .45), (3.21, .45), (4.12, .7), (5.40, .3), (10.45, .8), (11.30, .35), (13.38, 1.0), (15.55, .5), (16.35, .55), (18.32, .8), (19.53, .7), (21.45, 1.25), (23.05, .55), (24.30, .6)]:
    hit(tt0, s)

# ---------- risers & whooshes ----------
def riser(t_end, dur, g=.35):
    n = int(dur * SR); tt = np.arange(n) / SR; p = tt / dur
    x = bp(rng.standard_normal(n), 300, 6000) * p ** 2.2
    f = 200 * 2 ** (p * 3.2); x += np.sin(2 * np.pi * np.cumsum(f) / SR) * p ** 3 * .35
    add(x * g, t_end - dur, 1, 0, .7)
def whoosh(tc, dur=.9, g=.35, pan=0):
    n = int(dur * SR); tt = np.arange(n) / SR; p = tt / dur
    e = np.sin(np.pi * p) ** 2
    x = rng.standard_normal(n)
    x = bp(x, 400, 3500) * e
    add(x * g, tc - dur / 2, 1, pan, .5)
riser(.62, .55, .2); riser(10.45, 1.6, .28); riser(13.38, 1.3, .3); riser(18.32, 1.1, .25); riser(21.45, 2.2, .4)
for (tc, d_, g, p) in [(2.0, 1.0, .35, -.5), (4.0, 1.1, .4, .5), (5.2, .8, .25, 0), (8.1, .9, .2, -.4), (10.6, 1.4, .35, .5), (12.1, 1.2, .25, -.5), (16.4, 1.2, .35, 0), (17.6, 1.4, .3, .5), (20.95, 1.2, .4, -.3)]:
    whoosh(tc, d_, g, p)

# ---------- UI blips / data ----------
def blip(t0, f=1900, g=.12, dur=.07, pan=0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 45) + .3 * np.sin(2 * np.pi * f * 2.01 * tt) * np.exp(-tt * 70)
    add(x * g, t0, 1, pan, .35)
for (tt0, f, p) in [(5.40, 1760, -.4), (5.80, 2090, .4), (6.40, 1568, -.4), (6.55, 1760, .2), (6.85, 2349, -.2), (7.05, 2637, .3), (8.35, 2093, -.2), (8.55, 2349, .2), (8.75, 2637, 0)]:
    blip(tt0, f, .14, .09, p); blip(tt0 + .07, f * 1.5, .07, .07, p)
# snap / armed
blip(8.85, 3135, .16, .12); blip(8.95, 4186, .1, .1)
for k in range(3): blip(9.45 + k * .09, [1318, 1661, 1975][k], .15, .18)
# typing ticks during flick/mono texts
for (a, b) in [(.25, .9), (10.46, 11.1), (13.6, 15.0)]:
    tk = a
    while tk < b:
        blip(tk, 3000 + rng.random() * 1500, .035, .02, rng.uniform(-.5, .5)); tk += .04 + rng.random() * .03
# signal pulses
for i in range(5):
    for k in range(4):
        tk = 10.6 + i * .55 + k * 1.9
        if tk < 16.5: blip(tk, 1200 + i * 120, .05, .12, .3)
# alarm event & handled chime
for k in range(6): blip(14.2 + k * .22, 1760 if k % 2 else 1318, .07, .16, .5)
for k, f in enumerate([1318, 1661, 1975, 2637]): blip(15.55 + k * .06, f, .1, .4)
# counters
for (a, b) in [(18.34, 19.2), (19.53, 20.4)]:
    tk = a
    while tk < b: blip(tk, 2400, .045, .02); tk += .035 + (tk - a) * .05
# decrypt 24/7
for k in range(12): blip(13.42 + k * .03, 2000 + k * 120, .04, .03)
# logo shimmer
n = int(3 * SR); tt = np.arange(n) / SR; sh = np.zeros(n)
for f in [NOTE(81), NOTE(85), NOTE(88), NOTE(93)]: sh += np.sin(2 * np.pi * f * tt + rng.random() * 6)
sh *= np.exp(-tt * 1.2) * np.clip(tt * 8, 0, 1) * .03; add(sh, 22.35, 1, 0, .9)

# ---------- reverb on FX send ----------
ir_n = int(2.8 * SR); irt = np.arange(ir_n) / SR
ir = rng.standard_normal(ir_n) * np.exp(-irt * 2.4); ir = lp_fast(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
def conv(a, b):
    n = len(a) + len(b); nf = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, nf) * np.fft.rfft(b, nf), nf)[:len(a)]
rv = conv(FX, ir) * .45
rvR = conv(FX, np.roll(ir, 731)) * .45
L += rv; R += rvR

# ---------- VO + ducking ----------
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'vo.mp3', '-ar', str(SR), '-ac', '1', '-f', 'f32le', 'vo.raw'], check=True)
vo = np.fromfile('vo.raw', dtype=np.float32).astype(np.float64)
vo = hp(vo, 70)
V = np.zeros(N); i0 = int(VO_OFF * SR); V[i0:i0 + len(vo)] = vo[:N - i0]
envv = np.sqrt(np.maximum(lp_fast(V ** 2, 8), 0)); envv /= envv.max() + 1e-9
duck = 1 - .5 * np.clip(envv * 3, 0, 1)
duck = lp_fast(duck, 4)
M = np.stack([L, R]) * duck * .42
# small VO room
vr = conv(V, ir) * .06
mix = M + np.stack([V * 1.0 + vr, V * 1.0 + vr])
# master: soft clip + fade
fade = np.interp(t, [0, .02, 28.6, 30], [0, 1, 1, 0])
mix *= fade
pk = np.max(np.abs(mix)); mix = np.tanh(mix / pk * 1.2) * .95
out = (mix.T * 32767).astype(np.int16)
with wave.open('mix_pre.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok', pk)
sp = envv > .15
db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
print('VO during speech', round(db(V[sp]), 1), 'music during speech', round(db(M[0][sp]), 1), 'music in gaps', round(db(M[0][~sp]), 1))
