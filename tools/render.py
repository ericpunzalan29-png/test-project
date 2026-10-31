"""Render the DK Insurance self-employed reel: three posters with pop-up text, then the
open-enrollment end card, timed 3/3/3/4 s to reuse the first reel's audio track."""
import pickle, subprocess, sys
import numpy as np, cv2

S = "/tmp/claude-0/-home-user-test-project/a8719c71-5fc7-50d0-9200-be02e4987cd5/scratchpad"
AUDIO = sys.argv[1]
OUT = sys.argv[2]
W, H, FPS = 1080, 1350, 30
DUR = [3.0, 3.0, 3.0, 4.0]
DISSOLVE_INTO = {3: 0.4}  # slide index -> crossfade length (end card dissolves in, like reel 1)
data = pickle.load(open(f"{S}/L/layers.pkl", "rb"))
N = len(data)
STARTS_AT = np.concatenate([[0], np.cumsum(DUR)])
TOTAL = float(STARTS_AT[-1])
NF = int(round(TOTAL * FPS))
POP, SETTLE = 0.45, 0.2


def ease_out_back(x, k):
    x = np.clip(x, 0, 1) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def pop_state(lt, start, name):
    x = (lt - start) / POP
    if x <= 0:
        return 0.0, 0.0, 0.0
    a = min(1.0, x / 0.25)
    s = 0.55 + 0.45 * ease_out_back(x, 3.0 if name == "cta" else 2.4)
    dy = 26 * (1 - min(1, x)) ** 3
    return a, s, dy


def paste(frame, rgb, al, x, y):
    h, w = al.shape
    fx0, fy0, fx1, fy1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    a = al[fy0 - y:fy1 - y, fx0 - x:fx1 - x][..., None]
    src = rgb[fy0 - y:fy1 - y, fx0 - x:fx1 - x].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - a) + src * a


def draw_layer(frame, L, a, s, dy):
    x0, y0, x1, y1 = L["box"]
    rgb, al = L["rgb"], L["alpha"].astype(np.float32) / 255.0 * a
    h, w = al.shape
    nw, nh = w, h
    if abs(s - 1) > 1e-3:
        nw, nh = max(1, int(w * s)), max(1, int(h * s))
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
        al = cv2.resize(al, (nw, nh), interpolation=cv2.INTER_LINEAR)
    ax = x0 + 24  # anchor at the text's left edge
    paste(frame, rgb, al, int(round(ax - (ax - x0) * s)), int(round((y0 + y1) / 2 - nh / 2 + dy)))


def zoom(img, z):
    if z <= 1.0005:
        return img
    nw, nh = int(W * z), int(H * z)
    big = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x, y = (nw - W) // 2, (nh - H) // 2
    return big[y:y + H, x:x + W]


Y, X = np.ogrid[:H, :W]
vign = (1 - 0.14 * (((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2))[..., None].astype(np.float32)
rng = np.random.default_rng(7)


def slide_frame(si, lt):
    d = data[si]
    frame = d["clean"].astype(np.float32).copy()
    for i, L in enumerate(d["layers"]):
        st = 0.12 + 0.17 * i
        a, s, dy = pop_state(lt, st, L["name"])
        if a <= 0:
            continue
        w = np.clip((lt - st - POP) / SETTLE, 0, 1)
        if w > 0:  # hand over to the untouched original pixels once the bounce has landed
            x0, y0, x1, y1 = L["box"]
            m = L["settle"].astype(np.float32)[..., None] / 255.0 * w
            frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - m) + d["orig"][y0:y1, x0:x1] * m
        draw_layer(frame, L, a, s, dy)
    frame = (frame - 128) * 1.05 + 128
    frame *= vign
    punch = 0.0 if si in DISSOLVE_INTO else 0.07 * np.exp(-lt * 5)
    return zoom(np.clip(frame, 0, 255), 1.0 + 0.03 * (lt / DUR[si]) + punch)


ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", AUDIO,
                       "-map", "0:v", "-map", "1:a",
                       "-af", f"afade=t=out:st={TOTAL - 0.45}:d=0.45",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL), "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)

for fi in range(NF):
    gt = fi / FPS
    si = int(np.searchsorted(STARTS_AT, gt, side="right") - 1)
    si = min(si, N - 1)
    lt = gt - STARTS_AT[si]
    frame = slide_frame(si, lt)
    if si in DISSOLVE_INTO and lt < DISSOLVE_INTO[si]:
        k = lt / DISSOLVE_INTO[si]
        prev = slide_frame(si - 1, DUR[si - 1] + lt)
        frame = prev * (1 - k) + frame * k
    fl = sum(0.55 * np.exp(-((gt - STARTS_AT[k]) * 13) ** 2) for k in range(1, N) if k not in DISSOLVE_INTO)
    if fl > 0.01:
        frame = frame + (255 - frame) * fl
    frame = frame * min(1.0, gt / 0.3, max(0.0, (TOTAL - gt) / 0.45))
    frame += rng.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())

ff.stdin.close(); ff.wait()
print("done", NF, "frames")
