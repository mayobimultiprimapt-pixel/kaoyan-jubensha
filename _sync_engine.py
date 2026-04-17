"""Sync shared/engine.js to each subject's data/engine.js and strip inline
audio/BGM/util functions from the HTML (leaving BGM_TRACKS in place).

Layout in the original HTML:

    ... <script>
    // ============ Web Audio 音效引擎 ============
    let ac=null, ...                                 <-- SEG_A
    ...
    function playTrack(...) { ... }                  <-- end SEG_A
    const BGM_TRACKS = { ... };                      <-- keep in HTML
    function startBgmTrack(...) { ... }              <-- SEG_B
    ...
    function toggleBgm() { ... }                     <-- end SEG_B
    // ============ 游戏状态 ============
    let state = { ... };
    ... (FOLLOWUPS, PROLOGUE, etc)
    function showToast(msg){ ... }                   <-- SEG_C
    function normalize(s){ ... }
    function checkFill(...){ ... }                   <-- end SEG_C
    // ============ 答案判定 ============
    ...

SEG_A, SEG_B, SEG_C are contained verbatim in shared/engine.js (which omits
BGM_TRACKS and the state/followups/etc that sit between the segments).
This script splits shared/engine.js at the known anchors to recover SEG_A/B/C,
then does exact string replace on each subject HTML.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\mq")
SHARED_ENGINE = ROOT / "shared" / "engine.js"

SUBJECTS = [
    ("101剧本杀", "101剧本杀.html"),
    ("201剧本杀", "201剧本杀.html"),
    ("301剧本杀", "301剧本杀.html"),
    ("408剧本杀", "408剧本杀.html"),
]


def split_engine(engine_src: str):
    """Return (seg_a, seg_b, seg_c) corresponding to the three inline blocks
    that appear in each subject HTML. These are verbatim substrings of
    engine.js (minus the block comment header).
    """
    # Drop the leading /* ... */ block comment.
    body = re.sub(r"^/\*.*?\*/\s*", "", engine_src, count=1, flags=re.S)

    # Find anchors.
    a_start = body.index("// ============ Web Audio 音效引擎 ============")
    b_start = body.index("function startBgmTrack(trackId){")
    c_start = body.index("// ============ 通用工具 ============")
    # SEG_A ends just before startBgmTrack — strip the preceding comment/blank.
    # In HTML SEG_A ends at the closing '}' of playTrack; in engine.js,
    # the same character follows (the "多轨 BGM 引擎" comment sits mid-SEG_A).
    # We need SEG_A in HTML to end right before BGM_TRACKS, i.e. end of playTrack.
    # The segment in engine.js from a_start to b_start includes playTrack and
    # ends with "}\n". We trim trailing whitespace.
    seg_a = body[a_start:b_start].rstrip() + "\n"
    # SEG_B starts with startBgmTrack and ends before the "// 通用工具" marker.
    seg_b = body[b_start:c_start].rstrip() + "\n"
    # SEG_C is from "// ============ 通用工具 ============" to end, but the
    # original HTML did NOT have that comment line — it had "// ============ 答案判定 ============"
    # between showToast and normalize/checkFill. So drop the comment and keep
    # just the three function definitions.
    seg_c_body = body[c_start:]
    # Strip the "// ============ 通用工具 ============" line.
    seg_c_body = re.sub(
        r"^// ============ 通用工具 ============\n", "", seg_c_body, count=1
    )
    seg_c = seg_c_body.rstrip() + "\n"
    return seg_a, seg_b, seg_c


# ---- HTML-side anchors (these MUST appear verbatim in each subject HTML) ----

HTML_SEG_A_START = "// ============ Web Audio 音效引擎 ============\n"
# HTML_SEG_A ends at:   "}\n" of playTrack, followed by blank + "const BGM_TRACKS=..."
HTML_BGM_TRACKS_MARKER = "const BGM_TRACKS={"
HTML_SEG_B_START = "function startBgmTrack(trackId){\n"
# HTML_SEG_B ends at the toggleBgm '}' followed by blank + next section comment.
HTML_SEG_C_START = "function showToast(msg){\n"
# HTML_SEG_C ends at checkFill '}' followed by blank + "// ============ 答案判定..." or similar.
# In current HTML, the "// ============ 答案判定 ============" comment sits *between*
# showToast and normalize (on line 771). We want SEG_C to cover all three functions
# but skip that comment line.


def extract_html_seg_a(html: str) -> str:
    """Return the substring covering 'Web Audio 音效引擎' down through playTrack,
    up to (but not including) the blank line before 'const BGM_TRACKS='.
    """
    i = html.index(HTML_SEG_A_START)
    j = html.index(HTML_BGM_TRACKS_MARKER, i)
    # Include content up to BGM_TRACKS marker. Trim trailing whitespace/newlines.
    return html[i:j].rstrip() + "\n"


def extract_html_seg_b(html: str) -> str:
    """Return startBgmTrack through toggleBgm."""
    i = html.index(HTML_SEG_B_START)
    # Find the next "// ============" section marker after toggleBgm.
    m = re.search(r"\n// ============", html[i:])
    if not m:
        raise RuntimeError("cannot find end of SEG_B")
    return html[i : i + m.start()].rstrip() + "\n"


def extract_html_seg_c(html: str) -> str:
    """Return showToast + normalize + checkFill, skipping intermediate section
    comment lines."""
    i = html.index(HTML_SEG_C_START)
    # normalize starts after showToast. In current HTML, there's a
    # "// ============ 答案判定 ============" comment line between them.
    # Find end: checkFill ends with '}' on its own line, followed by blank + next section.
    # Look for the next "\n\n// ============" after showToast.
    after = html[i:]
    # Heuristic: find "function checkFill(" then its closing.
    k = after.index("function checkFill(")
    # Find the '}' that closes checkFill — scan forward until matching brace at depth 0.
    p = after.index("{", k)
    depth = 1
    p += 1
    while p < len(after) and depth:
        c = after[p]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "'" or c == '"':
            q = c
            p += 1
            while p < len(after) and after[p] != q:
                if after[p] == "\\":
                    p += 2
                else:
                    p += 1
        elif c == "/" and p + 1 < len(after):
            if after[p + 1] == "/":
                # line comment
                while p < len(after) and after[p] != "\n":
                    p += 1
                continue
            if after[p + 1] == "*":
                end = after.find("*/", p + 2)
                p = end + 2 if end >= 0 else len(after)
                continue
        p += 1
    # p is just past closing '}' of checkFill
    return after[: p + 1].rstrip() + "\n"


INJECT_ANCHOR = '<script src="data/rooms.js"></script>'
INJECT_TAG = '<script src="data/engine.js"></script>'


def patch_sw(sw_path: Path):
    text = sw_path.read_text(encoding="utf8")
    changed = False
    if "'./data/engine.js'" not in text:
        new_text, n = re.subn(
            r"(  './data/rooms\.js',\n)",
            r"\1  './data/engine.js',\n",
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


def process_subject(dir_name: str, html_name: str):
    target_dir = ROOT / dir_name
    html_path = target_dir / html_name
    html = html_path.read_text(encoding="utf8")

    # Skip if already migrated.
    if INJECT_TAG in html:
        print(f"  {html_name}: already has engine.js reference, skipping")
        return

    # Copy engine.js into data/
    data_dir = target_dir / "data"
    data_dir.mkdir(exist_ok=True)
    shutil.copy2(SHARED_ENGINE, data_dir / "engine.js")
    print(f"  copied engine.js -> {data_dir / 'engine.js'}")

    seg_a_html = extract_html_seg_a(html)
    seg_b_html = extract_html_seg_b(html)
    seg_c_html = extract_html_seg_c(html)

    # Sanity: segments must not overlap BGM_TRACKS *definition* or state *definition*.
    # (SEG_B legitimately *references* BGM_TRACKS and state.stage via applyBgm/toggleBgm.)
    for seg in (seg_a_html, seg_b_html, seg_c_html):
        assert "const BGM_TRACKS=" not in seg, "BGM_TRACKS definition leaked into segment"
        assert "let state=" not in seg, "state definition leaked into segment"

    # Remove the three segments in order (largest offset first to preserve indices).
    positions = [
        (html.index(seg_a_html), seg_a_html),
        (html.index(seg_b_html), seg_b_html),
        (html.index(seg_c_html), seg_c_html),
    ]
    positions.sort(reverse=True)
    new_html = html
    for _pos, seg in positions:
        new_html = new_html.replace(seg, "", 1)

    # Inject engine.js script tag after rooms.js script tag.
    new_html = new_html.replace(
        INJECT_ANCHOR, INJECT_ANCHOR + "\n" + INJECT_TAG, 1
    )

    html_path.write_text(new_html, encoding="utf8")
    print(f"  {html_name}: stripped 3 segments, injected engine.js tag")

    patch_sw(target_dir / "sw.js")


def main():
    if not SHARED_ENGINE.exists():
        raise SystemExit(f"Source {SHARED_ENGINE} missing — create it first.")

    # Pre-split shared/engine.js as sanity check (we don't actually use
    # the split halves directly; HTML extraction relies on HTML anchors).
    seg_a, seg_b, seg_c = split_engine(SHARED_ENGINE.read_text(encoding="utf8"))
    print(
        f"shared/engine.js split OK: "
        f"A={len(seg_a)}B, B={len(seg_b)}B, C={len(seg_c)}B"
    )

    for d, h in SUBJECTS:
        print(f"[{d}]")
        process_subject(d, h)
    print("Done.")


if __name__ == "__main__":
    main()
