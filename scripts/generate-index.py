#!/usr/bin/env python3
"""Generate _site/index.html listing every overlay HTML file as a clickable link.

Run from the repo root after copying overlay/* to _site/.
"""
import html
from pathlib import Path


def main() -> None:
    site = Path("_site")
    if not site.is_dir():
        raise SystemExit(f"_site/ folder not found at {site.resolve()}")

    files = sorted(
        p.name for p in site.iterdir() if p.is_file() and p.suffix == ".html"
    )

    rows = (
        "\n".join(
            f'<li><a href="{html.escape(f)}">{html.escape(f)}</a></li>'
            for f in files
        )
        if files
        else "<li>(no HTML files found)</li>"
    )

    index = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>world-21-suite — overlay index</title>
<style>
  body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #0a0a0b; color: #fafafa; max-width: 720px; margin: 4rem auto; padding: 0 1rem; }
  h1 { font-weight: 600; margin-bottom: 0.5rem; }
  p.muted { color: #8a8a93; margin-bottom: 2rem; }
  ul { list-style: none; padding: 0; }
  li { padding: 0.5rem 0; border-bottom: 1px solid #1f1f23; }
  a { color: #FFC107; text-decoration: none; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  a:hover { text-decoration: underline; }
  code { background: #141416; padding: 1px 6px; border-radius: 4px; font-size: 12px; }
</style>
</head>
<body>
  <h1>world-21-suite — overlay index</h1>
  <p class="muted">Each file below is a self-contained OBS browser source. Copy the URL into OBS.</p>
  <ul>
""" + rows + """
  </ul>
  <p class="muted" style="margin-top: 2rem;">
    URL pattern: <code>https://rkw-kim.github.io/world-21-suite/&lt;filename&gt;.html</code><br>
    Archive of earlier iterations: <a href="archive/">archive/</a>
  </p>
</body>
</html>
"""
    (site / "index.html").write_text(index)
    print(f"Generated _site/index.html with {len(files)} overlay links")


if __name__ == "__main__":
    main()
