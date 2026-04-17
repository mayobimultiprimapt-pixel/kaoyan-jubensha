"""Extract ZONES + ROOMS from each subject's HTML into data/rooms.js.

Each subject's ZONES and ROOMS are pure-JSON-style objects (single-quoted
strings, no backticks, no function expressions). This script:

1. Locates `const ZONES = { ... };` and `const ROOMS = { ... };` in the HTML.
2. Balanced-bracket scan to find the closing `;`.
3. Writes both blocks into <subject>/data/rooms.js.
4. Removes the two declarations from the HTML (replaced by a one-line comment).
5. Injects <script src="data/rooms.js"></script> just before the main inline
   <script> (the one that starts with // ============ Web Audio ...).
6. Patches each subject's sw.js to cache data/rooms.js.

Run from C:\\mq\\. Idempotent (safe to re-run).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\mq")

SUBJECTS = [
    ("101剧本杀", "101剧本杀.html"),
    ("201剧本杀", "201剧本杀.html"),
    ("301剧本杀", "301剧本杀.html"),
    ("408剧本杀", "408剧本杀.html"),
]


def extract_const(src: str, name: str):
    """Return (start, end, text) of the `const NAME = {...};` or `[...];` block.

    Assumes no backtick/template literals inside the block. Handles nested {[(
    and single-/double-quoted string literals with backslash escapes, plus
    line/block comments. Raises if a backtick is encountered.
    """
    m = re.search(r"^const\s+" + re.escape(name) + r"\s*=\s*", src, re.M)
    if not m:
        raise ValueError(f"{name} not found")
    start = m.start()
    p = m.end()
    while p < len(src) and src[p] in " \t":
        p += 1
    if src[p] not in "{[":
        raise ValueError(f"{name} is not an object/array literal at {p}")
    open_pairs = {"{": "}", "[": "]", "(": ")"}
    close_to_open = {v: k for k, v in open_pairs.items()}
    stack = [src[p]]
    p += 1
    while p < len(src) and stack:
        c = src[p]
        if c == "\\":
            p += 2
            continue
        if c in ("'", '"'):
            quote = c
            p += 1
            while p < len(src) and src[p] != quote:
                if src[p] == "\\":
                    p += 2
                else:
                    p += 1
            p += 1
            continue
        if c == "`":
            raise ValueError(
                f"{name} contains a template literal at {p} — aborting to avoid mis-parse"
            )
        if c == "/" and p + 1 < len(src) and src[p + 1] == "/":
            while p < len(src) and src[p] != "\n":
                p += 1
            continue
        if c == "/" and p + 1 < len(src) and src[p + 1] == "*":
            end = src.find("*/", p + 2)
            p = end + 2 if end >= 0 else len(src)
            continue
        if c in open_pairs:
            stack.append(c)
        elif c in close_to_open:
            if not stack or stack[-1] != close_to_open[c]:
                raise ValueError(f"Unbalanced {c} at {p} in {name}")
            stack.pop()
        p += 1
    # p is just past the closing bracket
    while p < len(src) and src[p] in " \t":
        p += 1
    if p < len(src) and src[p] == ";":
        p += 1
    if p < len(src) and src[p] == "\n":
        p += 1
    return start, p, src[start:p]


def patch_sw(sw_path: Path):
    """Ensure './data/rooms.js' is in the ASSETS list of sw.js. Idempotent."""
    text = sw_path.read_text(encoding="utf8")
    if "'./data/rooms.js'" in text or '"./data/rooms.js"' in text:
        return False
    # naive: find last line in ASSETS list and append before it.
    # ASSETS pattern: `  './icon-512.png',\n];`
    new_text, n = re.subn(
        r"(  './icon-512\.png',\n)(\];)",
        r"\1  './data/rooms.js',\n\2",
        text,
    )
    if n != 1:
        print(f"  WARN: could not patch {sw_path} (pattern not found)")
        return False
    sw_path.write_text(new_text, encoding="utf8")
    return True


MAIN_SCRIPT_ANCHOR = "<script>\n// ============ Web Audio 音效引擎 ============"
EXTERNAL_TAG = '<script src="data/rooms.js"></script>\n'


def process(dir_name: str, html_name: str):
    html_path = ROOT / dir_name / html_name
    src = html_path.read_text(encoding="utf8")

    # Skip if already processed (data/rooms.js script tag already present).
    if EXTERNAL_TAG.strip() in src:
        print(f"[{dir_name}] already has external data script, skipping extraction")
        return

    zones = extract_const(src, "ZONES")
    rooms = extract_const(src, "ROOMS")

    data_dir = ROOT / dir_name / "data"
    data_dir.mkdir(exist_ok=True)
    data_path = data_dir / "rooms.js"
    header = (
        "// 数据块：ZONES（展区配置）+ ROOMS（题库内容）\n"
        "// 由 _extract_data.py 从主 HTML 抽取，修改题目无需动 HTML 主文件。\n"
        "// 注意：本文件在主 inline <script> 之前加载，必须最先定义这两个全局 const。\n\n"
    )
    body = zones[2].rstrip() + "\n\n" + rooms[2].rstrip() + "\n"
    data_path.write_text(header + body, encoding="utf8")
    print(f"  wrote {data_path} ({data_path.stat().st_size} bytes)")

    # Delete from back to front to keep earlier indices valid.
    ranges = sorted([(zones[0], zones[1], "ZONES"), (rooms[0], rooms[1], "ROOMS")], reverse=True)
    new_src = src
    for s, e, _name in ranges:
        new_src = new_src[:s] + new_src[e:]

    # Inject external script tag before main inline script.
    if MAIN_SCRIPT_ANCHOR not in new_src:
        raise RuntimeError(f"[{dir_name}] main script anchor not found")
    new_src = new_src.replace(MAIN_SCRIPT_ANCHOR, EXTERNAL_TAG + MAIN_SCRIPT_ANCHOR, 1)

    html_path.write_text(new_src, encoding="utf8")
    print(f"  patched {html_path}")

    sw_path = ROOT / dir_name / "sw.js"
    if patch_sw(sw_path):
        print(f"  patched {sw_path} (added data/rooms.js to cache)")


def main():
    for d, h in SUBJECTS:
        print(f"[{d}]")
        process(d, h)
    print("Done.")


if __name__ == "__main__":
    main()
