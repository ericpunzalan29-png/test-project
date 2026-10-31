"""Split each poster into a clean background (text inpainted out) and text layers."""
import cv2, numpy as np, pickle, sys, os

IMG = "/tmp/claude-0/-home-user-test-project/a8719c71-5fc7-50d0-9200-be02e4987cd5/images"
OUT = sys.argv[1]

# (name, box x0,y0,x1,y1, colour classes)
SLIDES = [
    ("2.jpg", [
        ("eyebrow", (55, 175, 380, 215), "w"),
        ("h1", (55, 230, 800, 375), "w"),
        ("h2", (55, 380, 790, 540), "g"),
        ("sub", (55, 545, 490, 715), "wg"),
        ("cta", (55, 1155, 545, 1280), "wg"),
    ]),
    ("3.jpg", [
        ("eyebrow", (55, 175, 380, 215), "w"),
        ("h1", (55, 230, 870, 330), "w"),
        ("h2", (55, 330, 890, 440), "g"),
        ("sub", (55, 450, 690, 590), "wg"),
        ("cta", (55, 1155, 545, 1280), "wg"),
    ]),
    ("4.jpg", [
        ("eyebrow", (55, 135, 395, 170), "w"),
        ("h1", (55, 175, 600, 270), "w"),
        ("h2", (55, 270, 650, 360), "w"),
        ("h3", (55, 360, 795, 455), "d"),
        ("sub", (55, 1080, 680, 1165), "w", 9),
        ("cta", (55, 1180, 505, 1285), "wg", 9),
    ]),
]


def colour_mask(rgb, classes):
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    m = np.zeros(r.shape, bool)
    if "w" in classes:
        m |= (r > 205) & (g > 205) & (b > 205)
    if "g" in classes:  # brand gold, excludes neon-yellow vest (g > r)
        m |= (r > 190) & (g > 160) & (b < 175) & (r - b > 55) & (r >= g)
    if "d" in classes:  # dark navy headline
        m |= (r < 60) & (g < 60) & (b < 90)
    return m


ONLY = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
data = pickle.load(open(f"{OUT}/layers3.pkl", "rb")) if ONLY else []
os.makedirs(OUT, exist_ok=True)
for si, (fname, elems) in enumerate(SLIDES):
    if ONLY and si not in ONLY:
        continue
    bgr = cv2.imread(f"{IMG}/{fname}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    full_mask = np.zeros(rgb.shape[:2], np.uint8)
    layers = []
    for e in elems:
        name, (x0, y0, x1, y1), cls = e[:3]; dil = e[3] if len(e) > 3 else 25
        m = np.zeros(rgb.shape[:2], bool)
        m[y0:y1, x0:x1] = colour_mask(rgb[y0:y1, x0:x1], cls)
        m8 = m.astype(np.uint8) * 255
        wide = cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dil, dil)))
        full_mask |= wide
        tight = cv2.GaussianBlur(cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))), (0, 0), 1.2)
        settle = cv2.GaussianBlur(cv2.dilate(wide, np.ones((7, 7), np.uint8)), (0, 0), 4)
        P = 24
        x0, y0 = max(0, x0 - P), max(0, y0 - P)
        x1, y1 = min(1080, x1 + P), min(1350, y1 + P)
        layers.append(dict(name=name, box=(x0, y0, x1, y1), alpha=tight[y0:y1, x0:x1], settle=settle[y0:y1, x0:x1]))
    # texture-aware fill (frequency selective reconstruction), per masked band
    clean = bgr.copy()
    ys, xs = np.where(full_mask > 0)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(full_mask, np.ones((61, 61), np.uint8)))
    for k in range(1, n):
        x, y, w, h = stats[k, :4]
        X0, Y0, X1, Y1 = max(0, x - 40), max(0, y - 40), min(1080, x + w + 40), min(1350, y + h + 40)
        src = clean[Y0:Y1, X0:X1].copy()
        msk = (full_mask[Y0:Y1, X0:X1] == 0).astype(np.uint8)  # 1 = known
        dst = np.zeros_like(src)
        cv2.xphoto.inpaint(src, msk, dst, cv2.xphoto.INPAINT_FSR_BEST)
        clean[Y0:Y1, X0:X1] = np.where(msk[..., None] == 0, dst, src)
    clean_rgb = cv2.cvtColor(clean, cv2.COLOR_BGR2RGB)
    for L in layers:
        x0, y0, x1, y1 = L["box"]
        L["rgb"] = rgb[y0:y1, x0:x1].copy()
    cv2.imwrite(f"{OUT}/{fname}_clean.jpg", clean)
    entry = dict(orig=rgb, clean=clean_rgb, layers=layers)
    if ONLY: data[si] = entry
    else: data.append(entry)

pickle.dump(data, open(f"{OUT}/layers3.pkl", "wb"))
print("ok")
