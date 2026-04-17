"""Sync shared/game.js to each subject's data/game.js, strip inline save +
sidebar blocks from HTML (keeping a one-line `const SAVE_SUBJECT = ...`
marker for subject identity).

Original inline structure in each subject HTML:

    // ============ 存档 ============
    const SAVE_SUBJECT='101';
    const SAVE_KEY='exam_101_progress';
    const SAVE_LEGACY_KEY='101_rpg_save';
    const SAVE_VERSION=2;
    function _patchLoadedState(){...}
    function _writeSave(){...}
    function hasSave(){...}
    function saveGame(silent){...}
    function loadGame(){...}
    function resetGame(){...}

    ... (other code) ...

    // ============ Sidebar 增量渲染 (首次构建骨架，后续只 diff 变化节点) ============
    const _sb={...};
    const TOTAL_BADGES=Object.keys(ZONES).reduce(...);
    const NB_EMPTY_HTML=...;
    function _buildSidebarSkeleton(){...}
    function renderSidebar(){...}

After migration: save block shrinks to one-line marker, sidebar block removed.
All behavior is delegated to shared/game.js (as data/game.js).
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\mq")
SHARED_GAME = ROOT / "shared" / "game.js"

SUBJECTS = [
    ("101剧本杀", "101剧本杀.html"),
    ("201剧本杀", "201剧本杀.html"),
    ("301剧本杀", "301剧本杀.html"),
    ("408剧本杀", "408剧本杀.html"),
]

INJECT_ANCHOR = '<script src="data/engine.js"></script>'
INJECT_TAG = '<script src="data/game.js"></script>'


def _scan_balanced(src: str, open_idx: int) -> int:
    """Return index just past the matching '}' for '{' at open_idx.
    Handles nested {}, string literals (single/double), and line comments.
    """
    p = open_idx + 1
    depth = 1
    while p < len(src) and depth:
        c = src[p]
        if c == "\\":
            p += 2
            continue
        if c in ("'", '"'):
            q = c
            p += 1
            while p < len(src) and src[p] != q:
                if src[p] == "\\":
                    p += 2
                else:
                    p += 1
            p += 1
            continue
        if c == "`":
            p += 1
            while p < len(src) and src[p] != "`":
                if src[p] == "\\":
                    p += 2
                elif src[p : p + 2] == "${":
                    # template expression: recursively handle braces
                    p += 2
                    d = 1
                    while p < len(src) and d:
                        if src[p] == "{":
                            d += 1
                        elif src[p] == "}":
                            d -= 1
                        p += 1
                else:
                    p += 1
            p += 1
            continue
        if c == "/" and p + 1 < len(src):
            if src[p + 1] == "/":
                while p < len(src) and src[p] != "\n":
                    p += 1
                continue
            if src[p + 1] == "*":
                end = src.find("*/", p + 2)
                p = end + 2 if end >= 0 else len(src)
                continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        p += 1
    return p


def extract_save_block(html: str):
    """Return (start, end, subject) of the original save block.
    Start: `// ============ 存档 ============`
    End: just after `resetGame` closing brace (plus trailing blank line).
    """
    start_marker = "// ============ 存档 ============"
    s = html.index(start_marker)
    # Find reseGame definition
    reset_at = html.index("function resetGame()", s)
    open_brace = html.index("{", reset_at)
    end = _scan_balanced(html, open_brace)
    # Consume trailing newline(s) + blank line
    while end < len(html) and html[end] in "\n ":
        end += 1
    # Extract SAVE_SUBJECT value
    m = re.search(r"const SAVE_SUBJECT\s*=\s*'([^']+)'", html[s:end])
    if not m:
        raise RuntimeError("SAVE_SUBJECT not found in save block")
    return s, end, m.group(1)


def extract_sidebar_block(html: str):
    """Return (start, end) of sidebar block."""
    start_marker = "// ============ Sidebar 增量渲染"
    s = html.index(start_marker)
    render_at = html.index("function renderSidebar()", s)
    open_brace = html.index("{", render_at)
    end = _scan_balanced(html, open_brace)
    while end < len(html) and html[end] in "\n ":
        end += 1
    return s, end


def patch_sw(sw_path: Path):
    text = sw_path.read_text(encoding="utf8")
    changed = False
    if "'./data/game.js'" not in text:
        new_text, n = re.subn(
            r"(  './data/engine\.js',\n)",
            r"\1  './data/game.js',\n",
            text,
            count=1,
        )
        if n == 1:
            text = new_text
            changed = True
    new_text, n = re.subn(
        r"const CACHE = 'exam-(101|201|301|408)-v(\d+)';",
        lambda m: f"const CACHE = 'exam-{m.group(1)}-v{int(m.group(2)) + 1}';",
        text,
        count=1,
    )
    if n == 1 and new_text != text:
        text = new_text
        changed = True
    if changed:
        sw_path.write_text(text, encoding="utf8")
        print(f"  {sw_path.name}: patched")
    else:
        print(f"  {sw_path.name}: no change")


def process(dir_name: str, html_name: str):
    target_dir = ROOT / dir_name
    html_path = target_dir / html_name
    html = html_path.read_text(encoding="utf8")

    if INJECT_TAG in html:
        print(f"  {html_name}: already migrated, skipping")
        return

    # Copy game.js
    data_dir = target_dir / "data"
    data_dir.mkdir(exist_ok=True)
    shutil.copy2(SHARED_GAME, data_dir / "game.js")
    print(f"  copied -> {data_dir / 'game.js'}")

    # Extract and replace save block
    s1, e1, subject = extract_save_block(html)
    save_replacement = (
        f"// ============ 存档标识 (behaviour in data/game.js) ============\n"
        f"const SAVE_SUBJECT='{subject}';\n\n"
    )
    # Extract sidebar block
    s2, e2 = extract_sidebar_block(html)
    sidebar_replacement = ""

    # Apply edits from highest offset first so positions stay valid
    if s2 > s1:
        new_html = html[:s2] + sidebar_replacement + html[e2:]
        # Now update save block in the (now shorter) new_html
        # but positions s1, e1 from original html are still valid for the slice
        # before s2, which was not touched. Safe.
        new_html = new_html[:s1] + save_replacement + new_html[e1:]
    else:
        new_html = html[:s1] + save_replacement + html[e1:]
        # Sidebar offsets shift; recompute
        s2_new, e2_new = extract_sidebar_block(new_html)
        new_html = new_html[:s2_new] + sidebar_replacement + new_html[e2_new:]

    # Inject script tag
    new_html = new_html.replace(
        INJECT_ANCHOR, INJECT_ANCHOR + "\n" + INJECT_TAG, 1
    )

    html_path.write_text(new_html, encoding="utf8")
    save_trim = e1 - s1 - len(save_replacement)
    sidebar_trim = e2 - s2
    print(
        f"  {html_name}: save block trimmed {save_trim}B, "
        f"sidebar block removed {sidebar_trim}B"
    )
    patch_sw(target_dir / "sw.js")


def main():
    if not SHARED_GAME.exists():
        raise SystemExit(f"Source {SHARED_GAME} missing")
    for d, h in SUBJECTS:
        print(f"[{d}]")
        process(d, h)
    print("Done.")


if __name__ == "__main__":
    main()
