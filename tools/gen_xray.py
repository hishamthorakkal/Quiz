"""Radiograph-style teaching schematics for neonatal abdominal findings (no labels that give the answer away).

    python tools/gen_xray.py <out_dir>

Draws a supine neonatal abdominal film: soft-tissue body, spine, curved lower ribs, iliac wings, liver shadow and a
gastric bubble, with gas rendered dark (radiolucent) as on a real film. Patient's right is on the viewer's left.
Output is deterministic. These are generated teaching schematics, not patient images. Needs Pillow only.
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1200, 960
CX = W / 2


def base(seed):
    rng = random.Random(seed)
    img = Image.new('L', (W, H), 10)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((170, -40, W - 170, H + 60), radius=300, fill=112)               # trunk soft tissue
    img = img.filter(ImageFilter.GaussianBlur(22))
    d = ImageDraw.Draw(img)
    d.ellipse((190, 40, 690, 520), fill=142)                                             # liver (patient's right)
    d.rectangle((180, 0, 700, 140), fill=150)                                            # lower chest / diaphragm level
    d.ellipse((CX + 110, 230, CX + 300, 340), fill=60)                                   # gastric bubble
    img = img.filter(ImageFilter.GaussianBlur(14))
    d = ImageDraw.Draw(img)
    for i in range(5):                                                                   # lower ribs: curve down and out
        y0 = 30 + i * 52
        for side in (-1, 1):
            pts = [(CX + side * (44 + t), y0 - 0.20 * t + 0.0021 * t * t) for t in range(0, 345, 6)]
            pts = [p for p in pts if 40 < p[1] < 470]
            if len(pts) > 2:
                d.line(pts, fill=176, width=12, joint='curve')
    for i in range(14):                                                                  # vertebrae with pedicles
        y = -10 + i * 64
        d.rounded_rectangle((CX - 30, y, CX + 30, y + 52), radius=12, fill=196)
        for side in (-1, 1):
            d.ellipse((CX + side * 30 - 9, y + 12, CX + side * 30 + 9, y + 34), fill=206)
    for side in (-1, 1):                                                                 # iliac wings + sacrum
        cx = CX + side * 205
        d.ellipse((cx - 125, 840, cx + 125, 1000), fill=158)
    d.ellipse((CX - 52, 840, CX + 52, 1000), fill=170)
    img = img.filter(ImageFilter.GaussianBlur(4))
    return img, rng


def loop_path(cx, cy, length, angle, wiggle):
    pts = []
    for i in range(26):
        t = i / 25
        x = cx + (t - .5) * length * math.cos(angle) - math.sin(angle) * wiggle * math.sin(t * math.pi * 1.6)
        y = cy + (t - .5) * length * math.sin(angle) + math.cos(angle) * wiggle * math.sin(t * math.pi * 1.6)
        pts.append((x, y))
    return pts


def _sausage(size, pts, width):
    m = Image.new('L', size, 0)
    dm = ImageDraw.Draw(m)
    dm.line(pts, fill=255, width=int(width), joint='curve')
    for p in (pts[0], pts[-1]):
        r = width / 2
        dm.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    return m


def draw_loop(img, pts, width, wall=6, gas=34):
    """Gas-filled bowel loop: dark lumen with a thin soft-tissue wall."""
    img.paste(Image.new('L', img.size, 128), (0, 0), _sausage(img.size, pts, width + 2 * wall).filter(ImageFilter.GaussianBlur(2)))
    img.paste(Image.new('L', img.size, gas), (0, 0), _sausage(img.size, pts, width).filter(ImageFilter.GaussianBlur(3)))


LOOPS = [  # (cx, cy, length, angle, wiggle, width) — central/lower abdomen, below the liver edge
    (420, 560, 230, 0.35, 22, 74), (700, 520, 250, -0.25, 24, 78), (560, 660, 270, 0.08, 20, 72),
    (820, 670, 200, 0.6, 18, 70), (370, 740, 190, -0.45, 16, 66), (650, 805, 240, 0.12, 18, 64),
    (820, 410, 170, -0.1, 12, 60),
]


def bowel(img, loops=LOOPS, dilate=None):
    for i, (cx, cy, L, a, wg, wd) in enumerate(loops):
        draw_loop(img, loop_path(cx, cy, L, a, wg), int(wd * 1.8) if dilate == i else wd)
    return img


def finish(img, seed):
    noise = Image.effect_noise((W, H), 20).filter(ImageFilter.GaussianBlur(0.8))
    img = ImageChops.add(img, noise, scale=1.0, offset=-128).filter(ImageFilter.GaussianBlur(1.1))
    return img.convert('RGB')


def arrow(img, tip, frm, col=(255, 214, 10)):
    d = ImageDraw.Draw(img)
    d.line((frm, tip), fill=col, width=8)
    ang = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
    for s in (-0.5, 0.5):
        d.line((tip, (tip[0] - 38 * math.cos(ang + s), tip[1] - 38 * math.sin(ang + s))), fill=col, width=8)


def pneumatosis(seed=1):
    img, rng = base(seed)
    bowel(img)
    d = ImageDraw.Draw(img)
    for idx in (0, 2, 3):                    # bubbly + linear intramural gas tracking along the wall
        cx, cy, L, a, wg, wd = LOOPS[idx]
        pts = loop_path(cx, cy, L, a, wg)
        for j in range(1, len(pts) - 1):
            (x0, y0), (x1, y1) = pts[j - 1], pts[j + 1]
            nx, ny = -(y1 - y0), x1 - x0
            n = math.hypot(nx, ny) or 1
            for side in (-1, 1):
                px, py = pts[j][0] + nx / n * (wd / 2 + 3) * side, pts[j][1] + ny / n * (wd / 2 + 3) * side
                if rng.random() < .6:
                    r = rng.uniform(3, 6.5)
                    d.ellipse((px - r, py - r, px + r, py + r), fill=26)
                else:
                    d.line(((px - (x1 - x0) * .3, py - (y1 - y0) * .3), (px + (x1 - x0) * .3, py + (y1 - y0) * .3)), fill=30, width=3)
    img = finish(img, seed)
    arrow(img, (470, 615), (560, 760))
    arrow(img, (885, 720), (1000, 830))
    return img


def portal_gas(seed=2):
    img, rng = base(seed)
    bowel(img)
    d = ImageDraw.Draw(img)

    def branch(x, y, ang, length, w, depth):  # porta hepatis -> liver periphery
        if depth == 0 or length < 16:
            return
        x2, y2 = x + length * math.cos(ang), y + length * math.sin(ang)
        d.line((x, y, x2, y2), fill=58, width=max(2, int(w)))
        for da in (-0.45, 0.4):
            branch(x2, y2, ang + da + rng.uniform(-.12, .12), length * .72, w * .68, depth - 1)
    for a in (-2.55, -2.05, -1.6, 3.05, 2.6):
        branch(500, 360, a, 78, 6, 5)
    img = finish(img, seed)
    arrow(img, (330, 245), (215, 130))
    return img


def free_air(seed=3):
    """Supine pneumoperitoneum without pneumatosis/portal gas: football sign, falciform ligament, Rigler sign."""
    img, rng = base(seed)
    bowel(img)
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).ellipse((300, 230, 900, 780), fill=170)
    img.paste(Image.new('L', img.size, 46), (0, 0), m.filter(ImageFilter.GaussianBlur(45)))
    d = ImageDraw.Draw(img)
    d.line(((650, 240), (610, 540)), fill=150, width=6)            # falciform ligament
    for cx, cy, L, a, wg, wd in LOOPS[:4]:                          # both sides of the bowel wall outlined
        pts = loop_path(cx, cy, L, a, wg)
        m2 = _sausage(img.size, pts, wd + 12)
        edge = ImageChops.subtract(m2, _sausage(img.size, pts, wd))
        img.paste(Image.new('L', img.size, 150), (0, 0), edge)
    return finish(img, seed)


def fixed_loop(seed=4):
    """Two serial films: other loops move, one dilated loop stays in the same place."""
    panels = []
    for k in (0, 1):
        loops = [(cx + (35 if (i + k) % 2 else -30) * (k if i != 2 else 0), cy + (22 * k if i != 2 else 0), L, a + (0.35 * k if i != 2 else 0), wg, wd)
                 for i, (cx, cy, L, a, wg, wd) in enumerate(LOOPS)]
        img, _ = base(seed + k)
        bowel(img, loops, dilate=2)
        panels.append(finish(img, seed + k).resize((W // 2, H // 2)))
    out = Image.new('RGB', (W + 20, H // 2 + 54), (255, 255, 255))
    d = ImageDraw.Draw(out)
    for i, p in enumerate(panels):
        out.paste(p, (i * (W // 2 + 20), 54))
        d.text((i * (W // 2 + 20) + 8, 12), ['Film 1 (0 h)', 'Film 2 (6 h later)'][i], fill=(20, 20, 20), font_size=30)
    return out


GENERATORS = {'gen_pneumatosis': pneumatosis, 'gen_portal_gas': portal_gas, 'gen_free_air': free_air, 'gen_fixed_loop': fixed_loop}


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in GENERATORS.items():
        fn().save(f'{out}/{name}.png', optimize=True)
        print('wrote', f'{out}/{name}.png')
