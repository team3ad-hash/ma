# Synthesizes the 22s soundtrack (pad + pulse + transition hits + alarm + notification ping).
import numpy as np, wave, os, sys
BED=('--bed' in sys.argv)  # music bed only (pad + pulse), effects come from the HyperFrames SFX library
SR=44100; D=22.0; n=int(SR*D); t=np.arange(n)/SR
out=np.zeros(n)
rng=np.random.default_rng(3)
def env(start,a,d,length):
    e=np.zeros(n); i0=int(start*SR); L=int(length*SR); x=np.arange(L)/SR
    seg=np.minimum(x/a,1)*np.exp(-x/d); e[i0:i0+L]=seg[:max(0,min(L,n-i0))]; return e
def lp(x,k):  # one-pole lowpass
    y=np.zeros_like(x); a=k; acc=0.0
    for i in range(len(x)): acc+=a*(x[i]-acc); y[i]=acc
    return y
# pad: A minor -> F major at CTA
fade=np.clip(t/1.5,0,1)*np.clip((D-t)/1.2,0,1)
chord1=[110,130.81,164.81,220]; chord2=[87.31,130.81,174.61,220]
mix=np.clip((t-17.8)/0.6,0,1)
pad=sum(np.sin(2*np.pi*f*t+np.sin(2*np.pi*0.2*t)*0.5) for f in chord1)*(1-mix)+sum(np.sin(2*np.pi*f*t) for f in chord2)*mix
out+=0.05*pad*fade*(1+0.3*np.sin(2*np.pi*0.25*t))
# kick pulse at 100 bpm
beat=60/100
for k in np.arange(0.0,17.8,beat):
    L=int(0.35*SR); x=np.arange(L)/SR; i0=int(k*SR)
    f=45+80*np.exp(-x*30); ph=2*np.pi*np.cumsum(f)/SR
    vol=0.35 if k<10.6 else 0.5
    out[i0:i0+L]+=vol*np.sin(ph)*np.exp(-x*9)
    # hat on offbeat
    h0=int((k+beat/2)*SR); hl=int(0.05*SR)
    if k>3.3 and h0+hl<n: out[h0:h0+hl]+=0.04*rng.standard_normal(hl)*np.exp(-np.arange(hl)/SR*80)
# risers into transitions, impact hits, alarm and pings (skipped for --bed)
if not BED:
    noise=rng.standard_normal(n)
    hp=noise-lp(noise,0.2)
    for s in [3.4,6.8,10.6,14.6,17.8]:
        i0=int((s-0.5)*SR); i1=int(s*SR); r=np.linspace(0,1,i1-i0)**2
        out[i0:i1]+=0.12*hp[i0:i1]*r
        out+=0.45*np.sin(2*np.pi*50*t)*env(s,0.003,0.25,1.0)
        out+=0.10*hp*env(s,0.001,0.08,0.5)
    # alarm two-tone 3.45-6.3
    for i,k in enumerate(np.arange(3.45,6.3,0.18)):
        f=960 if i%2==0 else 720; L=int(0.16*SR); i0=int(k*SR); x=np.arange(L)/SR
        sq=np.sign(np.sin(2*np.pi*f*x))*0.5+np.sin(2*np.pi*f*x)*0.5
        out[i0:i0+L]+=0.045*sq*np.minimum(1,np.minimum(x,0.16-x)*200)*(1-0.6*(k-3.45)/2.85)
    # notification ping at 8.8s and CTA button chime
    for s,fs in [(8.8,[1318.5,1760]),(18.75,[880,1318.5]),(19.2,[1760])]:
        for j,f in enumerate(fs):
            out+=0.12*np.sin(2*np.pi*f*t)*env(s+j*0.09,0.003,0.18,1.0)
    # final big hit at CTA tail
    out+=0.25*np.sin(2*np.pi*55*t)*env(17.8,0.005,1.5,4.0)
out=lp(out,0.6)
out/=np.max(np.abs(out))*1.12
st=np.stack([out,out],1)
os.makedirs('out',exist_ok=True)
with wave.open('out/soundtrack-bed.wav' if BED else 'out/soundtrack.wav','wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype('<i2').tobytes())
print('ok')
