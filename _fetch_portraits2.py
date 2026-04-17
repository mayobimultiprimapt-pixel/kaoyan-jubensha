"""Retry failed portraits with different queries + add delays to avoid 429."""
import os, json, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFilter

ASSETS = r"C:\mq\故事模式\portraits"
UA = {"User-Agent": "mq-story-portraits-bot/1.0 (contact: noreply@example.com)"}

RETRY = {
    "chartist":        "Chartism engraving 19th century man",
    "kollwitz_weaver": "Kathe Kollwitz A Weavers Revolt",
    "canut_worker":    "Jacquard weaver Lyon",
    "marx_young":      "Karl Marx young man portrait",
}


def api(params):
    params["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    time.sleep(3)  # be polite
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)

def search(q):
    r = api({"action":"query","list":"search","srsearch":q+" filetype:bitmap","srnamespace":"6","srlimit":"5"})
    return [h["title"] for h in r.get("query",{}).get("search",[])]

def fileinfo(title):
    r = api({"action":"query","titles":title,"prop":"imageinfo","iiprop":"url|size|mime","iiurlwidth":"900"})
    for page in r.get("query",{}).get("pages",{}).values():
        ii = page.get("imageinfo")
        if ii: return ii[0]
    return None

def download(url, path):
    time.sleep(2)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        data = r.read()
    with open(path,"wb") as f: f.write(data)

def make_portrait(src, out, target_w=600, target_h=800):
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    scale = target_w / w
    nw, nh = target_w, int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    crop_h = min(nh, target_h)
    top = 0 if nh <= target_h else max(0, int(nh * 0.05))
    img = img.crop((0, top, target_w, top + crop_h))
    if img.height < target_h:
        canvas = Image.new("RGBA", (target_w, target_h), (0,0,0,0))
        canvas.paste(img, (0, 0))
        img = canvas
    mask = Image.new("L", (target_w, target_h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([int(target_w*.05), int(target_h*.03), target_w-int(target_w*.05), target_h-int(target_h*.03)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=18))
    img.putalpha(mask)
    img.save(out, "PNG", optimize=True)

for slug, q in RETRY.items():
    print(f"[{slug}] {q}")
    try:
        titles = search(q)
    except Exception as e:
        print(f"  search err: {e}"); continue
    if not titles:
        print(f"  no hits"); continue
    for t in titles[:3]:
        try:
            info = fileinfo(t)
            if not info or "image" not in info.get("mime",""):
                continue
            url = info.get("thumburl") or info.get("url")
            raw = os.path.join(ASSETS, f"_raw_{slug}.jpg")
            out = os.path.join(ASSETS, f"{slug}.png")
            download(url, raw)
            make_portrait(raw, out)
            try: os.remove(raw)
            except: pass
            sz = os.path.getsize(out)
            print(f"  ✓ {t} -> {sz//1024}KB")
            break
        except Exception as e:
            print(f"  try err: {e}")
    else:
        print(f"  ✗ all attempts failed for {slug}")

print("\nDIR:")
for f in sorted(os.listdir(ASSETS)):
    sz = os.path.getsize(os.path.join(ASSETS, f))
    print(f"  {f:30s} {sz//1024}KB")
