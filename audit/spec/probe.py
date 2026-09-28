#!/usr/bin/env python3
"""Pixel probes for inter-a/b/c QA — judges composition, tokens, legibility from pixels."""
import sys, os
from PIL import Image

AUD = "/home/z/my-project/world-21-suite/audit/spec"

def stats(img, box=None):
    im = img.crop(box) if box else img
    im = im.convert("RGB")
    px = list(im.getdata())
    n = len(px)
    r = sum(p[0] for p in px)/n; g = sum(p[1] for p in px)/n; b = sum(p[2] for p in px)/n
    return (round(r,1), round(g,1), round(b,1), n)

def count(img, pred, box=None):
    im = img.crop(box) if box else img
    im = im.convert("RGB")
    c = 0
    for p in im.getdata():
        if pred(p): c += 1
    return c

YELLOW = lambda p: p[0] > 200 and 140 < p[1] < 225 and p[2] < 110
LIGHT  = lambda p: p[0] > 180 and p[1] > 180 and p[2] > 180
GREEN  = lambda p: p[1] > 120 and p[0] < 100 and p[2] < 130

def probe(path, checks):
    img = Image.open(path).convert("RGB")
    print(f"\n== {os.path.basename(path)} == size={img.size}")
    mr,mg,mb,_ = stats(img)
    print(f"  mean RGB ({mr},{mg},{mb})")
    fails = []
    for name, fn in checks:
        try:
            v = fn(img)
            ok = v if not isinstance(v, tuple) else v[0]
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: {v if not isinstance(v,tuple) else v[1]}")
            if not ok: fails.append(name)
        except Exception as e:
            print(f"  ERR   {name}: {e}"); fails.append(name)
    return fails

def diff(path1, path2):
    a = Image.open(path1).convert("RGB"); b = Image.open(path2).convert("RGB")
    if a.size != b.size: return 1.0
    pa = list(a.getdata()); pb = list(b.getdata())
    d = sum(1 for x, y in zip(pa, pb) if abs(x[0]-y[0])+abs(x[1]-y[1])+abs(x[2]-y[2]) > 24)
    return d/len(pa)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "a":
        checks = [
            ("dark stage", lambda im: stats(im)[0] < 45),
            ("yellow present (brand)", lambda im: (lambda c: (c > 3000, c))(count(im, YELLOW))),
            ("giant type light pixels left rail", lambda im: (lambda c: (c > 8000, c))(count(im, LIGHT, (60, 260, 700, 760)))),
            ("countdown chip region lit", lambda im: (lambda c: (c > 400, c))(count(im, YELLOW, (1150, 380, 1850, 500)))),
            ("ticker yellow cap bottom-left", lambda im: (lambda c: (c > 2000, c))(count(im, YELLOW, (0, 1014, 260, 1080)))),
            ("ticker strip dark", lambda im: stats(im, (0, 1014, 1920, 1080))[0] < 60),
            ("rundown rows region has text", lambda im: (lambda c: (c > 5000, c))(count(im, LIGHT, (820, 300, 1850, 950)))),
        ]
        sys.exit(1 if probe(os.path.join(AUD, "inter-a-t0.png"), checks) else 0)
    if mode == "b":
        checks = [
            ("dark stage", lambda im: stats(im)[0] < 45),
            ("yellow present (perch+accents)", lambda im: (lambda c: (c > 5000, c))(count(im, YELLOW))),
            ("perch smile on board top edge", lambda im: (lambda c: (c > 1500, c))(count(im, YELLOW, (300, 330, 560, 500)))),
            ("headline light pixels", lambda im: (lambda c: (c > 4000, c))(count(im, LIGHT, (700, 130, 1250, 260)))),
            ("stat digits lit", lambda im: (lambda c: (c > 3000, c))(count(im, LIGHT, (380, 560, 1550, 760)))),
            ("notes region has card", lambda im: (lambda c: (c > 800, c))(count(im, LIGHT, (420, 830, 1500, 950)))),
            ("ticker yellow cap bottom-left", lambda im: (lambda c: (c > 2000, c))(count(im, YELLOW, (0, 1014, 320, 1080)))),
        ]
        sys.exit(1 if probe(os.path.join(AUD, "inter-b-t0.png"), checks) else 0)
    if mode == "c":
        checks = [
            ("dark stage", lambda im: stats(im)[0] < 45),
            ("yellow present (smile+cards+accents)", lambda im: (lambda c: (c > 8000, c))(count(im, YELLOW))),
            ("countdown digits huge & lit", lambda im: (lambda c: (c > 20000, c))(count(im, LIGHT, (560, 280, 1360, 520)))),
            ("film band cards lit", lambda im: (lambda c: (c > 30000, c))(count(im, lambda p: sum(p) > 180, (0, 730, 1920, 930)))),
            ("green card present", lambda im: (lambda c: (c > 4000, c))(count(im, GREEN))),
            ("smile near strip top", lambda im: (lambda c: (c > 1200, c))(count(im, YELLOW, (0, 590, 1920, 740)))),
            ("ticker yellow cap bottom-left", lambda im: (lambda c: (c > 2000, c))(count(im, YELLOW, (0, 1014, 320, 1080)))),
        ]
        sys.exit(1 if probe(os.path.join(AUD, "inter-c-t0.png"), checks) else 0)
    if mode == "motion":
        a, b = sys.argv[2], sys.argv[3]
        d = diff(a, b)
        print(f"frame diff {os.path.basename(a)} vs {os.path.basename(b)}: {d:.4f} -> {'MOTION' if d > 0.004 else 'STATIC?'}")
