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
        ("sub", (55, 1080, 680, 1165), "w"),
        ("cta", (55, 1180, 505, 1285), "wg"),
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


data = []
os.makedirs(OUT, exist_ok=True)
for fname, elems in SLIDES:
    bgr = cv2.imread(f"{IMG}/{fname}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    full_mask = np.zeros(rgb.shape[:2], np.uint8)
    layers = []
    for name, (x0, y0, x1, y1), cls in elems:
        m = np.zeros(rgb.shape[:2], bool)
        m[y0:y1, x0:x1] = colour_mask(rgb[y0:y1, x0:x1], cls)
        m8 = m.astype(np.uint8) * 255
        # include anti-aliased edges + drop shadow
        wide = cv2.dilate(m8, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(27, 27)))
        full_mask |= wide
        alpha = cv2.GaussianBlur(cv2.dilate(wide, np.ones((9, 9), np.uint8)), (0, 0), 5)
        P = 24
        x0, y0 = max(0, x0 - P), max(0, y0 - P)
        x1, y1 = min(1080, x1 + P), min(1350, y1 + P)
        layers.append(dict(name=name, box=(x0, y0, x1, y1), alpha=alpha[y0:y1, x0:x1]))
    clean = cv2.inpaint(bgr, full_mask, 9, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(clean, (0, 0), 9)
    w = cv2.GaussianBlur(cv2.dilate(full_mask, np.ones((9, 9), np.uint8)), (0, 0), 6)[..., None] / 255.0
    clean = (clean * (1 - w) + soft * w).astype(np.uint8)
    clean_rgb = cv2.cvtColor(clean, cv2.COLOR_BGR2RGB)
    for L in layers:
        x0, y0, x1, y1 = L["box"]
        L["rgb"] = rgb[y0:y1, x0:x1].copy()
        L["bg"] = clean_rgb[y0:y1, x0:x1].copy()
    cv2.imwrite(f"{OUT}/{fname}_clean.jpg", clean)
    data.append(dict(orig=rgb, clean=clean_rgb, layers=layers))

pickle.dump(data, open(f"{OUT}/layers.pkl", "wb"))
print("ok")
