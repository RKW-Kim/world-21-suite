#!/usr/bin/env python3
"""QA for the rebuilt speaking.html — 'the panel' podcast studio set.
Checks: structure, synced speech rhythms, ad slot, params, reduced-motion, overflow, errors."""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8017"
OUT = "/home/z/my-project/world-21-suite/audit/panel"
results, errs = [], []

def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    if not ok:
        errs.append(f"{name}: {detail}")

with sync_playwright() as p:
    b = p.chromium.launch()
    # ── pass 1: default page at 1920x1080 ──
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    cerrs = []
    pg.on("pageerror", lambda e: cerrs.append(str(e)))
    pg.on("console", lambda m: cerrs.append(m.text) if m.type == "error" else None)
    pg.goto(f"{BASE}/speaking.html", wait_until="networkidle")
    pg.wait_for_timeout(1200)

    seats = pg.locator(".set")
    check("6 seats", seats.count() == 6, f"got {seats.count()}")
    check("5 guests + 1 host",
          pg.locator(".set.guest").count() == 5 and pg.locator(".set.host").count() == 1,
          f"guest={pg.locator('.set.guest').count()} host={pg.locator('.set.host').count()}")
    check("6 name tags", pg.locator(".ntag").count() == 6, f"got {pg.locator('.ntag').count()}")
    bars = pg.locator(".viz .bar")
    check("bars baked (9 host + 5x7 guest = 44)", bars.count() == 44, f"got {bars.count()}")
    check("ad slot present", pg.locator("#ad").count() == 1, "missing #ad")
    check("3 ad slides", pg.locator(".slide").count() == 3, f"got {pg.locator('.slide').count()}")
    check("hanging ON AIR sign", pg.locator(".signbox").count() == 1, "missing")
    check("floor band", pg.locator(".floorband").count() == 1, "missing")
    check("sig present", pg.locator(".sig").count() == 1, "missing")

    # speech engine: every viz + halo + pip + ntag::after carries a talk/lamp animation
    anim = pg.evaluate("""() => {
      const out = {viz: [], halo: 0, pip: 0, tagAfter: 0, pipBars: 0};
      document.querySelectorAll('.viz').forEach(v => out.viz.push(getComputedStyle(v).animationName));
      out.halo = [...document.querySelectorAll('.halo')].filter(h => /talk|lamp|^none/.test(getComputedStyle(h).animationName) && getComputedStyle(h).animationName.startsWith('lamp')).length;
      out.pip = [...document.querySelectorAll('.pip')].filter(h => getComputedStyle(h).animationName.startsWith('lamp')).length;
      out.pipBars = [...document.querySelectorAll('.pip i')].filter(i => getComputedStyle(i).animationName === 'eqB').length;
      const tags = [...document.querySelectorAll('.ntag')];
      out.tagAfter = tags.filter(t => getComputedStyle(t, '::after').animationName.startsWith('lamp')).length;
      return out;
    }""")
    check("all 6 rigs ride talk envelopes",
          all(n.startswith("talk") for n in anim["viz"]), json.dumps(anim["viz"]))
    check("6 halos on lamp cycles", anim["halo"] == 6, f"got {anim['halo']}")
    check("6 pips on lamp cycles", anim["pip"] == 6, f"got {anim['pip']}")
    check("15 pip bars looping eqB", anim["pipBars"] == 18, f"got {anim['pipBars']}")  # 6 pips x 3
    check("6 tag glows on lamp cycles", anim["tagAfter"] == 6, f"got {anim['tagAfter']}")

    # envelope motion probe: rig scaleY must differ between hot and quiet moments
    scales = pg.evaluate("""() => new Promise(res => {
      const v = document.querySelector('.set.r1 .viz');
      const s1 = getComputedStyle(v).transform;
      setTimeout(() => res([s1, getComputedStyle(v).transform]), 2500);
    })""")
    check("rig envelope actually moves", scales[0] != scales[1], json.dumps(scales))

    # overflow
    ov = pg.evaluate("() => [document.scrollingElement.scrollWidth, window.innerWidth]")
    check("no horizontal overflow", ov[0] <= ov[1], f"scrollW={ov[0]} innerW={ov[1]}")
    check("0 page errors (default)", len(cerrs) == 0, "; ".join(cerrs[:3]))

    pg.screenshot(path=f"{OUT}/panel-default.png")

    # desks stand on the floor: seat bottoms vs floor top edge
    geo = pg.evaluate("""() => {
      const seat = document.querySelector('.set.host .desk').getBoundingClientRect();
      const fl = document.querySelector('.floorband').getBoundingClientRect();
      return {deskBottom: seat.bottom, floorTop: fl.top};
    }""")
    check("host desk lands on floor", abs(geo["deskBottom"] - geo["floorTop"]) < 4,
          json.dumps(geo))
    pg.close()

    # ── pass 2: params ──
    pg2 = b.new_page(viewport={"width": 1920, "height": 1080})
    cerrs2 = []
    pg2.on("pageerror", lambda e: cerrs2.append(str(e)))
    pg2.goto(BASE + "/speaking.html?names=Alpha,Bravo,Charlie&emojis=%F0%9F%94%A5,%F0%9F%98%8E&ad=TEST%20AD%20LINE",
              wait_until="networkidle")
    pg2.wait_for_timeout(600)
    tags = pg2.locator(".ntag b").all_inner_texts()
    check("names fill seats left->right",
          tags[:3] == ["Alpha", "Bravo", "Charlie"] and tags[3:] == ["HALO", "PROF"] if False else
          tags[:3] == ["Alpha", "Bravo", "Charlie"], json.dumps(tags))
    av = pg2.locator(".av").all_inner_texts()
    check("emoji override seats 1-2", av[0] == "🔥" and av[1] == "😎", json.dumps(av))
    adt = pg2.locator("#ad .s1 .t").inner_text()
    check("?ad= replaces carousel", adt == "TEST AD LINE", adt)
    check("?ad= hides s2/s3",
          not pg2.locator("#ad .s2").is_visible() and not pg2.locator("#ad .s3").is_visible(), "")
    check("0 page errors (params)", len(cerrs2) == 0, "; ".join(cerrs2[:3]))
    pg2.screenshot(path=f"{OUT}/panel-params.png")
    pg2.close()

    # ── pass 3: adimg + noad ──
    pg3 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg3.goto(f"{BASE}/speaking.html?noad=1", wait_until="domcontentloaded")
    check("?noad=1 removes slot", pg3.locator("#ad").count() == 0, "")
    pg3.close()

    pg4 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg4.goto(BASE + "/speaking.html?adimg=https://rkw-kim.github.io/world-21-suite/overlay/assets/smile-mark.svg",
              wait_until="domcontentloaded")
    pg4.wait_for_timeout(800)
    check("?adimg= injects img", pg4.locator("#ad img").count() == 1, "")
    pg4.close()

    # ── pass 4: reduced motion poster ──
    pg5 = b.new_page(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")
    pg5.goto(f"{BASE}/speaking.html", wait_until="networkidle")
    rm = pg5.evaluate("""() => {
      const names = new Set();
      document.querySelectorAll('.viz,.halo,.pip,.bar,.av,.signbox,.adshine,.slide').forEach(e =>
        names.add(getComputedStyle(e).animationName));
      names.delete('none');
      const pipVisible = [...document.querySelectorAll('.pip')].some(p => getComputedStyle(p).display !== 'none');
      const s1 = getComputedStyle(document.querySelector('.slide.s1')).opacity;
      return {running: [...names], pipVisible, s1};
    }""")
    check("reduced-motion: nothing runs", len(rm["running"]) == 0, json.dumps(rm["running"]))
    check("reduced-motion: pips hidden", not rm["pipVisible"], "")
    check("reduced-motion: slide 1 is the poster", rm["s1"] == "1", f"s1 opacity={rm['s1']}")
    pg5.screenshot(path=f"{OUT}/panel-reduced.png")
    pg5.close()
    b.close()

fails = [r for r in results if not r[1]]
print(f"\n==== QA PANEL: {len(results) - len(fails)}/{len(results)} PASS ====")
for n, ok, d in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {n}" + (f" — {d}" if (d and not ok) else ""))
sys.exit(1 if fails else 0)
