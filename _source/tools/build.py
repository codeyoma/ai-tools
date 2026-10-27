"""Merge section data files and image results into the published catalog.

Usage:
  python3 -I build.py merge <data_src_dir> <merged.json>
  python3 -I build.py final <merged.json> <download_dir> <store_dir>
"""
import glob
import json
import os
import re
import sys

KEYS = ["id", "name", "vendor", "domain", "category", "tagline", "description", "connect", "worksWith",
        "aiCost", "price", "free", "official", "status", "stars", "updated", "homepage", "repo", "install",
        "caveats", "korea", "starter", "sources", "foundVia"]
ENUMS = {
    "domain": {"general", "finance", "game", "web", "mobile", "design", "music", "video", "ideation", "startup"},
    "aiCost": {"plan", "credits", "apikey", "none"},
    "official": {"official", "community", "third-party"},
    "status": {"active", "beta", "preview", "experimental", "deprecated", "archived", "shutdown", "stale"},
}
CONNECT = {"remote-mcp", "local-mcp", "plugin", "skills", "cli", "signin", "byok", "ide", "library", "app", "connector"}
WORKS = {"claude", "chatgpt", "gemini", "copilot", "cursor", "local"}
# Same product listed by two sections; keep the other copy.
EXCLUDE = {"mob-junie", "web-firebase-studio", "vgen-remotion", "vgen-hyperframes", "vgen-opusclip", "vgen-descript",
           "vgen-ffmpeg", "vgen-video-use", "vedit-vrew", "biz-angellist-mcp"}
# Same product, different angle per section; make the names tell them apart.
RENAME = {"mob-lovable-mobile": "Lovable (모바일 앱)", "mob-anything": "Anything (모바일 앱)"}


def norm(name):
    return re.sub(r"[^a-z0-9가-힣]", "", name.lower())


def merge(src_dir, out_path):
    entries, problems, seen_ids, seen_names = [], [], set(), {}
    for path in sorted(glob.glob(os.path.join(src_dir, "*.json"))):
        with open(path) as f:
            data = json.load(f)
        for e in data:
            e = {k: e.get(k) for k in KEYS}
            tag = f"{os.path.basename(path)}:{e['id']}"
            for k, allowed in ENUMS.items():
                if e[k] not in allowed:
                    problems.append(f"{tag} bad {k}={e[k]!r}")
            e["connect"] = [c for c in (e["connect"] or []) if c in CONNECT]
            e["worksWith"] = [w for w in (e["worksWith"] or []) if w in WORKS]
            e["caveats"] = [c for c in (e["caveats"] or []) if c][:3]
            e["sources"] = [s for s in (e["sources"] or []) if isinstance(s, dict) and str(s.get("url", "")).startswith("http")][:3]
            for k in ("homepage",):
                if e[k] and not str(e[k]).startswith("https://"):
                    e[k] = None if not str(e[k]).startswith("http://") else e[k]
            if e["repo"] and not re.fullmatch(r"[\w.-]+/[\w.-]+", e["repo"]):
                problems.append(f"{tag} bad repo {e['repo']!r}")
                e["repo"] = None
            if not isinstance(e["stars"], int):
                e["stars"] = None
            e["free"] = bool(e["free"])
            e["starter"] = bool(e["starter"])
            if e["id"] in EXCLUDE:
                continue
            e["name"] = RENAME.get(e["id"], e["name"])
            if e["id"] in seen_ids:
                problems.append(f"{tag} duplicate id")
                continue
            key = norm(e["name"])
            if key in seen_names:
                problems.append(f"{tag} duplicate name of {seen_names[key]}")
            seen_names.setdefault(key, e["id"])
            seen_ids.add(e["id"])
            entries.append(e)
    with open(out_path, "w") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    by = {}
    for e in entries:
        by[e["domain"]] = by.get(e["domain"], 0) + 1
    print(f"entries={len(entries)} by_domain={by}")
    for p in problems:
        print("PROBLEM", p)


def small_icon(dl_dir, eid, size=72):
    """Re-encode the fetched icon at a smaller size to keep catalog.json light."""
    import base64
    import subprocess
    src = os.path.join(dl_dir, eid, "icon-final.png")
    out = os.path.join(dl_dir, eid, f"icon{size}.png")
    if not os.path.exists(src):
        return None
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        subprocess.run(["sips", "-Z", str(size), src, "--out", out], capture_output=True)
    if not os.path.exists(out):
        return None
    with open(out, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def bundle(entries, store_dir, dl_dir, published_list, per_bundle=20):
    """Pack preview images that are not already published as files into JSON bundles.

    The artifact keeps at most 511 files per version, so new previews travel as
    base64 inside a few bundle files that the page loads lazily.
    """
    import base64
    import shutil
    with open(published_list) as f:
        published = set(f.read().split())
    bdir = os.path.join(store_dir, "imgb")
    shutil.rmtree(bdir, ignore_errors=True)
    os.makedirs(bdir)
    parked = os.path.join(dl_dir, "_bundled")
    os.makedirs(parked, exist_ok=True)
    groups = {}
    for e in entries:
        if e["img"] and os.path.basename(e["img"]) not in published:
            groups.setdefault(e["domain"], []).append(e)
    count = 0
    for domain, items in groups.items():
        for i in range(0, len(items), per_bundle):
            chunk = items[i:i + per_bundle]
            name = f"imgb/{domain}-{i // per_bundle + 1}.json"
            payload = {}
            for e in chunk:
                src = os.path.join(store_dir, e["img"])
                with open(src, "rb") as f:
                    payload[e["id"]] = base64.b64encode(f.read()).decode()
                shutil.move(src, os.path.join(parked, os.path.basename(src)))
                e["imgB"], e["img"] = name, None
            with open(os.path.join(store_dir, name), "w") as f:
                json.dump(payload, f, separators=(",", ":"))
            count += 1
    return count


def final(merged_path, dl_dir, store_dir, published_list=None):
    with open(merged_path) as f:
        entries = json.load(f)
    results = {}
    for path in sorted(glob.glob(os.path.join(dl_dir, "_results_*.json"))):
        with open(path) as f:
            for k, v in json.load(f).items():
                results.setdefault(k, {}).update({x: y for x, y in v.items() if y is not None})
    for e in entries:
        r = results.get(e["id"], {})
        img = r.get("img")
        if img and not os.path.exists(os.path.join(store_dir, img)):
            parked = os.path.join(dl_dir, "_bundled", os.path.basename(img))
            if os.path.exists(parked):
                os.replace(parked, os.path.join(store_dir, img))
            else:
                img = None
        e["img"], e["imgSrc"], e["imgKind"] = img, r.get("imgSrc") if img else None, r.get("imgKind") if img else None
        e["icon"] = small_icon(dl_dir, e["id"]) or r.get("icon")
        e["imgB"] = None
    bundles = bundle(entries, store_dir, dl_dir, published_list) if published_list else 0
    out = os.path.join(store_dir, "data", "catalog.json")
    with open(out, "w") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))
    used = {e["img"] for e in entries if e["img"]}
    bundled = sum(1 for e in entries if e["imgB"])
    for path in glob.glob(os.path.join(store_dir, "img", "*.jpg")):
        if f"img/{os.path.basename(path)}" not in used:
            os.remove(path)
    print(f"catalog={len(entries)} previews={len(used)} bundled={bundled} in {bundles} bundles "
          f"icons={sum(1 for e in entries if e['icon'])} "
          f"bytes={os.path.getsize(out)}")


if sys.argv[1] == "merge":
    merge(sys.argv[2], sys.argv[3])
else:
    final(*sys.argv[2:6])
