"""Generate PNG icons (192 + 512) for the 5 jubensha PWAs.

Layout mirrors the original SVG: dark radial bg + gold ring + bronze accent
ring + large bronze code + subtitle in theme color + "ARCHIVE" tag.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(r"C:\mq")

ICONS = [
    {
        "dir": "考研剧本杀合集",
        "code": "考研",
        "sub": "归档处",
        "accent": (106, 42, 138),   # #6a2a8a purple
    },
    {
        "dir": "101剧本杀",
        "code": "101",
        "sub": "藏心·求真",
        "accent": (139, 0, 0),      # #8b0000 crimson
    },
    {
        "dir": "201剧本杀",
        "code": "201",
        "sub": "漪兰·求真",
        "accent": (192, 112, 48),   # #c07030 amber
    },
    {
        "dir": "301剧本杀",
        "code": "301",
        "sub": "若虚·求真",
        "accent": (42, 90, 170),    # #2a5aaa blue
    },
    {
        "dir": "408剧本杀",
        "code": "408",
        "sub": "溯涟·求真",
        "accent": (42, 138, 74),    # #2a8a4a green
    },
]

GOLD = (212, 175, 55)
DIM_GOLD = (138, 122, 90)
BG_CENTER = (26, 10, 10)
BG_EDGE = (5, 5, 5)


def find_cjk_font():
    for name in [
        "C:/Windows/Fonts/STKAITI.TTF",
        "C:/Windows/Fonts/simkai.ttf",
        "C:/Windows/Fonts/STSONG.TTF",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ]:
        if Path(name).exists():
            return name
    raise RuntimeError("no CJK font found")


def find_latin_font():
    for name in [
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        if Path(name).exists():
            return name
    return find_cjk_font()


CJK = find_cjk_font()
LATIN = find_latin_font()


def radial_bg(size):
    img = Image.new("RGB", (size, size), BG_EDGE)
    px = img.load()
    cx, cy = size / 2, size * 0.35
    maxd = size * 0.70
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5 / maxd
            if d > 1:
                d = 1
            px[x, y] = tuple(
                int(BG_CENTER[i] * (1 - d) + BG_EDGE[i] * d) for i in range(3)
            )
    return img


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def draw_icon(size, code, sub, accent):
    s = size
    bg = radial_bg(s)
    mask = rounded_mask(s, int(s * 0.1875))
    out = Image.new("RGB", (s, s), BG_EDGE)
    out.paste(bg, (0, 0), mask)

    d = ImageDraw.Draw(out)
    cx, cy = s / 2, s / 2

    # outer gold ring
    r1 = int(s * 196 / 512)
    d.ellipse(
        [cx - r1, cy - r1, cx + r1, cy + r1],
        outline=tuple(int(c * 0.8) for c in GOLD),
        width=max(3, int(s * 5 / 512)),
    )
    # inner accent ring
    r2 = int(s * 168 / 512)
    faded_accent = tuple(int(c * 0.6 + 20) for c in accent)
    d.ellipse(
        [cx - r2, cy - r2, cx + r2, cy + r2],
        outline=faded_accent,
        width=max(2, int(s * 2 / 512)),
    )

    # code (large, gold, bold CJK font)
    code_font_size = int(s * 130 / 512)
    cf = ImageFont.truetype(CJK, code_font_size)
    bbox = d.textbbox((0, 0), code, font=cf)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(
        (cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1] - int(s * 14 / 512)),
        code,
        font=cf,
        fill=GOLD,
    )

    # subtitle (accent color, smaller CJK)
    sub_size = int(s * 38 / 512)
    sf = ImageFont.truetype(CJK, sub_size)
    bbox = d.textbbox((0, 0), sub, font=sf)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(
        (cx - tw / 2 - bbox[0], int(s * 322 / 512) - th / 2 - bbox[1]),
        sub,
        font=sf,
        fill=accent,
    )

    # ARCHIVE (latin, dim)
    arc_size = int(s * 18 / 512)
    af = ImageFont.truetype(LATIN, arc_size)
    archive = "A R C H I V E"
    bbox = d.textbbox((0, 0), archive, font=af)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(
        (cx - tw / 2 - bbox[0], int(s * 380 / 512) - th / 2 - bbox[1]),
        archive,
        font=af,
        fill=DIM_GOLD,
    )

    return out


def main():
    for cfg in ICONS:
        target = ROOT / cfg["dir"]
        for size in (192, 512):
            img = draw_icon(size, cfg["code"], cfg["sub"], cfg["accent"])
            path = target / f"icon-{size}.png"
            img.save(path, "PNG", optimize=True)
            print(f"  wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
