#!/usr/bin/env python3
"""Screenshot auditor for stingers lab pages. Usage: python3 scripts/audit-sg.py <html> <out> [keys] [wait_ms]"""
import sys, asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8799/"

async def main():
    page_name = sys.argv[1]          # e.g. stingers-example.html?x=1
    out = sys.argv[2]
    keys = sys.argv[3] if len(sys.argv) > 3 else ""
    wait = int(sys.argv[4]) if len(sys.argv) > 4 else 1600
    url = BASE + page_name
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        await pg.goto(url, wait_until="networkidle")
        await pg.wait_for_timeout(900)
        for k in keys:
            await pg.keyboard.press(k if len(k) > 1 else k)
            await pg.wait_for_timeout(700)
        await pg.wait_for_timeout(wait)
        await pg.screenshot(path=out)
        print("ERRORS:", errors if errors else "none")
        await b.close()

asyncio.run(main())
