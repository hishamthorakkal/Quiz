"""Unlabelled teaching charts for hemodynamics questions (titles/labels never state the answer).

    python tools/gen_charts.py <out_dir>

Saturation bars, ductal Doppler traces, parasternal short-axis septal shape and an oxygenation-index trend,
drawn with Pillow only (no matplotlib). Output is deterministic. Generated teaching schematics, not patient data.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

INK, GREY, LIGHT = (30, 41, 59), (100, 116, 139), (226, 232, 240)


def font(size):
    return ImageFont.load_default(size=size)


class Axes:
    def __init__(self, img, box, x0, x1, y0, y1):
        self.d, self.box, self.x0, self.x1, self.y0, self.y1 = ImageDraw.Draw(img), box, x0, x1, y0, y1

    def px(self, x, y):
        l, t, r, b = self.box
        return l + (x - self.x0) / (self.x1 - self.x0) * (r - l), b - (y - self.y0) / (self.y1 - self.y0) * (b - t)

    def frame(self, yticks, ylabel, xticks=(), xlabel='', grid=True):
        l, t, r, b = self.box
        for v in yticks:
            _, y = self.px(self.x0, v)
            if grid:
                self.d.line((l, y, r, y), fill=LIGHT, width=2)
            self.d.text((l - 14, y), f'{v:g}', fill=INK, font=font(24), anchor='rm')
        for v, lab in xticks:
            x, _ = self.px(v, self.y0)
            self.d.line((x, b, x, b + 8), fill=INK, width=2)
            self.d.text((x, b + 14), lab, fill=INK, font=font(24), anchor='ma')
        self.d.line((l, t, l, b), fill=INK, width=3)
        self.d.line((l, b, r, b), fill=INK, width=3)
        if xlabel:
            self.d.text(((l + r) / 2, b + 52), xlabel, fill=INK, font=font(26), anchor='ma')
        if ylabel:
            lab = Image.new('RGBA', (600, 40), (255, 255, 255, 0))
            ImageDraw.Draw(lab).text((300, 20), ylabel, fill=INK, font=font(26), anchor='mm')
            lab = lab.rotate(90, expand=True)
            self.d._image.paste(lab, (int(l - 110), int((t + b) / 2 - 300)), lab)


def diffsat(pre, post):
    img = Image.new('RGB', (1100, 760), 'white')
    ax = Axes(img, (170, 40, 1060, 600), 0, 2, 70, 100)
    ax.frame([70, 75, 80, 85, 90, 95, 100], 'SpO2 (%)', [(0.5, 'Right hand'), (1.5, 'Foot')], 'Pulse-oximeter site')
    for x, v, hatch in ((0.5, pre, 0), (1.5, post, 1)):
        l, t = ax.px(x - 0.28, v)
        r, b = ax.px(x + 0.28, 70)
        ax.d.rectangle((l, t, r, b), fill=(191, 219, 254) if not hatch else (254, 215, 170), outline=INK, width=3)
        ax.d.text(((l + r) / 2, t - 10), f'{v}%', fill=INK, font=font(34), anchor='md')
    return img


def _wave(kind, t):
    """Velocity (m/s) at time t (cardiac cycles). Positive = towards the transducer (here: left-to-right)."""
    ph = t % 1
    if kind == 'restrictive':    # high-velocity continuous flow with a systolic accentuation
        return 2.3 + (0.45 * math.sin(math.pi * ph / 0.5) if ph < 0.5 else 0)
    if kind == 'unrestrictive':  # low-velocity pulsatile flow
        return 0.25 + (0.95 * math.sin(math.pi * ph / 0.5) if ph < 0.5 else 0)
    if kind == 'reversal':       # systemic artery: systolic forward flow, diastolic reversal
        return 1.05 * math.sin(math.pi * ph / 0.5) if ph < 0.5 else -0.22
    raise ValueError(kind)


def _doppler_panel(img, box, kind, title=None, ymax=3.0):
    ax = Axes(img, box, 0, 3, 0, ymax)
    ax.frame([0, 0.5, 1, 1.5, 2, 2.5, 3][:int(ymax / 0.5) + 1], 'Velocity (m/s)', [(v, str(v)) for v in range(4)], 'Cardiac cycles')
    pts = [ax.px(i / 200 * 3, _wave(kind, i / 200 * 3)) for i in range(201)]
    ax.d.polygon(pts + [ax.px(3, 0), ax.px(0, 0)], fill=(203, 213, 225))
    ax.d.line(pts, fill=INK, width=4)
    if title:
        l, t, r, _ = box
        ax.d.text(((l + r) / 2, t - 18), title, fill=INK, font=font(30), anchor='md')


def doppler_single():
    img = Image.new('RGB', (1100, 700), 'white')
    _doppler_panel(img, (170, 40, 1060, 560), 'unrestrictive')
    ImageDraw.Draw(img).text((1060, 690), 'Ductal Doppler; flow above the baseline = left-to-right', fill=GREY, font=font(22), anchor='rd')
    return img


def doppler_ab():
    img = Image.new('RGB', (1800, 720), 'white')
    _doppler_panel(img, (160, 80, 860, 560), 'restrictive', 'Pattern A')
    _doppler_panel(img, (1060, 80, 1760, 560), 'unrestrictive', 'Pattern B')
    ImageDraw.Draw(img).text((1760, 710), 'Ductal Doppler; flow above the baseline = left-to-right', fill=GREY, font=font(22), anchor='rd')
    return img


def _short_axis(d, cx, cy, flattened):
    """Parasternal short axis: RV crescent wrapping a circular LV; septal flattening turns the LV into a 'D'."""
    rv = (cx - 230, cy - 170, cx + 60, cy + 170) if flattened else (cx - 250, cy - 115, cx - 40, cy + 115)
    d.ellipse(rv, fill=(71, 85, 105))                                    # RV cavity
    d.ellipse((rv[0] + 20, rv[1] + 20, rv[2] - 20, rv[3] - 20), fill=(15, 23, 42))
    r = 120
    if flattened:
        pts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [i / 60 * 2 * math.pi for i in range(61)]]
        pts = [(max(x, cx - 55), y) for x, y in pts]                    # septum pushed flat towards the LV
        d.polygon(pts, fill=(148, 163, 184))
        inner = [(cx + (r - 26) * math.cos(a), cy + (r - 26) * math.sin(a)) for a in [i / 60 * 2 * math.pi for i in range(61)]]
        d.polygon([(max(x, cx - 30), y) for x, y in inner], fill=(15, 23, 42))
    else:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(148, 163, 184))  # LV myocardium
        d.ellipse((cx - r + 26, cy - r + 26, cx + r - 26, cy + r - 26), fill=(15, 23, 42))
    d.text((rv[0] + (70 if flattened else 62), cy), 'RV', fill='white', font=font(30), anchor='mm')
    d.text((cx + 10, cy), 'LV', fill='white', font=font(30), anchor='mm')


def septum():
    img = Image.new('RGB', (1400, 620), 'white')
    d = ImageDraw.Draw(img)
    for i, (lab, flat) in enumerate((('Reference: normal', False), ('This infant (systole)', True))):
        cx = 420 + i * 640
        d.rounded_rectangle((cx - 330, 60, cx + 300, 560), radius=24, fill=(30, 41, 59))
        _short_axis(d, cx + 40, 310, flat)
        d.text((cx - 15, 40), lab, fill=INK, font=font(30), anchor='md')
    d.text((1380, 610), 'Parasternal short-axis view (schematic)', fill=GREY, font=font(22), anchor='rd')
    return img


def oi_trend():
    img = Image.new('RGB', (1100, 720), 'white')
    ax = Axes(img, (170, 40, 1060, 580), -0.5, 5, 10, 45)
    ax.frame([10, 15, 20, 25, 30, 35, 40, 45], 'Oxygenation index', [(v, str(v)) for v in range(6)], 'Time (h)')
    pts = [ax.px(t, v) for t, v in ((0, 18), (2, 27), (4, 39))]
    ax.d.line(pts, fill=INK, width=5)
    for (x, y), v in zip(pts, (18, 27, 39)):
        ax.d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=INK)
        ax.d.text((x, y - 20), str(v), fill=INK, font=font(30), anchor='md')
    return img


GENERATORS = {
    'gen_diffsat_97_84': lambda: diffsat(97, 84), 'gen_diffsat_96_84': lambda: diffsat(96, 84),
    'gen_doppler_low_pulsatile': doppler_single, 'gen_doppler_ab': doppler_ab,
    'gen_septum': septum, 'gen_oi_trend': oi_trend,
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    for name, fn in GENERATORS.items():
        fn().save(f'{out}/{name}.png', optimize=True)
        print('wrote', f'{out}/{name}.png')
