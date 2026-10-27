"""Screenshot homepages for entries that still have no preview image.

Usage: python3 -I shots.py <catalog.json> <download_dir> <store_dir>
Reads and updates <download_dir>/_results.json.
"""
import concurrent.futures as cf
import glob
import json
import os
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
catalog_path, dl_dir, store_dir = sys.argv[1:4]
results_path = os.path.join(dl_dir, "_results_zz_shots.json")


def shoot(job):
    idx, entry = job
    eid, url = entry["id"], entry["homepage"]
    raw = os.path.join(dl_dir, eid, "shot.png")
    out = os.path.join(store_dir, "img", f"{eid}.jpg")
    profile = os.path.join(dl_dir, f"_chrome{idx % 4}")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
           "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
           "--window-size=1280,672", "--virtual-time-budget=7000", "--timeout=25000",
           f"--screenshot={raw}", url]
    try:
        subprocess.run(cmd, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return eid, None
    if not os.path.exists(raw) or os.path.getsize(raw) < 15000:
        return eid, None
    r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "68", "-Z", "720", raw, "--out", out],
                       capture_output=True)
    return eid, (url if r.returncode == 0 else None)


def main():
    with open(catalog_path) as f:
        entries = json.load(f)
    results = {}
    for path in sorted(glob.glob(os.path.join(dl_dir, "_results_*.json"))):
        with open(path) as f:
            for k, v in json.load(f).items():
                results.setdefault(k, {}).update({x: y for x, y in v.items() if y is not None})
    todo = [e for e in entries if not results.get(e["id"], {}).get("img")
            and e.get("homepage") and "github.com/" not in e["homepage"]]
    for e in todo:
        os.makedirs(os.path.join(dl_dir, e["id"]), exist_ok=True)
    done = 0
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for eid, url in pool.map(shoot, enumerate(todo)):
            if url:
                results.setdefault(eid, {"id": eid})
                results[eid].update(img=f"img/{eid}.jpg", imgSrc=url, imgKind="shot")
                done += 1
    with open(results_path, "w") as f:
        json.dump({k: v for k, v in results.items() if v.get("imgKind") == "shot"}, f)
    print(f"screenshot candidates={len(todo)} captured={done}")


main()
