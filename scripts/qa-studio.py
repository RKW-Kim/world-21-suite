#!/usr/bin/env python3
"""QA for speaking.html v2 ('the studio') + end-credits.html (restored credits roll).
Checks: structure, instant-jump waveform engine, wall contracts, schedule contract,
reduced-motion, overflow, page errors. Screenshots -> audit/studio/."""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8017"
OUT = "/home/z/my-project/world-21-suite/audit/studio"
results, errs = [], []

def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        errs.append(f"{name}: {detail}")

ADIMG = "data:image/svg+xml;utf8," + "%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='9'%3E%3Crect width='16' height='9' fill='%23164'/%3E%3C/svg%3E"

with sync_playwright() as p:
    b = p.chromium.launch()

    # ═══════════════ speaking.html v2 — default ═══════════════
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    cerrs = []
    pg.on("pageerror", lambda e: cerrs.append(str(e)))
    pg.on("console", lambda m: cerrs.append(m.text) if m.type == "error" else None)
    pg.goto(f"{BASE}/speaking.html", wait_until="networkidle")
    pg.wait_for_timeout(1200)

    check("6 seats (1 host + 5 guests)",
          pg.locator(".set.hostset").count() == 1 and pg.locator(".set.guest").count() == 5,
          f"host={pg.locator('.set.hostset').count()} guests={pg.locator('.set.guest').count()}")
    check("6 name tags", pg.locator(".ntag").count() == 6, f"got {pg.locator('.ntag').count()}")
    check("chat-bubble pips are GONE", pg.locator(".pip").count() == 0,
          f"got {pg.locator('.pip').count()}")
    check("6 waveform pills", pg.locator(".wv").count() == 6, f"got {pg.locator('.wv').count()}")
    bars = pg.locator(".wv .trk i")
    check("73 bars baked (13 host + 5x12)", bars.count() == 73, f"got {bars.count()}")
    check("headphones on host", pg.locator(".hostset .hp").count() == 1, "missing")
    check("boom mic on host desk", pg.locator(".hostset .boom").count() == 1, "missing")
    check("wall present", pg.locator("#ad").count() == 1 and pg.locator(".screen").count() == 1, "missing")
    check("wall idle slides x3", pg.locator("#slides .slide").count() == 3, f"got {pg.locator('#slides .slide').count()}")
    check("feed hidden by default", pg.locator("#feed").is_hidden(), "visible")
    check("corner brackets x4", pg.locator(".corner").count() == 4, f"got {pg.locator('.corner').count()}")
    check("ON AIR sign", pg.locator(".signbox").count() == 1, "missing")
    check("sig present", pg.locator(".sig").count() == 1, "missing")

    eng = pg.evaluate("""() => {
      const out = {wrap: [], wv: [], trk: [], barTiming: new Set(), barName: new Set(),
                   halo: 0, led: 0, tagAfter: 0, steps: 0};
      document.querySelectorAll('.wvwrap').forEach(w => out.wrap.push(getComputedStyle(w).animationName));
      document.querySelectorAll('.wv').forEach(w => out.wv.push(getComputedStyle(w).animationName));
      document.querySelectorAll('.wv .trk').forEach(t => out.trk.push(getComputedStyle(t).animationName));
      document.querySelectorAll('.wv i').forEach(i => {
        const cs = getComputedStyle(i);
        out.barTiming.add(cs.animationTimingFunction);
        out.barName.add(cs.animationName);
        if (/steps/.test(cs.animationTimingFunction)) out.steps++;
      });
      out.halo = [...document.querySelectorAll('.halo')].filter(h => getComputedStyle(h).animationName.startsWith('lamp')).length;
      out.led = [...document.querySelectorAll('.df')].filter(d => getComputedStyle(d, '::before').animationName.startsWith('lamp')).length;
      out.tagAfter = [...document.querySelectorAll('.ntag')].filter(t => getComputedStyle(t, '::after').animationName.startsWith('lamp')).length;
      return {wrap: out.wrap, wv: out.wv, trk: out.trk, timing: [...out.barTiming], names: [...out.barName],
              steps: out.steps, halo: out.halo, led: out.led, tagAfter: out.tagAfter};
    }""")
    check("pill frames stay steady (no envelope on frame)", all(n == "none" for n in eng["wrap"]), json.dumps(eng["wrap"]))
    check("6 pills ride lamp cycles", all(n.startswith("lamp") for n in eng["wv"]), json.dumps(eng["wv"]))
    check("6 bar tracks ride talk envelopes", all(n.startswith("talk") for n in eng["trk"]) and len(eng["trk"]) == 6, json.dumps(eng["trk"]))
    check("all 73 bars use steps(1,end) instant jumps", eng["steps"] == 73, json.dumps(eng["timing"]))
    check("bars draw from vjA/vjB/vjC", set(eng["names"]) <= {"vjA", "vjB", "vjC"} and len(eng["names"]) == 3, json.dumps(eng["names"]))
    check("6 halos on lamp cycles", eng["halo"] == 6, f"got {eng['halo']}")
    check("6 LED strips on lamp cycles", eng["led"] == 6, f"got {eng['led']}")
    check("6 tag glows on lamp cycles", eng["tagAfter"] == 6, f"got {eng['tagAfter']}")

    # instant-jump frame probe: scaleY holds then jumps (repeats AND changes)
    probe = pg.evaluate("""() => new Promise(res => {
      const bar = document.querySelector('.set.guest .wv i');
      const vals = [];
      const t0 = performance.now();
      const iv = setInterval(() => {
        vals.push(getComputedStyle(bar).transform);
        if (performance.now() - t0 > 1400) { clearInterval(iv);
          const uniq = new Set(vals);
          res({samples: vals.length, unique: uniq.size}); }
      }, 60);
    })""")
    check("frame probe: holds + jumps (instant, not smooth)",
          probe["unique"] >= 3 and probe["unique"] < probe["samples"],
          json.dumps(probe))

    # layout: no overflow, wall & rows inside frame, guests clear of wall bottom
    lay = pg.evaluate("""() => {
      const r = id => { const e = document.querySelector(id); if (!e) return null;
        const b = e.getBoundingClientRect(); return {x: b.x, y: b.y, r: b.right, b: b.bottom, w: b.width, h: b.height}; };
      return {wall: r('#ad'), host: r('.hostset'), grow: r('.guestrow'),
              sig: r('.sig'), sw: document.documentElement.scrollWidth,
              iw: window.innerWidth, sh: document.documentElement.scrollHeight};
    }""")
    check("no horizontal overflow", lay["sw"] <= lay["iw"], f"{lay['sw']} > {lay['iw']}")
    check("wall inside frame", lay["wall"] and lay["wall"]["x"] >= 0 and lay["wall"]["r"] <= lay["iw"], json.dumps(lay["wall"]))
    check("guest row inside frame", lay["grow"] and lay["grow"]["r"] <= lay["iw"], json.dumps(lay["grow"]))
    pg.screenshot(path=f"{OUT}/speaking-default.png")

    # ═══════════════ contracts ═══════════════
    pg2 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg2.on("pageerror", lambda e: cerrs.append(str(e)))
    pg2.goto(f"{BASE}/speaking.html?names=SMILE%2CMOOSE%2CJAZZ%2CKOBI%2CZAWADI%2CTABI&emojis=%F0%9F%98%8E%2C%F0%9F%A4%AF%2C%F0%9F%98%B1%2C%F0%9F%A4%96%2C%F0%9F%90%92&ad=NAIROBI%20COFFEE%20ROASTERS", wait_until="networkidle")
    pg2.wait_for_timeout(700)
    tags = pg2.locator(".ntag b").all_text_contents()
    check("?names= fills tags", tags[:6] == ["SMILE", "MOOSE", "JAZZ", "KOBI", "ZAWADI", "TABI"], json.dumps(tags))
    avs = pg2.locator(".guest .av").all_text_contents()
    check("?emojis= swaps faces", avs == ["😎", "🤯", "😱", "🤖", "🐒"], json.dumps(avs))
    check("?ad= shows sponsor line", pg2.locator(".slide.s1 .t").text_content().strip() == "NAIROBI COFFEE ROASTERS", pg2.locator(".slide.s1 .t").text_content())
    pg2.screenshot(path=f"{OUT}/speaking-params.png")

    pg3 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg3.goto(f"{BASE}/speaking.html?adimg={ADIMG}", wait_until="networkidle")
    pg3.wait_for_timeout(500)
    check("?adimg= covers the wall", pg3.locator(".screen img.feedimg").count() == 1 and pg3.locator("#slides").is_hidden(), "no img/visible slides")
    pg3.screenshot(path=f"{OUT}/speaking-adimg.png")

    pg4 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg4.goto(f"{BASE}/speaking.html?screen=1", wait_until="networkidle")
    pg4.wait_for_timeout(500)
    check("?screen=1 shows feed dress", pg4.locator("#feed").is_visible() and pg4.locator("#slides").count() == 0, "feed/slides wrong")
    check("?screen=1 renames chip", pg4.locator("#adchip").text_content().strip() == "SCREEN", pg4.locator("#adchip").text_content())
    pg4.screenshot(path=f"{OUT}/speaking-screen.png")

    pg5 = b.new_page(viewport={"width": 1920, "height": 1080})
    pg5.goto(f"{BASE}/speaking.html?noad=1", wait_until="networkidle")
    pg5.wait_for_timeout(500)
    check("?noad=1 strips wall to bare glass",
          pg5.locator("#slides").count() == 0 and pg5.locator("#feed").count() == 0 and pg5.locator("#adchip").count() == 0,
          "residue left")

    # smaller viewport sanity
    pg6 = b.new_page(viewport={"width": 1366, "height": 768})
    pg6.goto(f"{BASE}/speaking.html", wait_until="networkidle")
    pg6.wait_for_timeout(700)
    lay6 = pg6.evaluate("""() => ({sw: document.documentElement.scrollWidth, iw: window.innerWidth,
      wall: (() => { const b = document.querySelector('#ad').getBoundingClientRect();
        const g = document.querySelector('.guestrow').getBoundingClientRect();
        return {wallBottom: b.bottom, guestsTop: g.top, clear: g.top >= b.bottom - 2}; })()})""")
    check("1366x768 no overflow", lay6["sw"] <= lay6["iw"], json.dumps(lay6))
    check("1366x768 guests clear of wall", lay6["wall"]["clear"], json.dumps(lay6["wall"]))
    pg6.screenshot(path=f"{OUT}/speaking-1366.png")

    # reduced motion
    pg7 = b.new_page(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")
    pg7.goto(f"{BASE}/speaking.html", wait_until="networkidle")
    pg7.wait_for_timeout(400)
    rm = pg7.evaluate("""() => {
      const bar = getComputedStyle(document.querySelector('.wv i'));
      const wrap = getComputedStyle(document.querySelector('.wvwrap'));
      const s1 = getComputedStyle(document.querySelector('.slide.s1'));
      return {barName: bar.animationName, barTf: bar.transform, wrapName: wrap.animationName, s1: s1.opacity};
    }""")
    check("reduced-motion: bars frozen at static level",
          rm["barName"] in ("none", "vjA") and rm["barTf"] not in ("none", "matrix(1, 0, 0, 1, 0, 0)"), json.dumps(rm))
    check("reduced-motion: slide 1 readable", rm["s1"] == "1", rm["s1"])
    pg7.screenshot(path=f"{OUT}/speaking-reduced.png")

    # ═══════════════ end-credits.html ═══════════════
    pc = b.new_page(viewport={"width": 1920, "height": 1080})
    pc.on("pageerror", lambda e: cerrs.append(str(e)))
    pc.goto(f"{BASE}/end-credits.html", wait_until="networkidle")
    pc.wait_for_timeout(1000)
    check("credits box present", pc.locator(".credits").count() == 1, "missing")
    cb = pc.locator(".credits").bounding_box()
    check("credits box sits on the RIGHT", cb and cb["x"] > 1920 * 0.55, json.dumps(cb))
    check("14 credit rows (7 x2 loop)", pc.locator(".cr").count() == 14, f"got {pc.locator('.cr').count()}")
    roll = pc.evaluate("() => getComputedStyle(document.querySelector('.ctrack')).animationName")
    check("credits roll looping", roll == "roll", roll)
    check("orbit + verbatim face", pc.locator(".orbitB .face svg").count() == 1, "missing")
    check("follow chip with sheen", pc.locator(".follow").count() == 1, "missing")
    check("bell fallback (no schedule)", pc.locator(".bellrow").is_visible() and not pc.locator(".nextrow").is_visible(), "wrong state")
    import re as _re
    check("clock chip ticks", bool(_re.search(r"\d{2}:\d{2}", pc.locator("#clock").text_content())), pc.locator("#clock").text_content())
    pc.screenshot(path=f"{OUT}/credits-default.png")

    pc2 = b.new_page(viewport={"width": 1920, "height": 1080})
    pc2.goto(f"{BASE}/end-credits.html?ep=77&next=Saturday%20%C2%B7%208PM%20EAT&host=Alice&what=Trivia%20Night", wait_until="networkidle")
    pc2.wait_for_timeout(600)
    check("?ep= fills header", pc2.locator(".chead .ep").text_content().strip().endswith("77"), pc2.locator(".chead .ep").text_content())
    check("?next= activates card", pc2.locator(".nextrow").is_visible() and not pc2.locator(".bellrow").is_visible(), "wrong state")
    check("?next= fills credit row", pc2.locator("#crNext").text_content() == "Saturday · 8PM EAT", pc2.locator("#crNext").text_content())
    nh = pc2.locator("#nh").text_content()
    check("?host/?what fill chip line", "hosted by Alice" in nh and "Trivia Night" in nh, nh)
    pc2.screenshot(path=f"{OUT}/credits-next.png")

    pc3 = b.new_page(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")
    pc3.goto(f"{BASE}/end-credits.html", wait_until="networkidle")
    pc3.wait_for_timeout(400)
    rmr = pc3.evaluate("() => getComputedStyle(document.querySelector('.ctrack')).animationName")
    check("credits reduced-motion: roll frozen", rmr in ("none",), rmr)

    b.close()

print("\\n" + "=" * 60)
fails = [r for r in results if not r[1]]
print(f"TOTAL {len(results)} | PASS {len(results) - len(fails)} | FAIL {len(fails)}")
if cerrs:
    print("PAGE ERRORS:"); [print("  " + e) for e in cerrs]
sys.exit(1 if (fails or cerrs) else 0)
