"""Procedural sound design for the blueprint film.
Reads events.json (timeline events + camera speed curve exported by the page)
and writes sfx.wav (stereo, 48 kHz) aligned to VIDEO time (timeline - PRE)."""
import json, sys
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
PRE = 0.25          # video starts at timeline t=0.25
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
out = np.zeros((N, 2))
here = sys.argv[1] if len(sys.argv) > 1 else '.'
ev = json.load(open(f'{here}/events.json'))

def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype='band', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def lp(x, f, order=2):
    sos = signal.butter(order, f, btype='low', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def hp(x, f, order=2):
    sos = signal.butter(order, f, btype='high', fs=SR, output='sos'); return signal.sosfilt(sos, x)
def env(n, a, d):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d); return e
def place(sig, t, gain=1.0, pan=0.0):
    t -= PRE
    i = int(round(t * SR))
    if i >= N or i + len(sig) <= 0: return
    s = sig
    if i < 0: s = s[-i:]; i = 0
    s = s[:N - i]
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    out[i:i + len(s), 0] += s * gain * l
    out[i:i + len(s), 1] += s * gain * r

def boom(f0=80, f1=42, dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, .004, dur / 3.5)
def click(dur=.012, f=3500):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * .6 + rng.standard_normal(n) * .4) * env(n, .0003, dur / 4)
def noise_burst(dur, lo, hi, a=.002, d=None):
    n = int(dur * SR); return bp(rng.standard_normal(n), lo, hi) * env(n, a, d or dur / 3)

# --- camera whooshes, driven by the exported speed curve
sp = np.array([s['v'] for s in ev['speed']]); zr = np.array([abs(s['z']) for s in ev['speed']])
tt = np.arange(len(sp)) / 100.0 - PRE
tv = np.arange(N) / SR
speed = np.interp(tv, tt, sp); zoom = np.interp(tv, tt, zr)
amp = np.clip(speed / 4500, 0, 1) ** 1.4 + np.clip(zoom / 4, 0, .6) ** 1.6 * .5
amp = lp(amp, 8)
base = rng.standard_normal((N, 2))
low = lp(base, 700); mid = bp(base, 600, 3500); air = hp(base, 5000)
bright = np.clip(speed / 5000, 0, 1)[:, None]
wh = (low * 1.6 + mid * (0.25 + bright * .9) + air * bright * .25) * amp[:, None]
out += wh * .55

# --- event sounds
for e in ev['sfx']:
    t, ty = e['t'], e['type']; soft = e.get('soft', 0)
    if ty == 'tick':
        place(click(.010, 2600 + rng.random() * 1800), t, .05 if soft else .09, rng.uniform(-.4, .4))
    elif ty == 'rise':
        n = int(.22 * SR); x = bp(rng.standard_normal(n), 1800, 7000) * np.sin(np.linspace(0, np.pi, n)) ** 2
        place(x, t - .02, .05, rng.uniform(-.3, .3))
    elif ty == 'slam':
        g = .5 if soft else 1.0
        place(boom(90, 44, 1.0), t, .55 * g)
        place(noise_burst(.25, 200, 2500, .001, .05), t, .35 * g)
        place(click(.02, 1800), t, .25 * g)
    elif ty == 'check':
        place(click(.012, 2200), t, .14, .2); place(click(.010, 3400), t + .045, .11, .2)
    elif ty == 'draw':
        dur = min(e.get('dur', .6), 1.6); n = int(dur * SR)
        x = bp(rng.standard_normal(n), 2500, 9000)
        jit = lp(np.abs(rng.standard_normal(n)), 40); jit /= jit.max() + 1e-9
        x *= jit * np.sin(np.linspace(0, np.pi, n)) ** .5
        place(x, t, .045, rng.uniform(-.5, .5))
    elif ty == 'plate':
        place(noise_burst(.35, 300, 4000, .01, .09), t, .16)
        place(click(.03, 900), t + .05, .18)
    elif ty == 'pop':
        n = int(.09 * SR); tt2 = np.arange(n) / SR; f = 700 + 900 * tt2 / .09
        place(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .03), t, .16)
    elif ty == 'stamp':
        place(boom(70, 36, 1.6), t, 1.0)
        place(noise_burst(.18, 80, 1200, .0005, .04), t, .9)
        place(noise_burst(.4, 1500, 8000, .001, .06), t, .25)

# --- riser into the pull-back, downlifter after
t0, t1 = 21.6, 23.55
n = int((t1 - t0) * SR); x = rng.standard_normal(n); k = np.linspace(0, 1, n)
riser = np.zeros(n)
for j, (lo, hi) in enumerate([(300, 900), (900, 2500), (2500, 7000)]):
    seg = bp(x, lo, hi); w = np.clip(k * 3 - j, 0, 1); riser += seg * w
riser *= k ** 2.2
place(riser, t0, .2)
place(boom(60, 30, 2.4), 23.5, .5)

# soft room tone so silence never reads as dead air
out += np.stack([lp(rng.standard_normal(N), 220), lp(rng.standard_normal(N), 220)], 1) * .012

out = np.tanh(out * 1.1) * .9
sf.write(f'{here}/sfx.wav', out.astype(np.float32), SR)
print('sfx peak', np.abs(out).max())
