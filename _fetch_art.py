"""Fetch CC0 / Public-Domain historical art from Wikimedia Commons for
story-mode scene backgrounds. 所有抓下来的图都来自 Commons（绝大多数
19 世纪作品是 Public Domain）。

失败也不致命：CSS 还有渐变 fallback。
"""
import os, json, urllib.parse, urllib.request, urllib.error, sys

ASSETS_DIR = r"C:\mq\故事模式\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

UA = {"User-Agent": "mq-story-mode-bot/1.0 (https://github.com/mayobimultiprimapt-pixel/kaoyan-jubensha)"}

# scene → search query（优先选我记得的著名画作）
QUERIES = {
    "lyon-street":    "Révolte des canuts Lyon 1831",
    "silk-workshop":  "Jacquard loom 19th century",
    "uprising":       "Canuts insurrection 1834 Lyon",
    "london-rain":    "Chartist meeting Kennington Common 1848",
    "silesia-night":  "Käthe Kollwitz Weavers Revolt",
    "paris-study":    "Karl Marx portrait 1875",
}


def api(params):
    params["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def find_candidates(query, limit=6):
    r = api({
        "action": "query",
        "list": "search",
        "srsearch": query + " filetype:bitmap",
        "srnamespace": "6",
        "srlimit": str(limit),
    })
    return [h["title"] for h in r.get("query", {}).get("search", [])]


def get_file_info(title, width=1600):
    r = api({
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": str(width),
    })
    pages = r.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        ii = page.get("imageinfo")
        if ii:
            return ii[0]
    return None


def download(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


results = {}
for scene, query in QUERIES.items():
    print(f"\n[{scene}] query: {query}")
    try:
        titles = find_candidates(query)
    except Exception as e:
        print(f"  ! search failed: {e}")
        continue
    if not titles:
        print(f"  no results")
        continue
    for t in titles[:5]:
        print(f"  try: {t}")
        try:
            info = get_file_info(t)
        except Exception as e:
            print(f"    info failed: {e}")
            continue
        if not info:
            continue
        img_url = info.get("thumburl") or info.get("url")
        mime = info.get("mime", "")
        if "image" not in mime:
            continue
        ext = "jpg" if "jpeg" in mime else ("png" if "png" in mime else mime.rsplit("/", 1)[-1])
        local = os.path.join(ASSETS_DIR, f"{scene}.{ext}")
        try:
            size = download(img_url, local)
            print(f"    ✓ {size // 1024}KB -> {os.path.basename(local)}")
            results[scene] = f"{scene}.{ext}"
            break
        except Exception as e:
            print(f"    download failed: {e}")
    else:
        print(f"  ✗ no image downloaded for {scene}")

print("\n" + "="*60)
print("RESULTS:")
for k, v in results.items():
    p = os.path.join(ASSETS_DIR, v)
    sz = os.path.getsize(p) if os.path.exists(p) else 0
    print(f"  {k:20s} -> {v} ({sz // 1024}KB)")
if len(results) < len(QUERIES):
    missing = set(QUERIES) - set(results)
    print(f"\n  未抓到 {len(missing)} 个: {', '.join(missing)}")
