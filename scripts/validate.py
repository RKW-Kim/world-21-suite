# CI + local check: JSON parses, brand.json has required keys, pages link smile.css.
import json, glob, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "core"); errors = []
for f in glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True):
    if "node_modules" in f: continue
    try:
        with open(f, encoding="utf-8") as fh: data = json.load(fh)
    except Exception as e:
        errors.append("BAD JSON %s: %s" % (f, e)); continue
    if os.path.basename(f) == "brand.json":
        for k in ("wordmark", "tokens", "handles"):
            if k not in data: errors.append("%s missing key %s" % (f, k))
for html in glob.glob(os.path.join(CORE, "*.html")):
    with open(html, encoding="utf-8") as fh: t = fh.read()
    if "smile.css" not in t: errors.append("%s does not link smile.css" % html)
print("validate: %d error(s)" % len(errors))
for e in errors: print("  - " + e)
sys.exit(1 if errors else 0)
