#!/usr/bin/env python3
"""Numeric pixel probes for TECH scene screenshots (no VLM, pure measurement)."""
import sys
from PIL import Image, ImageChops

def region(im, x0, y0, x1, y1):
    return im.crop((x0, y0, x1, y1))

def measures(crop):
    d = list(crop.getdata()); n = max(1, len(d))
    r = sum(p[0] for p in d)/n; g = sum(p[1] for p in d)/n; b = sum(p[2] for p in d)/n
    yellow = sum(1 for p in d if p[0] > 190 and p[1] > 130 and p[2] < 110)/n
    red    = sum(1 for p in d if p[0] > 170 and p[1] < 110 and p[2] < 110)/n
    green  = sum(1 for p in d if p[1] > 130 and p[0] < 120 and p[2] < 160)/n
    bright = sum(1 for p in d if p[0] > 180 and p[1] > 180 and p[2] > 180)/n
    lit    = sum(1 for p in d if p[0]+p[1]+p[2] > 120)/n
    return r, g, b, yellow, red, green, bright, lit

def show(path, probes, extra=None):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    out = [f"== {path.split('/')[-1]} ({W}x{H}) =="]
    small = im.resize((160, 90)); dd = list(small.getdata())
    mr = sum(p[0] for p in dd)/len(dd); mg = sum(p[1] for p in dd)/len(dd); mb = sum(p[2] for p in dd)/len(dd)
    out.append(f"global mean RGB ({mr:.0f},{mg:.0f},{mb:.0f})")
    for name, box in probes.items():
        r, g, b, y, rd, gr, br, lt = measures(region(im, *box))
        out.append(f"  {name:24s} mean({r:5.1f},{g:5.1f},{b:5.1f}) Y{y*100:5.1f}% R{rd*100:5.1f}% G{gr*100:5.1f}% bright{br*100:5.1f}% lit{lt*100:5.1f}%")
    if extra:
        for name, box in extra.items():
            r, g, b, y, rd, gr, br, lt = measures(region(im, *box))
            out.append(f"  {name:24s} mean({r:5.1f},{g:5.1f},{b:5.1f}) Y{y*100:5.1f}% R{rd*100:5.1f}% G{gr*100:5.1f}% bright{br*100:5.1f}% lit{lt*100:5.1f}%")
    print("\n".join(out))

def diff(p1, p2, box):
    a = Image.open(p1).convert('RGB').crop(box)
    b = Image.open(p2).convert('RGB').crop(box)
    d = ImageChops.difference(a, b)
    dd = list(d.getdata()); n = max(1, len(dd))
    m = sum((p[0]+p[1]+p[2])/3 for p in dd)/n
    print(f"  diff {p1.split('/')[-1]} vs {p2.split('/')[-1]} in {box}: mean {m:.2f} {'MOTION' if m > 2 else 'STATIC!'}")

if __name__ == '__main__':
    mode, files = sys.argv[1], sys.argv[2:]
    D = '/home/z/my-project/world-21-suite/audit/spec/'
    files = [f if '/' in f else D+f for f in files]
    if mode == 'a':
        probes = {
            'banner strip':      (0, 0, 1920, 50),
            'banner text zone':  (260, 12, 1250, 44),
            'avatar (disc)':     (44, 74, 116, 146),
            'wordmark':          (150, 80, 560, 132),
            'downtime digits':   (1760, 95, 1880, 142),
            'row1 sparkline':    (522, 272, 1328, 336),
            'row1 badge':        (1534, 282, 1770, 326),
            'row2 badge':        (1534, 464, 1770, 508),
            'row3 badge':        (1534, 646, 1770, 690),
            'row4 badge':        (1534, 828, 1770, 872),
            'row2 beat dot':     (152, 478, 174, 500),
            'uptime col':        (1044, 286, 1194, 322),
            'foot chips':        (0, 952, 1920, 1038),
            'ticker cap':        (0, 1038, 240, 1080),
            'ticker mid':        (400, 1038, 1500, 1080),
        }
    elif mode == 'b':
        probes = {
            'h1 zone':           (660, 100, 1260, 250),
            'ring top arc':      (860, 260, 1060, 330),
            'ring bottom arc':   (860, 620, 1060, 690),
            'ring center face':  (870, 380, 1050, 560),
            'pct readout':       (880, 560, 1040, 600),
            'chip left (rec)':   (330, 440, 700, 500),
            'chip right (nom)':  (1220, 440, 1590, 500),
            'log head':          (630, 700, 1290, 730),
            'log lines':         (640, 730, 1280, 850),
            'log foot':          (700, 855, 1220, 890),
            'ticker cap':        (0, 1022, 260, 1080),
            'ticker mid':        (400, 1022, 1500, 1080),
        }
    elif mode == 'c':
        probes = {
            'lockup we-re-on-it': (64, 20, 720, 78),
            'downtime digits':    (1620, 30, 1870, 78),
            'chart head+badge':   (700, 130, 1114, 175),
            'chart candles zone': (100, 250, 1050, 900),
            'chart dead flatline':(100, 900, 1050, 990),
            'smile disc':         (1380, 160, 1580, 350),
            'wrench zone':        (1560, 300, 1680, 400),
            'steps list':         (1180, 430, 1820, 700),
            'wchips':             (1300, 710, 1700, 760),
            'wfoot note':         (1300, 950, 1780, 1000),
            'ticker cap':         (0, 1026, 250, 1080),
            'ticker mid':         (400, 1026, 1500, 1080),
        }
    elif mode == 'diff':
        # diff mode: p1 p2 box
        diff(files[0], files[1], tuple(int(x) for x in sys.argv[3:6+3]))
        sys.exit(0)
    for p in files:
        show(p, probes)
