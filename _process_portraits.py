"""处理用户用即梦生成的 4 张立绘：
1. rembg 抠透明背景
2. 裁到人物边界
3. 统一输出到 故事模式/portraits/<slug>.png
"""
import os, shutil
from PIL import Image
from rembg import remove, new_session

SRC_DIR = r"C:\Users\Administrator\Desktop\新建文件夹 (4)"
DST_DIR = r"C:\mq\故事模式\portraits"
os.makedirs(DST_DIR, exist_ok=True)

# 源文件 hash → 角色 slug（按生成顺序和内容对应）
MAPPING = {
    "7cbf368993fe04d2c94b3a5a6e979ee7.jpg": "marx_young",
    "9921d86e7461da22467f061b5a334b3c.jpg": "lyon_weaver",
    "b39c950994c4ff4c5bba90703c48e90a.jpg": "chartist",
    "81b0510a08dc0ff6ca00273f848b7ddb.jpg": "silesia_weaver",
}

# u2net 是默认模型，效果最好；u2netp 更轻
session = new_session("u2net")

def trim_transparent(img):
    """裁到非透明边界，上下左右各留 10px padding。"""
    bbox = img.getbbox()
    if not bbox: return img
    l, t, r, b = bbox
    w, h = img.size
    pad = 10
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(w, r + pad), min(h, b + pad)
    return img.crop((l, t, r, b))

def process_one(src, slug):
    print(f"[{slug}] 处理: {os.path.basename(src)}")
    with open(src, "rb") as f:
        data = f.read()
    cut = remove(data, session=session)
    # cut 是 PNG bytes
    import io
    img = Image.open(io.BytesIO(cut)).convert("RGBA")
    img = trim_transparent(img)
    # 统一最大尺寸：max_w 640, max_h 900
    max_w, max_h = 640, 900
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    out = os.path.join(DST_DIR, f"{slug}.png")
    img.save(out, "PNG", optimize=True)
    sz = os.path.getsize(out)
    print(f"  ✓ {img.size} -> {slug}.png ({sz // 1024}KB)")
    return slug

for fname, slug in MAPPING.items():
    src = os.path.join(SRC_DIR, fname)
    if os.path.exists(src):
        try:
            process_one(src, slug)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    else:
        print(f"  ✗ {slug}: 源文件不存在 {src}")

print("\n最终 portraits/:")
for f in sorted(os.listdir(DST_DIR)):
    sz = os.path.getsize(os.path.join(DST_DIR, f))
    print(f"  {f:30s} {sz // 1024}KB")
