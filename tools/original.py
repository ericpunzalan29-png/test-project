"""Original 9:16 DK Insurance reel: kinetic typography over the poster photos.

Timeline (13 s, matches reel 1 audio):
  0.0-1.6  navy intro  "SELF-EMPLOYED?" / "You're the boss."
  1.6-3.6  yard photo  "You run the crew."
  3.6-5.6  farm photo  "You run the farm."
  5.6-7.6  roof photo  "You run the roof."
  7.6-9.2  3-way split "Who's got you?"
  9.2-13   end card    compare plans / open enrollment dates / phone
"""
import pickle, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

S = "/tmp/claude-0/-home-user-test-project/a8719c71-5fc7-50d0-9200-be02e4987cd5/scratchpad"
AUDIO, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, TOTAL = 1080, 1920, 30, 13.0
F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
WHITE, GOLD, NAVY, MUTED = (255, 255, 255), (236, 205, 128), (14, 27, 52), (200, 210, 230)

# ---------- assets ----------
data = pickle.load(open(f"{S}/L/layers.pkl", "rb"))


def strip_header(img):
    top = img[:150]
    r, g, b = [top[..., i].astype(int) for i in range(3)]
    m = (top.max(2) > 190) | ((b > 150) & (b - r > 60)) | ((r > 180) & (r - b > 50))
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[:150] = cv2.dilate(m.astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
    bgr = cv2.inpaint(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), mask, 12, cv2.INPAINT_TELEA)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def fill916(img, cx):
    img = strip_header(img)
    s = H / img.shape[0]
    big = cv2.resize(img, (int(img.shape[1] * s), H), interpolation=cv2.INTER_CUBIC)
    x0 = int(np.clip(cx * s - W / 2, 0, big.shape[1] - W))
    return big[:, x0:x0 + W].astype(np.float32)


PHOTOS = [fill916(data[0]["clean"], 650), fill916(data[1]["clean"], 700), fill916(data[2]["clean"], 520)]
# remove the poster's own header strip (logo/label) – we draw our own

end = cv2.cvtColor(cv2.imread(f"{S}/L/endcard.png"), cv2.COLOR_BGR2RGB)
txt = (end.max(2) > 150).astype(np.uint8) * 255
plate = cv2.inpaint(cv2.cvtColor(end, cv2.COLOR_RGB2BGR), cv2.dilate(txt, np.ones((15, 15), np.uint8)), 15, cv2.INPAINT_TELEA)
NAVY_BG = cv2.cvtColor(cv2.GaussianBlur(plate, (0, 0), 8), cv2.COLOR_BGR2RGB).astype(np.float32)
# logo (icon + wordmark) cut from the reel-1 end card
lx0, ly0, lx1, ly1 = 60, 70, 430, 125
la = cv2.GaussianBlur(cv2.dilate(txt[ly0:ly1, lx0:lx1], np.ones((3, 3), np.uint8)), (0, 0), 0.7)
LOGO = np.dstack([end[ly0:ly1, lx0:lx1], la])


def sprite(text, size, weight="ExtraBold", color=WHITE, track=0, shadow=True):
    font = ImageFont.truetype(F.format(weight), size)
    chars = list(text)
    widths = [font.getlength(c) + track for c in chars]
    asc, desc = font.getmetrics()
    w, h = int(sum(widths) + 40), asc + desc + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 20
    for c, cw in zip(chars, widths):
        d.text((x, 20), c, font=font, fill=color + (255,))
        x += cw
    a = np.array(im).astype(np.float32)
    if shadow:
        sh = cv2.GaussianBlur(a[..., 3], (0, 0), size / 14) * 0.55
        sh = np.roll(sh, int(size / 22), 0)
        out = np.zeros_like(a)
        al = a[..., 3:] / 255
        out[..., :3] = a[..., :3] * al
        out[..., 3] = np.maximum(a[..., 3], sh)
        out[..., :3] = np.where(out[..., 3:] > 0, out[..., :3] / np.maximum(out[..., 3:] / 255, 1e-3), 0)
        a = out
    return a


def blit(frame, spr, x, y, alpha=1.0, scale=1.0, anchor="lc"):
    if alpha <= 0.003:
        return
    s = spr
    if abs(scale - 1) > 1e-3:
        s = cv2.resize(spr, (max(1, int(spr.shape[1] * scale)), max(1, int(spr.shape[0] * scale))), interpolation=cv2.INTER_LINEAR)
    h, w = s.shape[:2]
    if anchor == "lc":
        x, y = x - 20 * scale, y - h / 2
    elif anchor == "c":
        x, y = x - w / 2, y - h / 2
    x, y = int(round(x)), int(round(y))
    fx0, fy0, fx1, fy1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    sub = s[fy0 - y:fy1 - y, fx0 - x:fx1 - x]
    a = sub[..., 3:4] / 255.0 * alpha
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - a) + sub[..., :3] * a


def back(x, k=2.2):
    x = np.clip(x, 0, 1) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def out3(x):
    return 1 - (1 - np.clip(x, 0, 1)) ** 3


def pop(frame, spr, x, y, t0, t, dur=0.42, anchor="lc", big=False, t_out=None):
    p = (t - t0) / dur
    if p <= 0:
        return
    a = min(1, p / 0.3)
    if t_out is not None and t > t_out:
        a *= max(0, 1 - (t - t_out) / 0.18)
    s = 0.5 + 0.5 * back(p, 2.8 if big else 2.2)
    blit(frame, spr, x, y + 30 * (1 - out3(p)), a, s, anchor)


def rect(frame, x0, y0, x1, y1, color, a=1.0):
    x0, x1 = int(max(0, x0)), int(min(W, x1))
    y0, y1 = int(max(0, y0)), int(min(H, y1))
    if x1 > x0 and y1 > y0:
        frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + np.array(color, np.float32) * a


def kb(img, t, dur, z0=1.0, z1=1.08, dx=0):
    z = z0 + (z1 - z0) * (t / dur)
    M = cv2.getRotationMatrix2D((W / 2 + dx * t / dur, H / 2), 0, z)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


Yg = np.linspace(0, 1, H)[:, None, None].astype(np.float32)
BOTTOM_SHADE = np.clip((Yg - 0.5) / 0.5, 0, 1) ** 1.2 * 0.9
TOP_SHADE = np.clip((0.14 - Yg) / 0.14, 0, 1) * 0.55
Y, X = np.ogrid[:H, :W]
VIGN = (1 - 0.16 * (((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2))[..., None].astype(np.float32)


def shade(img):
    navy = np.array(NAVY, np.float32)
    img = img * (1 - BOTTOM_SHADE) + navy * BOTTOM_SHADE
    return img * (1 - TOP_SHADE) + navy * TOP_SHADE


# ---------- text sprites ----------
T = dict(
    eyebrow=sprite("SELF-EMPLOYED?", 44, "Bold", GOLD, track=9, shadow=False),
    boss1=sprite("You're", 150, "Black"),
    boss2=sprite("the boss.", 150, "Black", GOLD),
    run=sprite("You run", 120, "ExtraBold"),
    crew=sprite("the crew.", 165, "Black", GOLD),
    farm=sprite("the farm.", 165, "Black", GOLD),
    roof=sprite("the roof.", 165, "Black", GOLD),
    tag1=sprite("LANDSCAPING", 34, "Bold", WHITE, 7, False),
    tag2=sprite("FARMING", 34, "Bold", WHITE, 7, False),
    tag3=sprite("ROOFING", 34, "Bold", WHITE, 7, False),
    who1=sprite("But who's", 140, "Black"),
    who2=sprite("got you?", 140, "Black", GOLD),
    c1=sprite("We'll compare health plans", 62, "SemiBold"),
    c2=sprite("built for people who work", 62, "SemiBold"),
    c3=sprite("for themselves.", 62, "SemiBold"),
    oe=sprite("OPEN ENROLLMENT", 40, "Bold", GOLD, 8, False),
    d1=sprite("Nov 1 to Jan 15.", 112, "Black"),
    d2=sprite("Enroll by Dec 15", 66, "Bold", GOLD),
    d3=sprite("for Jan 1 coverage.", 66, "Bold", GOLD),
    free=sprite("Free plan review.", 50, "Regular", MUTED, shadow=False),
    msg=sprite("Send us a message or call us", 46, "Medium", WHITE, shadow=False),
    phone=sprite("712-639-6347", 122, "ExtraBold", GOLD),
)
LOGO_SPR = LOGO.astype(np.float32)

CUTS = [1.6, 3.6, 5.6, 7.6, 9.2]


def photo_scene(frame_photo, t, dur, tagspr, word, i):
    img = shade(kb(frame_photo, t, dur, 1.12, 1.02 if i % 2 else 1.14, dx=(-40 if i % 2 else 40)))
    # tag chip
    p = out3((t - 0.1) / 0.35)
    if p > 0:
        tw = tagspr.shape[1] - 10
        rect(img, 70, 1402, 70 + tw * p, 1458, GOLD, 0.95)
        blit(img, tagspr * np.array([0, 0, 0, 1], np.float32) + np.array([14, 27, 52, 0], np.float32), 85, 1430, min(1, p * 2))
    pop(img, T["run"], 75, 1550, 0.22, t)
    pop(img, T[word], 75, 1705, 0.42, t, big=True)
    # gold underline wipe
    u = out3((t - 0.75) / 0.4)
    if u > 0:
        rect(img, 80, 1805, 80 + 260 * u, 1815, GOLD)
    return img


def split_scene(t):
    img = NAVY_BG.copy()
    cw = W // 3
    for k, ph in enumerate(PHOTOS):
        p = out3((t - 0.08 * k) / 0.45)
        if p <= 0:
            continue
        col = cv2.resize(ph, None, fx=1.0, fy=1.0)[:, (W - cw) // 2:(W - cw) // 2 + cw]
        col = shade(np.pad(col, ((0, 0), (0, W - cw), (0, 0))))[:, :cw]
        off = int((1 - p) * (H if k % 2 == 0 else -H))
        y0, y1 = max(0, off), min(H, H + off)
        img[y0:y1, k * cw:(k + 1) * cw] = col[y0 - off:y1 - off]
    rect(img, 0, 0, W, H, NAVY, 0.55)
    pop(img, T["who1"], W / 2, 820, 0.35, t, anchor="c")
    pop(img, T["who2"], W / 2, 980, 0.55, t, anchor="c", big=True)
    return img


def end_scene(t):
    img = NAVY_BG.copy()
    blit(img, LOGO_SPR, 75, 120, min(1, t / 0.3), 1.25)
    seq = [("c1", 330), ("c2", 410), ("c3", 490)]
    for i, (k, y) in enumerate(seq):
        pop(img, T[k], 75, y, 0.15 + 0.12 * i, t)
    u = out3((t - 0.6) / 0.35)
    if u > 0:
        rect(img, 80, 590, 80 + 110 * u, 600, GOLD)
    pop(img, T["oe"], 75, 700, 0.75, t)
    pop(img, T["d1"], 75, 810, 0.9, t, big=True)
    pop(img, T["d2"], 75, 945, 1.1, t)
    pop(img, T["d3"], 75, 1025, 1.22, t)
    pop(img, T["free"], 75, 1130, 1.4, t)
    pop(img, T["msg"], 75, 1500, 1.6, t)
    # phone: pop + gentle pulse
    pulse = 1 + 0.05 * np.exp(-((t - 2.9) * 6) ** 2)
    p = (t - 1.75) / 0.45
    if p > 0:
        blit(img, T["phone"], 75, 1610, min(1, p / 0.3), (0.5 + 0.5 * back(p, 3.0)) * pulse)
    return img


def intro(t):
    img = NAVY_BG.copy()
    blit(img, LOGO_SPR, 75, 120, min(1, t / 0.3), 1.25)
    pop(img, T["eyebrow"], 75, 860, 0.15, t, t_out=1.45)
    pop(img, T["boss1"], 75, 980, 0.35, t, big=True, t_out=1.45)
    pop(img, T["boss2"], 75, 1140, 0.6, t, big=True, t_out=1.45)
    return img


def render(gt):
    if gt < CUTS[0]:
        img = intro(gt)
    elif gt < CUTS[3]:
        i = int(np.searchsorted(CUTS, gt, side="right")) - 1
        img = photo_scene(PHOTOS[i], gt - CUTS[i], CUTS[i + 1] - CUTS[i], T[f"tag{i + 1}"], ["crew", "farm", "roof"][i], i)
        blit(img, LOGO_SPR, 75, 120, 1.0, 1.25)
    elif gt < CUTS[4]:
        img = split_scene(gt - CUTS[3])
        blit(img, LOGO_SPR, 75, 120, 1.0, 1.25)
    else:
        img = end_scene(gt - CUTS[4])
    img *= VIGN
    # punch zoom + flash at every cut
    z, fl = 1.0, 0.0
    for c in CUTS:
        dt = gt - c
        if 0 <= dt < 0.5:
            z += 0.06 * np.exp(-dt * 7)
        fl += 0.5 * np.exp(-(dt * 14) ** 2)
    if z > 1.001:
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    img = img + (255 - img) * min(fl, 0.6)
    img *= min(1.0, gt / 0.25, max(0.0, (TOTAL - gt) / 0.45))
    return img


ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-i", AUDIO, "-map", "0:v", "-map", "1:a",
                       "-af", f"afade=t=out:st={TOTAL - 0.45}:d=0.45", "-c:v", "libx264", "-preset", "slow",
                       "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL),
                       "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
rng = np.random.default_rng(3)
for fi in range(int(TOTAL * FPS)):
    img = render(fi / FPS)
    img += rng.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    ff.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
print("done")
