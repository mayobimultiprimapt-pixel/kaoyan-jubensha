"""Sync shared/boot.js to each subject's data/boot.js and patch HTML + sw.js.

- Copies shared/boot.js -> {subject}/data/boot.js (5 copies: hub + 4 exams).
- Removes the three equivalent inline blocks from each HTML (error boundary,
  keyboard delegate, SW register).
- Inserts <script src="data/boot.js"></script> after the last apple-touch-icon
  link in <head>.
- Patches sw.js: adds data/boot.js to ASSETS, bumps CACHE version.

Idempotent: re-running is a no-op if boot.js is already linked.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\mq")
SHARED_BOOT = ROOT / "shared" / "boot.js"

# (dir_name, html_name, has_kbd_delegate_block)
TARGETS = [
    ("考研剧本杀合集", "index.html", False),
    ("101剧本杀", "101剧本杀.html", True),
    ("201剧本杀", "201剧本杀.html", True),
    ("301剧本杀", "301剧本杀.html", True),
    ("408剧本杀", "408剧本杀.html", True),
]

ERROR_BOUNDARY_BLOCK = """<script>
(function(){
  function show(msg){try{
    var d=document.getElementById('_err_toast');
    if(!d){d=document.createElement('div');d.id='_err_toast';
      d.style.cssText='position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:rgba(139,0,0,.95);color:#fff5e0;padding:10px 18px;border-radius:4px;z-index:99999;font-size:13px;letter-spacing:1px;max-width:92vw;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.5);font-family:inherit';
      (document.body||document.documentElement).appendChild(d);
    }
    d.textContent='⚠ 发生错误：'+msg+'（详情见 Console）';
    clearTimeout(d._t);d._t=setTimeout(function(){try{d.remove()}catch(_){}},7000);
  }catch(_){}}
  window.addEventListener('error',function(e){console.error('[error]',e);var loc=e.filename?' @ '+String(e.filename).split('/').pop()+':'+e.lineno:'';show((e.message||'未知错误')+loc)});
  window.addEventListener('unhandledrejection',function(e){console.error('[promise]',e.reason);show(String((e.reason&&(e.reason.message||e.reason))||'Promise 被拒'))});
})();
</script>
"""

KBD_BLOCK = """// ============ 键盘无障碍 ============
document.addEventListener('keydown',function(e){
    if((e.key==='Enter'||e.key===' ')&&e.target&&e.target.matches&&e.target.matches('[data-kbd]')){
        e.preventDefault();e.target.click();
    }
});

"""

SW_REG_BLOCK = """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  });
}
</script>
"""

APPLE_TOUCH_ANCHOR = '<link rel="apple-touch-icon" sizes="512x512" href="icon-512.png">'
BOOT_LINK = '<script src="data/boot.js"></script>'


def patch_html(path: Path, has_kbd: bool):
    src = path.read_text(encoding="utf8")
    if BOOT_LINK in src:
        print(f"  {path.name}: already patched, skipping")
        return
    changes = []
    # Replace error boundary with boot.js link (placed at same spot, which
    # is right after the apple-touch-icon line).
    if ERROR_BOUNDARY_BLOCK not in src:
        raise RuntimeError(f"{path}: error boundary block not found")
    src = src.replace(ERROR_BOUNDARY_BLOCK, BOOT_LINK + "\n", 1)
    changes.append("error-boundary->boot.js")
    # Remove keyboard delegate block (4 exam HTMLs).
    if has_kbd:
        if KBD_BLOCK not in src:
            raise RuntimeError(f"{path}: kbd block not found")
        src = src.replace(KBD_BLOCK, "", 1)
        changes.append("kbd delegate")
    # Remove SW register block.
    if SW_REG_BLOCK not in src:
        raise RuntimeError(f"{path}: sw register block not found")
    src = src.replace(SW_REG_BLOCK, "", 1)
    changes.append("sw register")
    path.write_text(src, encoding="utf8")
    print(f"  {path.name}: removed [{', '.join(changes)}]")


def patch_sw(sw_path: Path):
    text = sw_path.read_text(encoding="utf8")
    changed = False
    if "'./data/boot.js'" not in text:
        new_text, n = re.subn(
            r"(  './icon-512\.png',\n)",
            r"\1  './data/boot.js',\n",
            text,
            count=1,
        )
        if n == 1:
            text = new_text
            changed = True
    # Bump cache version v2 -> v3, or v1 -> v2 (for hub which started at v1)
    new_text, n = re.subn(
        r"const CACHE = 'exam-(hub|101|201|301|408)-v(\d+)';",
        lambda m: f"const CACHE = 'exam-{m.group(1)}-v{int(m.group(2)) + 1}';",
        text,
        count=1,
    )
    if n == 1 and new_text != text:
        text = new_text
        changed = True
    if changed:
        sw_path.write_text(text, encoding="utf8")
        print(f"  {sw_path.name}: patched (boot.js + cache bump)")
    else:
        print(f"  {sw_path.name}: no change needed")


def main():
    if not SHARED_BOOT.exists():
        raise RuntimeError(f"Source {SHARED_BOOT} missing. Create it first.")
    for dir_name, html_name, has_kbd in TARGETS:
        target_dir = ROOT / dir_name
        data_dir = target_dir / "data"
        data_dir.mkdir(exist_ok=True)
        shutil.copy2(SHARED_BOOT, data_dir / "boot.js")
        print(f"[{dir_name}]")
        print(f"  copied boot.js -> {data_dir / 'boot.js'}")
        patch_html(target_dir / html_name, has_kbd)
        patch_sw(target_dir / "sw.js")
    print("Done.")


if __name__ == "__main__":
    main()
