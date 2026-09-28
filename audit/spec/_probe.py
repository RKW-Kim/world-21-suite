#!/usr/bin/env python3
"""Numeric pixel probes for spec/qa screenshots (no VLM, pure measurement)."""
import sys
from PIL import Image

def stats(path, probes):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()
    out = [f"== {path.split('/')[-1]} ({W}x{H}) =="]
    # global mean
    small = im.resize((160, 90))
    data = list(small.getdata())
    mr = sum(p[0] for p in data)/len(data)
    mg = sum(p[1] for p in data)/len(data)
    mb = sum(p[2] for p in data)/len(data)
    out.append(f"global mean RGB: ({mr:.0f},{mg:.0f},{mb:.0f})")
    for name, (x0, y0, x1, y1) in probes.items():
        crop = im.crop((x0, y0, x1, y1))
        d = list(crop.getdata()); n = len(d)
        r = sum(p[0] for p in d)/n; g = sum(p[1] for p in d)/n; b = sum(p[2] for p in d)/n
        yellow = sum(1 for p in d if p[0] > 190 and p[1] > 130 and p[2] < 100)/n
        red = sum(1 for p in d if p[0] > 170 and p[1] < 110 and p[2] < 110)/n
        bright = sum(1 for p in d if p[0] > 180 and p[1] > 180 and p[2] > 180)/n
        green = sum(1 for p in d if p[1] > 130 and p[0] < 110 and p[2] < 150)/n
        blue = sum(1 for p in d if p[2] > 130 and p[0] < 110 and p[1] > 110)/n
        out.append(f"  {name:22s} mean({r:5.1f},{g:5.1f},{b:5.1f}) yellow{yellow*100:5.1f}% red{red*100:5.1f}% green{green*100:5.1f}% blue{blue*100:5.1f}% bright{bright*100:5.1f}%")
    print("\n".join(out))

if __name__ == '__main__':
    which = sys.argv[1]
    if which == 'a':
        probes = {
            'h1-left-ASK/ME zone': (100, 300, 850, 560),
            'h1-ANYTHING zone':    (100, 560, 900, 730),
            'eyebrow chip':        (95, 190, 480, 235),
            'chips+MIC row':       (95, 745, 800, 800),
            'txcard zone':         (1080, 340, 1750, 680),
            'deck ghosts':         (1100, 700, 1740, 760),
            'onair lamp':          (1520, 30, 1880, 80),
            'ticker cap yellow':   (4, 1020, 200, 1076),
            'ticker mid':          (400, 1020, 1400, 1076),
            'ticker cap right':    (1560, 1020, 1916, 1076),
        }
    elif which == 'b':
        probes = {
            'wall center glyphs':  (700, 200, 1250, 560),
            'wall left glyphs':    (150, 150, 620, 500),
            'header chip':         (56, 30, 460, 80),
            'header ep+clock':     (1480, 30, 1870, 80),
            'host disc (yellow)':  (830, 480, 1090, 700),
            'desk slab':           (600, 680, 1320, 715),
            'desk front+plate':    (600, 715, 1320, 950),
            'mic prop':            (660, 540, 790, 705),
            'desklamp red':        (1120, 640, 1260, 700),
            'qcol left':           (40, 200, 276, 880),
            'qcol right':          (1644, 200, 1880, 880),
            'ticker cap left':     (4, 1020, 260, 1076),
            'ticker mid':          (400, 1020, 1400, 1076),
        }
    elif which == 'c':
        probes = {
            'h1 title zone':       (64, 60, 900, 160),
            'h1 board. yellow':    (560, 60, 950, 160),
            'title smile disc':    (860, 60, 960, 170),
            'ep badge':            (1520, 80, 1860, 140),
            'row1 onair badge':    (90, 210, 260, 320),
            'row1 vu zone':        (1400, 210, 1700, 320),
            'row1 timer':          (1720, 230, 1870, 300),
            'row2 next badge':     (90, 350, 260, 455),
            'row2 mini eq':        (1420, 360, 1690, 440),
            'queued rows zone':    (64, 470, 1860, 860),
            'eqstrip':             (64, 880, 1860, 940),
            'chips row':           (64, 950, 800, 1000),
            'ticker cap yellow':   (4, 1020, 200, 1076),
            'ticker mid':          (400, 1020, 1400, 1076),
        }
    else:
        print("unknown scene"); sys.exit(1)
    for p in sys.argv[2:]:
        stats(p, probes)
