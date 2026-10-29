"""Cinematic 120 BPM soundtrack for the Team3 Demand Gen spot (30s).

The beat grid here is the same one the visuals in index.html are cut to:
BEAT = 0.5s, hits at 8s (alarm), 14s (patrol drop) and 26s (logo).
Usage: python3 music.py out.wav
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
t_all = np.arange(N) / SR


def buf():
    return np.zeros((N, 2))


def place(dst, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    if sig.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        sig = np.stack([sig * l, sig * r], axis=1)
    dst[i : i + len(sig)] += sig * gain


def fft_filter(x, lo=None, hi=None):
    """Brick-ish band filter with soft edges, done in the frequency domain."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if X.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n=x.shape[0], axis=0)


def env(n, a, d, curve=6.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0)
    return e * np.exp(-curve * np.maximum(t - a, 0) / max(d, 1e-4))


def kick(length=0.6, f0=150, f1=42):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 5.5)
    click = rng.standard_normal(n) * np.exp(-t * 400) * 0.25
    return np.tanh((body + click) * 1.6)


def hat(length=0.08, open_=False):
    n = int(SR * (0.35 if open_ else length))
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude high-pass
    x = np.diff(np.concatenate([[0], x]))
    return x * env(n, 0.001, 0.12 if open_ else 0.03, 5) * 0.15


def clap():
    n = int(SR * 0.4)
    x = rng.standard_normal(n)
    e = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022, 0.034]):
        i = int(off * SR)
        e[i:] += np.exp(-np.arange(n - i) / SR * (60 if k < 3 else 14))
    x = fft_filter(x * e, lo=900, hi=7000)
    return x / np.max(np.abs(x)) * 0.55


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (freq * (1 + detune) * t) % 1.0
    return 2 * ph - 1


def braam(length=3.6, root=55.0):
    n = int(SR * length)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for mult, g in [(1, 1), (2, 0.6), (1.5, 0.45), (3, 0.25), (0.5, 0.8)]:
        for dt in (-0.006, 0.0, 0.007):
            x += saw(root * mult, n, dt) * g
    # growl: amplitude flutter
    x *= 1 + 0.25 * np.sin(2 * np.pi * 7 * t)
    x = fft_filter(x, lo=30, hi=900)
    e = np.minimum(t / 0.06, 1) * np.exp(-t * 0.9)
    x = np.tanh(x * 0.35) * e
    return x / np.max(np.abs(x))


def impact(length=3.0):
    n = int(SR * length)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.6)
    noise = fft_filter(rng.standard_normal(n), hi=2500) * np.exp(-t * 4) * 0.6
    tail = fft_filter(rng.standard_normal(n), lo=200, hi=1200) * np.exp(-t * 1.2) * 0.12
    x = np.tanh((boom + noise + tail) * 1.4)
    return x / np.max(np.abs(x))


def riser(length=2.0):
    n = int(SR * length)
    t = np.arange(n) / SR
    k = t / length
    noise = rng.standard_normal(n)
    # sweep band by blending progressively brighter filtered copies
    lo_ = fft_filter(noise, lo=300, hi=1500)
    hi_ = fft_filter(noise, lo=2000, hi=12000)
    x = lo_ * (1 - k) + hi_ * k
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1400 * k**2) / SR) * 0.25
    x = (x * 0.6 + tone) * k**2.2
    return x / np.max(np.abs(x))


def whoosh(length=0.7):
    n = int(SR * length)
    t = np.arange(n) / SR
    x = fft_filter(rng.standard_normal(n), lo=400, hi=5000)
    e = np.sin(np.pi * np.clip(t / length, 0, 1)) ** 3
    return x / np.max(np.abs(x)) * e


def chirp_alarm(length=1.6):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = np.where((t * 4).astype(int) % 2 == 0, 988, 740)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5
    x = fft_filter(x, lo=300, hi=3500)
    return x * np.exp(-t * 1.4) * np.minimum(t / 0.01, 1)


def tick():
    n = int(SR * 0.05)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 180) * 0.35


def main(out):
    drums, music, fx = buf(), buf(), buf()

    # --- Drone pad: A minor bed, swelling through the spot -------------------
    pad = np.zeros(N)
    for f, g in [(55, 1.0), (82.41, 0.6), (110, 0.5), (130.81, 0.35), (164.81, 0.25)]:
        for dt in (-0.004, 0.003):
            pad += saw(f, N, dt) * g
    pad = fft_filter(pad, lo=35, hi=650)
    swell = np.interp(t_all, [0, 4, 8, 8.1, 14, 26, 27, 30], [0.0, 0.35, 0.5, 0.25, 0.55, 0.7, 0.45, 0.0])
    pad = pad / np.max(np.abs(pad)) * swell * 0.32
    music += np.stack([pad, np.roll(pad, 220)], axis=1)

    # --- Clock ticks (tension, 8ths) 1.0s - 8.0s -------------------------------
    for i in range(int(1.0 / (BEAT / 2)), int(8.0 / (BEAT / 2))):
        place(fx, tick(), i * BEAT / 2, 0.5 if i % 2 == 0 else 0.25, pan=-0.3 if i % 2 else 0.3)

    # --- Heartbeat kicks 4 - 8s (beats only) -----------------------------------
    for b in range(8, 16):
        place(drums, kick(0.5, 110, 40), b * BEAT, 0.55)

    # --- Rise into the alarm hit ----------------------------------------------
    place(fx, riser(2.0), 6.0, 0.45)

    # --- ALARM HIT @ 8s ------------------------------------------------------------
    place(fx, impact(), 8.0, 0.9)
    place(music, braam(3.0, 55), 8.0, 0.55)
    place(fx, chirp_alarm(1.8), 8.0, 0.22)

    # --- Pulse bass ostinato (16ths, A) 10 - 26s, ducked by kick ------------------
    step = BEAT / 4
    bass = np.zeros(N)
    notes = [55, 55, 55, 55, 55, 55, 65.41, 55, 55, 55, 55, 55, 49, 49, 61.74, 49]
    s = int(10.0 / step)
    for i in range(s, int(26.0 / step)):
        f = notes[(i - s) % 16]
        n = int(step * SR)
        seg = saw(f, n) * env(n, 0.002, step * 0.9, 4)
        a = int(i * step * SR)
        bass[a : a + n] += seg[: N - a]
    bass = fft_filter(bass, lo=35, hi=420)
    bass = bass / np.max(np.abs(bass)) * 0.38
    # sidechain on beats
    phase = (t_all % BEAT) / BEAT
    duck = 0.35 + 0.65 * np.minimum(phase / 0.35, 1)
    bass *= duck
    music += np.stack([bass, bass], axis=1)

    # --- Mid section kicks 10 - 14s ------------------------------------------------
    for b in range(20, 28):
        place(drums, kick(), b * BEAT, 0.8)
    for i in range(int(10 / (BEAT / 2)), int(14 / (BEAT / 2))):
        place(drums, hat(), i * BEAT / 2, 0.8, pan=0.25)

    place(fx, riser(1.5), 12.5, 0.5)
    # snare roll into the drop
    for k in range(8):
        place(drums, clap(), 13.0 + k * BEAT / 4, 0.25 + k * 0.06)

    # --- DROP @ 14s: full drums until 26s -----------------------------------------
    place(fx, impact(2.4), 14.0, 0.7)
    place(fx, whoosh(0.8), 13.6, 0.4)
    for b in range(28, 52):
        place(drums, kick(), b * BEAT, 0.95)
        if b % 2 == 1:
            place(drums, clap(), b * BEAT, 0.6)
    for i in range(int(14 / (BEAT / 4)), int(26 / (BEAT / 4))):
        open_ = i % 4 == 2
        place(drums, hat(open_=open_), i * BEAT / 4, 0.9 if i % 2 == 0 else 0.5, pan=0.3 if i % 2 else -0.2)

    # Scene-change whooshes
    for at in (3.7, 9.7, 17.7, 19.7, 21.7):
        place(fx, whoosh(0.6), at, 0.35, pan=-0.4)

    # --- Final build + logo hit @ 26s -----------------------------------------
    place(fx, riser(2.0), 24.0, 0.55)
    place(fx, impact(3.5), 26.0, 1.0)
    place(music, braam(4.0, 55), 26.0, 0.6)
    # bright resolving chord tail (A major lift)
    n = int(SR * 4)
    t = np.arange(n) / SR
    chord = sum(np.sin(2 * np.pi * f * t) * g for f, g in [(220, 0.5), (277.18, 0.35), (329.63, 0.35), (440, 0.25)])
    chord *= np.minimum(t / 0.4, 1) * np.exp(-t * 0.6) * 0.25
    place(music, chord, 26.0, 1.0)

    mix = drums * 0.9 + music + fx * 0.8
    # fade the tail
    fade = np.clip((DUR - t_all) / 0.8, 0, 1)[:, None]
    mix *= fade
    mix = np.tanh(mix * 1.2) * 0.9
    mix /= np.max(np.abs(mix)) / 0.95

    pcm = (mix * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "music.wav")
