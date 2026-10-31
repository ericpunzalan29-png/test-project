"""Rebuild the first reel's 9:16 end card as a 1080x1350 slide and append it to layers.pkl."""
import cv2, numpy as np, pickle

S = "/tmp/claude-0/-home-user-test-project/a8719c71-5fc7-50d0-9200-be02e4987cd5/scratchpad"
W, H = 1080, 1350
fr = cv2.cvtColor(cv2.imread(f"{S}/L/endcard.png"), cv2.COLOR_BGR2RGB)  # 1080x1920

text = (fr.max(2) > 150).astype(np.uint8) * 255
clean = cv2.inpaint(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), cv2.dilate(text, np.ones((15, 15), np.uint8)), 15, cv2.INPAINT_TELEA)
clean = cv2.GaussianBlur(clean, (0, 0), 6)
bg = cv2.cvtColor(cv2.resize(clean, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)

# (name, src box in 1920 frame, dy shift into 1350 slide, pops?)
BLOCKS = [
    ("header", (0, 50, 1080, 140), -15, False),
    ("eyebrow", (60, 555, 560, 605), -330, True),
    ("h1", (60, 620, 700, 780), -330, True),
    ("h2", (60, 780, 600, 920), -330, True),
    ("g1", (60, 950, 760, 1050), -330, True),
    ("g2", (60, 1050, 900, 1160), -330, True),
    ("sub", (60, 1170, 520, 1310), -330, True),
    ("cta_l", (60, 1580, 700, 1660), -475, True),
    ("cta", (60, 1665, 960, 1790), -475, True),
]

orig = bg.astype(np.float32).copy()
cleanplate = bg.copy()
layers = []
for name, (x0, y0, x1, y1), dy, pops in BLOCKS:
    a = cv2.GaussianBlur(cv2.dilate(text[y0:y1, x0:x1], np.ones((3, 3), np.uint8)), (0, 0), 0.8).astype(np.float32) / 255
    rgb = fr[y0:y1, x0:x1]
    Y0, Y1 = y0 + dy, y1 + dy
    region = orig[Y0:Y1, x0:x1]
    orig[Y0:Y1, x0:x1] = region * (1 - a[..., None]) + rgb * a[..., None]
    if not pops:
        cleanplate[Y0:Y1, x0:x1] = orig[Y0:Y1, x0:x1].astype(np.uint8)
        continue
    P = 24
    bx0, by0, bx1, by1 = max(0, x0 - P), max(0, Y0 - P), min(W, x1 + P), min(H, Y1 + P)
    al = np.zeros((by1 - by0, bx1 - bx0), np.float32)
    al[Y0 - by0:Y1 - by0, x0 - bx0:x1 - bx0] = a
    layers.append(dict(name=name, box=(bx0, by0, bx1, by1), alpha=(al * 255).astype(np.uint8),
                       settle=(al * 255).astype(np.uint8)))
orig = orig.clip(0, 255).astype(np.uint8)
for L in layers:
    x0, y0, x1, y1 = L["box"]
    L["rgb"] = orig[y0:y1, x0:x1].copy()

data = pickle.load(open(f"{S}/L/layers3.pkl", "rb"))[:3]
data.append(dict(orig=orig, clean=cleanplate, layers=layers))
pickle.dump(data, open(f"{S}/L/layers.pkl", "wb"))
cv2.imwrite(f"{S}/L/endcard_45.jpg", cv2.cvtColor(orig, cv2.COLOR_RGB2BGR))
print("ok", [L["name"] for L in layers])
