#!/usr/bin/env python3
"""Staggered frames of the panel to verify conversation turn-taking reads."""
from playwright.sync_api import sync_playwright

OUT = "/home/z/my-project/world-21-suite/audit/panel"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto("http://127.0.0.1:8017/speaking.html", wait_until="networkidle")
    pg.wait_for_timeout(900)
    for i in range(3):
        hot = pg.evaluate("""() => [...document.querySelectorAll('.set')].map(s => ({
            viz: getComputedStyle(s.querySelector('.viz')).opacity,
            lamp: getComputedStyle(s.querySelector('.halo')).opacity,
            tag: s.querySelector('.ntag b').textContent}))""")
        on = [h["tag"] for h in hot if float(h["lamp"]) > .5]
        print(f"frame {i}: hot = {on} | lamp opacities = {[round(float(h['lamp']),2) for h in hot]}")
        pg.screenshot(path=f"{OUT}/frame-{i}.png")
        pg.wait_for_timeout(5200)
    b.close()
print("done")
