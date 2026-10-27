"""Fetch an icon and a preview image for every catalog entry.

Usage: python3 -I fetch_images.py <catalog.json> <download_dir> <store_dir>

Preview: the homepage's og:image / twitter:image, else the GitHub social card.
Icon: apple-touch-icon / large favicon from the homepage, else Google's favicon
service, else the GitHub owner avatar. Raw downloads stay in <download_dir>;
converted files go to <store_dir>/img (previews) and are embedded (icons).
"""
import base64
import concurrent.futures as cf
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
MAX_BYTES = 6 * 1024 * 1024

catalog_path, dl_dir, store_dir = sys.argv[1:4]
img_dir = os.path.join(store_dir, "img")
os.makedirs(img_dir, exist_ok=True)


def get(url, limit=MAX_BYTES, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept,
                                               "Accept-Language": "en-US,en;q=0.8,ko;q=0.6"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = r.read(limit + 1)
        if len(data) > limit:
            raise ValueError("too large")
        return data, r.geturl(), r.headers.get("Content-Type", "")


def image_kind(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] == b"\x00\x00\x01\x00":
        return "ico"
    return None


def meta_content(page, names):
    for tag in re.findall(r"<meta\b[^>]*>", page, re.I):
        key = re.search(r'(?:property|name)\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        val = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if key and val and key.group(1).lower() in names:
            return html.unescape(val.group(1).strip())
    return None


def icon_links(page):
    found = []
    for tag in re.findall(r"<link\b[^>]*>", page, re.I):
        rel = re.search(r'rel\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        href = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if not rel or not href:
            continue
        rel = rel.group(1).lower()
        if "icon" not in rel:
            continue
        sizes = re.search(r'sizes\s*=\s*["\'](\d+)x\d+', tag, re.I)
        score = int(sizes.group(1)) if sizes else (180 if "apple" in rel else 32)
        h = html.unescape(href.group(1).strip())
        if h.lower().split("?")[0].endswith(".svg"):
            continue
        found.append((score, h))
    found.sort(reverse=True)
    return [h for _, h in found]


def pixel_width(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", path], capture_output=True, text=True)
    m = re.search(r"pixelWidth:\s*(\d+)", out.stdout)
    return int(m.group(1)) if m else 0


def convert(raw_path, out_path, fmt, max_dim, quality=None):
    cmd = ["sips", "-s", "format", fmt]
    if quality:
        cmd += ["-s", "formatOptions", str(quality)]
    cmd += ["-Z", str(max_dim), raw_path, "--out", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0


def save_raw(entry_dir, name, data):
    kind = image_kind(data)
    if not kind:
        return None
    path = os.path.join(entry_dir, f"{name}.{kind}")
    with open(path, "wb") as f:
        f.write(data)
    return path


def process(entry):
    eid = entry["id"]
    entry_dir = os.path.join(dl_dir, eid)
    os.makedirs(entry_dir, exist_ok=True)
    result = {"id": eid, "img": None, "imgSrc": None, "imgKind": None, "icon": None, "iconSrc": None}
    out_preview = os.path.join(img_dir, f"{eid}.jpg")
    homepage = entry.get("homepage")
    repo = entry.get("repo")
    page, base = "", homepage
    if homepage and "github.com/" not in homepage:
        try:
            data, base, ctype = get(homepage, limit=3 * 1024 * 1024, accept="text/html")
            page = data.decode("utf-8", "replace")
        except Exception:
            page = ""

    # Preview image
    candidates = []
    og = meta_content(page, {"og:image", "og:image:url", "og:image:secure_url", "twitter:image", "twitter:image:src"}) if page else None
    if og:
        candidates.append((urllib.parse.urljoin(base, og), "og"))
    if repo:
        candidates.append((f"https://opengraph.githubassets.com/1/{repo}", "github"))
    for url, kind in candidates:
        try:
            data, _, _ = get(url, accept="image/*")
            raw = save_raw(entry_dir, "preview", data)
            if raw and pixel_width(raw) >= 300 and convert(raw, out_preview, "jpeg", 720, 68):
                result.update(img=f"img/{eid}.jpg", imgSrc=url, imgKind=kind)
                break
        except Exception:
            continue

    # Icon
    icon_candidates = []
    if page:
        icon_candidates += [urllib.parse.urljoin(base, h) for h in icon_links(page)[:3]]
    host = urllib.parse.urlparse(homepage).netloc if homepage else ""
    if host and host != "github.com":
        icon_candidates.append(f"https://www.google.com/s2/favicons?domain={host}&sz=128")
    if repo:
        icon_candidates.append(f"https://github.com/{repo.split('/')[0]}.png?size=128")
    for i, url in enumerate(icon_candidates):
        try:
            data, _, _ = get(url, limit=2 * 1024 * 1024, accept="image/*")
            raw = save_raw(entry_dir, f"icon{i}", data)
            if not raw or pixel_width(raw) < 48:
                continue
            out_icon = os.path.join(entry_dir, "icon-final.png")
            if convert(raw, out_icon, "png", 96):
                with open(out_icon, "rb") as f:
                    result["icon"] = "data:image/png;base64," + base64.b64encode(f.read()).decode()
                result["iconSrc"] = url
                break
        except Exception:
            continue
    return result


def main():
    with open(catalog_path) as f:
        entries = json.load(f)
    results = {}
    with cf.ThreadPoolExecutor(max_workers=16) as pool:
        for r in pool.map(process, entries):
            results[r["id"]] = r
    tag = os.path.splitext(os.path.basename(catalog_path))[0]
    with open(os.path.join(dl_dir, f"_results_{tag}.json"), "w") as f:
        json.dump(results, f)
    n = len(entries)
    print(f"entries={n} previews={sum(1 for r in results.values() if r['img'])} "
          f"icons={sum(1 for r in results.values() if r['icon'])}")


main()
