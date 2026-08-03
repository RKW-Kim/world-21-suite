import sys, base64, pathlib
url = "http://127.0.0.1:8787/core/update.txt"
try:
    import urllib.request
    data = urllib.request.urlopen(url, timeout=10).read()
except Exception as e:
    print("Could not reach bridge:", e)
    sys.exit(1)
files = {}
for block in data.decode().strip().split("\n---\n"):
    path, b64 = block.split("\n", 1)
    files[path] = base64.b64decode(b64)
for path, content in files.items():
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    print("wrote", path, len(content), "bytes")
print("OK - update applied")
