# Composes the 22s background score (cinematic / tech, A minor) as MIDI, timed to the video's scenes,
# and renders it with FluidSynth + the FluidR3 GM soundfont (MIT licence) to out/music.wav.
# Needs: pip install mido; apt install fluidsynth fluid-soundfont-gm
import mido, subprocess, os

BEAT = 3.4 / 6            # 0.5667 s -> ~105.9 BPM: alarm on beat 6, cameras on bar 3 (6.8 s), CTA on bar 8 (18.13 s)
TPB = 480
DUR = 22.0
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'

events = []  # (beat, channel, note, velocity, length_in_beats)
def n(beat, ch, note, vel, length):
    events.append((beat, ch, note, vel, length))

# channels / GM programs
STR, BASS, PIZZ, ARP, BRASS, TIMP, PAD, DR = 0, 1, 2, 3, 4, 5, 6, 9
PROGRAMS = {STR: 48, BASS: 38, PIZZ: 45, ARP: 81, BRASS: 61, TIMP: 47, PAD: 89}
VOLUME = {STR: 92, BASS: 100, PIZZ: 80, ARP: 52, BRASS: 88, TIMP: 100, PAD: 70}

A2, C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, A4, B4, C5, E5 = 45, 48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 76
CHORDS = {'Am': [A3, C4, E4], 'F': [F3, A3, C4], 'C': [C4, E4, G4], 'G': [G3, B3, D4], 'E': [E3, G3 + 1, B3]}
ROOT = {'Am': A2, 'F': F3 - 12, 'C': C3, 'G': G3 - 12, 'E': E3 - 12}

# --- intro (beats 0-6): night, suspense -------------------------------------------------------
for c in CHORDS['Am']:
    n(0, PAD, c, 60, 6)
n(0, BASS, A2 - 12, 70, 6)
n(0, TIMP, A2, 88, 2)                                                        # opening low hit under the hook
for i, p in enumerate([A3, E4, A4, C5, A4, E4, A3, E4, A4, C5, E5, C5]):   # pizzicato heartbeat
    n(i * 0.5, PIZZ, p, 72 + i * 3, 0.45)
for b in range(2, 6):
    n(b, DR, 42, 30 + b * 6, 0.25)                                          # ticking hats
n(4.0, TIMP, A2, 50, 2)                                                      # timpani swell into the alarm
for k in range(8):
    n(4.0 + k * 0.25, TIMP, A2, 50 + k * 8, 0.25)

# --- alarm (beats 6-12): tension -----------------------------------------------------------------
for c in [A3, C4, E4, A4]:
    n(6, BRASS, c, 115, 1.5)
n(6, DR, 49, 110, 2); n(6, DR, 36, 120, 1)
for k in range(24):                                                          # strings ostinato, 16ths
    b = 6 + k * 0.25
    n(b, STR, [A3, A3, E4, A3][k % 4] + (1 if 8 <= b < 10 and k % 4 == 2 else 0), 70 + k, 0.22)
for b in range(7, 12):
    n(b, DR, 36, 105, 0.5)
    n(b + 0.5, DR, 42, 70, 0.25)
for k, b in enumerate([10, 10.5, 11, 11.25, 11.5, 11.75]):                  # tom fill into the groove
    n(b, DR, [50, 48, 47, 45, 43, 41][k], 100 + k * 4, 0.25)
n(6, BASS, A2 - 12, 100, 6)

# --- groove (beats 12-32): cameras, 24/7 center, trust ---------------------------------------------
prog = ['Am', 'F', 'C', 'G', 'E']
for bar, ch in enumerate(prog):
    b0 = 12 + bar * 4
    for c in CHORDS[ch]:
        n(b0, STR, c, 74 + bar * 5, 4)                                       # sustained strings
    for e in range(8):                                                       # pumping bass, 8ths
        n(b0 + e * 0.5, BASS, ROOT[ch] + (12 if e % 2 else 0), 104 if e % 2 == 0 else 86, 0.45)
    tones = CHORDS[ch] + [CHORDS[ch][0] + 12]
    for s in range(16):                                                      # arpeggio, 16ths
        n(b0 + s * 0.25, ARP, tones[[0, 1, 2, 3, 2, 1, 2, 3][s % 8]] + 12, 60 + (s % 4 == 0) * 14, 0.2)
    for beat in range(4):                                                    # drums
        b = b0 + beat
        if beat in (0, 2): n(b, DR, 36, 112, 0.5)
        if beat == 1: n(b + 0.5, DR, 36, 90, 0.5)
        if beat in (1, 3): n(b, DR, 38, 100, 0.5); n(b, DR, 39, 80, 0.5)
        n(b, DR, 42, 75, 0.25); n(b + 0.5, DR, 46 if beat == 3 else 42, 65, 0.25)
    if bar in (0, 2): n(b0, DR, 49, 100, 2)
# build in the last bar: snare roll + timpani crescendo into the CTA
for k in range(16):
    b = 28 + k * 0.25
    n(b, DR, 38, 60 + k * 4, 0.2)
    if k >= 8: n(b, TIMP, E3 - 12, 70 + k * 3, 0.25)
for c in [E3, G3 + 1, B3, E4]:
    n(30, BRASS, c, 80, 2)

# --- CTA (beats 32-38.8): resolve to C major ------------------------------------------------------
for c in [C3, G3, C4, E4, G4, C5]:
    n(32, STR, c, 100, 6.8)
for c in [C4, E4, G4]:
    n(32, BRASS, c, 112, 3); n(35, BRASS, c, 85, 3.8)
n(32, BASS, C3 - 12, 110, 6.8); n(32, TIMP, C3 - 12, 115, 2)
n(32, DR, 49, 120, 4); n(32, DR, 36, 120, 1); n(32, DR, 57, 90, 4)
for c in [C4, E4, G4]:
    n(32, PAD, c, 70, 6.8)
for k, p in enumerate([C5, G4, E5, C5]):                                     # gentle sparkle under the button
    n(33 + k * 0.5, ARP, p + 12, 55, 0.4)

# --- write MIDI -----------------------------------------------------------------------------------
mid = mido.MidiFile(ticks_per_beat=TPB)
tr = mido.MidiTrack(); mid.tracks.append(tr)
msgs = [(0, mido.MetaMessage('set_tempo', tempo=int(BEAT * 1e6)))]
for ch, prg in PROGRAMS.items():
    msgs.append((0, mido.Message('program_change', channel=ch, program=prg)))
    msgs.append((0, mido.Message('control_change', channel=ch, control=7, value=VOLUME[ch])))
    msgs.append((0, mido.Message('control_change', channel=ch, control=91, value=60)))   # reverb send
for b, ch, note, vel, ln in events:
    t0 = int(round(b * TPB)); t1 = int(round((b + ln) * TPB))
    msgs.append((t0, mido.Message('note_on', channel=ch, note=note, velocity=min(127, vel))))
    msgs.append((t1, mido.Message('note_off', channel=ch, note=note, velocity=0)))
msgs.sort(key=lambda m: (m[0], m[1].type == 'note_on'))
last = 0
for t, m in msgs:
    tr.append(m.copy(time=t - last)); last = t
os.makedirs('out', exist_ok=True)
mid.save('out/music.mid')

subprocess.run(['fluidsynth', '-ni', '-g', '0.45', '-r', '44100', '-F', 'out/music-raw.wav', SF2, 'out/music.mid'],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'out/music-raw.wav', '-af', f'atrim=0:{DUR},afade=t=out:st={DUR - 1.2}:d=1.2',
                'out/music.wav'], check=True)
os.remove('out/music-raw.wav')
print('ok: out/music.wav')
