"""Render the DK Insurance self-employed reel: pop-up text, punch zooms, flashes, SFX."""
import pickle, subprocess, sys, wave
import numpy as np, cv2

S = "/tmp/claude-0/-home-user-test-project/a8719c71-5fc7-50d0-9200-be02e4987cd5/scratchpad"
OUT = sys.argv[1]
W, H, FPS = 1080, 1350, 30
SLIDE = 4.2
data = pickle.load(open(f"{S}/L/layers.pkl", "rb"))
N = len(data)
TOTAL = SLIDE * N + 0.6  # small hold on last slide
NF = int(round(TOTAL * FPS))

# pop start time (seconds into slide) per element name
STARTS = {"eyebrow": 0.25, "h1": 0.45, "h2": 0.75, "h3": 1.05, "sub": 1.25, "cta": 1.6}
POP = 0.5
CTA_PULSE = 3.0


def ease_out_back(x, k=2.4):
    x = np.clip(x, 0, 1) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def pop_state(lt, start, name):
    x = (lt - start) / POP
    if x <= 0:
        return 0.0, 0.0, 0.0
    a = min(1.0, x / 0.25)
    s = 0.55 + 0.45 * ease_out_back(x, 3.0 if name == "cta" else 2.4)
    dy = 26 * (1 - min(1, x)) ** 3
    if name == "cta":
        s *= 1 + 0.07 * np.exp(-((lt - CTA_PULSE) * 7) ** 2)
    return a, s, dy


def draw_layer(frame, L, a, s, dy):
    x0, y0, x1, y1 = L["box"]
    rgb, al = L["rgb"], L["alpha"].astype(np.float32) / 255.0 * a
    h, w = al.shape
    if abs(s - 1) > 1e-3:
        nw, nh = max(1, int(w * s)), max(1, int(h * s))
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
        al = cv2.resize(al, (nw, nh), interpolation=cv2.INTER_LINEAR)
    else:
        nw, nh = w, h
    # anchor: left edge of text (box x0 + padding), vertical centre
    ax = x0 + 24
    cx = int(round(ax - (ax - x0) * s))
    cy = int(round((y0 + y1) / 2 - nh / 2 + dy))
    fx0, fy0 = max(0, cx), max(0, cy)
    fx1, fy1 = min(W, cx + nw), min(H, cy + nh)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sub_rgb = rgb[fy0 - cy:fy1 - cy, fx0 - cx:fx1 - cx].astype(np.float32)
    sub_a = al[fy0 - cy:fy1 - cy, fx0 - cx:fx1 - cx][..., None]
    reg = frame[fy0:fy1, fx0:fx1]
    frame[fy0:fy1, fx0:fx1] = reg * (1 - sub_a) + sub_rgb * sub_a


def zoom(img, z):
    if z <= 1.0005:
        return img
    nw, nh = int(W * z), int(H * z)
    big = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x, y = (nw - W) // 2, (nh - H) // 2
    return big[y:y + H, x:x + W]


Y, X = np.ogrid[:H, :W]
vign = 1 - 0.28 * (((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2) / 2
vign = vign[..., None].astype(np.float32)
rng = np.random.default_rng(7)

pops = []  # audio events
for i, d in enumerate(data):
    for L in d["layers"]:
        pops.append(i * SLIDE + STARTS[L["name"]])

# ---- audio first (ffmpeg reads it as second input) ----
SR = 44100
n = int(TOTAL * SR)
t = np.arange(n) / SR
audio = np.zeros(n, np.float32)
noise = rng.standard_normal(n).astype(np.float32)
# band-limited whoosh: smooth noise, envelope rising into each cut
def g(sig):
    k = np.exp(-0.5 * (np.arange(-4 * sig, 4 * sig + 1) / sig) ** 2); return k / k.sum()
b = (np.convolve(noise, g(3), 'same') - np.convolve(noise, g(25), 'same')) * 2.5
for k in range(1, N):
    c = k * SLIDE
    env = np.exp(-((t - c + 0.08) * 6) ** 2)
    audio += 0.9 * b * env
# pops: quick pitch-dropping sine blip
for p in pops:
    i0 = int(p * SR); L = int(0.12 * SR)
    tt = np.arange(L) / SR
    f = 950 * np.exp(-tt * 12) + 380
    blip = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38) * 0.35
    audio[i0:i0 + L] += blip[:max(0, min(L, n - i0))]
# soft sub "thump" on each slide start
for k in range(N):
    i0 = int(k * SLIDE * SR); L = int(0.3 * SR)
    tt = np.arange(L) / SR
    th = np.sin(2 * np.pi * (70 * tt + 40 * (1 - np.exp(-tt * 20)) / 20)) * np.exp(-tt * 14) * 0.45
    audio[i0:i0 + L] += th[:max(0, min(L, n - i0))]
audio *= np.clip((TOTAL - t) / 0.4, 0, 1)
audio = np.tanh(audio * 1.1) * 0.9
st = (np.stack([audio, audio], 1) * 32767).astype(np.int16)
with wave.open(f"{S}/sfx.wav", "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(st.tobytes())

ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", f"{S}/sfx.wav",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)


for fi in range(NF):
    gt = fi / FPS
    si = min(N - 1, int(gt // SLIDE))
    lt = gt - si * SLIDE
    d = data[si]
    frame = d["clean"].astype(np.float32).copy()
    for L in d["layers"]:
        a, s, dy = pop_state(lt, STARTS[L["name"]], L["name"])
        if a > 0:
            draw_layer(frame, L, a, s, dy)
    # grade + vignette
    frame = (frame - 128) * 1.06 + 128
    frame *= vign
    # camera: slow push + punch-in at slide start
    z = 1.0 + 0.035 * (lt / SLIDE) + 0.07 * np.exp(-lt * 5)
    frame = zoom(np.clip(frame, 0, 255), z)
    # white flash around cuts
    fl = 0.0
    for k in range(1, N):
        fl += 0.6 * np.exp(-((gt - k * SLIDE) * 13) ** 2)
    if fl > 0.01:
        frame = frame + (255 - frame) * fl
    # fades
    fade = min(1.0, gt / 0.3, max(0.0, (TOTAL - gt) / 0.45))
    frame = frame * fade
    frame += rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)  # grain
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
print("done", NF, "frames")
