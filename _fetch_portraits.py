"""Fetch historical portraits from Wikimedia Commons, then cut out an oval
head-shoulder crop with feathered edges and gold glow — yielding "classical
oil-painting立绘" for story mode characters.
"""
import os, json, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFilter

ASSETS = r"C:\mq\故事模式\portraits"
os.makedirs(ASSETS, exist_ok=True)
UA = {"User-Agent": "mq-story-portraits-bot/1.0"}

# slug → search query
PORTRAITS = {
    "marx_young": "Karl Marx 1840s young",
    "marx_old":   "Karl Marx 1875 Mayall portrait",
    "engels":     "Friedrich Engels portrait 1860",
    "chartist":   "Feargus O'Connor Chartist portrait",
    "kollwitz_weaver": "Käthe Kollwitz Weavers March",
    "canut_worker":    "Canut Lyon silk weaver 19th century",
}


def api(params):
    params["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def search(query, limit=5):
    r = api({"action":"query","list":"search","srsearch":query+" filetype:bitmap","srnamespace":"6","srlimit":str(limit)})
    return [h["title"] for h in r.get("query",{}).get("search",[])]


def fileinfo(title, w=900):
    r = api({"action":"query","titles":title,"prop":"imageinfo","iiprop":"url|size|mime","iiurlwidth":str(w)})
    for page in r.get("query",{}).get("pages",{}).values():
        ii = page.get("imageinfo")
        if ii: return ii[0]
    return None


def download(url, path):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        data = r.read()
    with open(path,"wb") as f: f.write(data)
    return len(data)


def make_portrait(src_path, out_path, target_w=600, target_h=800):
    """Crop center-top (head-shoulder), apply oval mask + feather + gold ring."""
    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    # Scale so width matches target, keep aspect
    scale = target_w / w
    nw, nh = target_w, int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    # Crop top portion (portraits usually have face near top 1/3)
    crop_h = min(nh, target_h)
    top = 0 if nh <= target_h else max(0, int(nh * 0.05))  # skip top 5% padding
    img = img.crop((0, top, target_w, top + crop_h))
    # Pad bottom if shorter than target
    if img.height < target_h:
        canvas = Image.new("RGBA", (target_w, target_h), (0,0,0,0))
        canvas.paste(img, (0, 0))
        img = canvas
    # Build feathered oval mask
    mask = Image.new("L", (target_w, target_h), 0)
    md = ImageDraw.Draw(mask)
    # Oval slightly inset
    pad_x = int(target_w * 0.05)
    pad_y = int(target_h * 0.03)
    md.ellipse([pad_x, pad_y, target_w - pad_x, target_h - pad_y], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=18))
    # Apply mask to alpha
    r, g, b, a = img.split() if img.mode == "RGBA" else (*img.convert("RGB").split(), None)
    img.putalpha(mask)
    img.save(out_path, "PNG", optimize=True)


results = {}
for slug, query in PORTRAITS.items():
    print(f"[{slug}] {query}")
    try:
        titles = search(query)
    except Exception as e:
        print(f"  search err: {e}"); continue
    if not titles:
        print(f"  no hits"); continue
    for t in titles[:4]:
        info = fileinfo(t)
        if not info or "image" not in info.get("mime",""):
            continue
        url = info.get("thumburl") or info.get("url")
        raw_path = os.path.join(ASSETS, f"_raw_{slug}.jpg")
        out_path = os.path.join(ASSETS, f"{slug}.png")
        try:
            download(url, raw_path)
            make_portrait(raw_path, out_path)
            os.remove(raw_path)
            sz = os.path.getsize(out_path)
            print(f"  ✓ {t} -> {slug}.png ({sz//1024}KB)")
            results[slug] = f"{slug}.png"
            break
        except Exception as e:
            print(f"  fail: {e}")
    else:
        print(f"  ✗ no portrait for {slug}")

print("\nFINAL:")
for k, v in results.items():
    print(f"  {k} -> {v}")
