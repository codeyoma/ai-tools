"""Turn the artifact build (catalog.json + preview files + image bundles) into a static site.

Usage: python3 -I make_static.py <artifact_store_dir> <site_dir>

- Previews: every entry gets img/<id>.jpg (bundled previews are decoded back to files).
- Icons: base64 data URIs become icons/<id>.png so catalog.json stays small.
- index.html: the artifact page is wrapped in a full HTML document with SEO/OG tags.
"""
import base64
import json
import os
import shutil
import sys

store, site = sys.argv[1:3]
img_out = os.path.join(site, "img")
icon_out = os.path.join(site, "icons")
data_out = os.path.join(site, "data")
for d in (img_out, icon_out, data_out):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)

with open(os.path.join(store, "data", "catalog.json")) as f:
    entries = json.load(f)

bundles = {}
missing = 0
for e in entries:
    eid = e["id"]
    target = os.path.join(img_out, f"{eid}.jpg")
    if e.get("imgB"):
        path = os.path.join(store, e["imgB"])
        if path not in bundles:
            with open(path) as f:
                bundles[path] = json.load(f)
        b64 = bundles[path].get(eid)
        if b64:
            with open(target, "wb") as f:
                f.write(base64.b64decode(b64))
    elif e.get("img"):
        src = os.path.join(store, e["img"])
        if os.path.exists(src):
            shutil.copyfile(src, target)
    if os.path.exists(target):
        e["img"] = f"img/{eid}.jpg"
    else:
        if e.get("img") or e.get("imgB"):
            missing += 1
        e["img"] = None
    e.pop("imgB", None)

    icon = e.get("icon")
    if icon and icon.startswith("data:image/png;base64,"):
        with open(os.path.join(icon_out, f"{eid}.png"), "wb") as f:
            f.write(base64.b64decode(icon.split(",", 1)[1]))
        e["icon"] = f"icons/{eid}.png"

with open(os.path.join(data_out, "catalog.json"), "w") as f:
    json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))

print(f"entries={len(entries)} previews={sum(1 for e in entries if e['img'])} "
      f"icons={sum(1 for e in entries if e.get('icon'))} missing_previews={missing} "
      f"catalog_bytes={os.path.getsize(os.path.join(data_out, 'catalog.json'))}")
