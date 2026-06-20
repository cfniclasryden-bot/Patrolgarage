#!/usr/bin/env python3
"""patch_menu.py — fix the mobile hamburger menu across all pages.

The served pages have a hamburger button + the `nav { display:none }` mobile media
query, but NO `nav.open` reveal CSS and NO toggle JS (they don't load js/main.js or
css/style.css). This injects both, inline, using each page's own design variables.

Idempotent: skips any file already carrying the marker. Whitespace-tolerant regex
anchor so it handles BOTH the pretty-printed pages and the older fully-minified
blog pages (e.g. `nav,.header-cta{display:none;}`).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKER = "/*menu-toggle*/"

# CSS injected right AFTER the existing `nav, .header-cta { display:none }` rule,
# which lives inside the @media (max-width:920px) block in every broken page.
CSS_BLOCK = (
    "nav.open{display:block;position:absolute;top:100%;left:0;right:0;"
    "background:rgba(10,10,10,0.98);-webkit-backdrop-filter:blur(20px);"
    "backdrop-filter:blur(20px);border-bottom:1px solid var(--line);"
    "padding:0.5rem 1.5rem 1rem;z-index:99;}"
    "nav.open ul{flex-direction:column;gap:0;align-items:stretch;}"
    "nav.open li{border-top:1px solid var(--line);}"
    "nav.open a{display:block;padding:0.95rem 0;font-size:1rem;}"
)

# Whitespace-tolerant anchor: `nav , .header-cta { display : none ; }` in any spacing.
ANCHOR_RE = re.compile(
    r"nav\s*,\s*\.header-cta\s*\{\s*display\s*:\s*none\s*;?\s*\}"
)

JS_BLOCK = (
    "<script>" + MARKER + "(function(){"
    "var t=document.querySelector('.menu-toggle'),n=document.querySelector('nav');"
    "if(t&&n){"
    "t.addEventListener('click',function(e){e.stopPropagation();n.classList.toggle('open');});"
    "n.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){n.classList.remove('open');});});"
    "document.addEventListener('click',function(e){if(!e.target.closest('header'))n.classList.remove('open');});"
    "}})();</script>"
)


def patch_file(path):
    """Return ('patched'|'skipped'|'no-anchor'|'no-body', detail)."""
    html = path.read_text(encoding="utf-8")

    if MARKER in html or "nav.open" in html:
        return "skipped", "already patched"

    if "menu-toggle" not in html:
        return "skipped", "no hamburger on this page"

    # --- CSS: inject after the mobile nav-hide rule ---
    m = ANCHOR_RE.search(html)
    if not m:
        return "no-anchor", "could not find `nav,.header-cta{display:none}` rule"
    css_added = html[: m.end()] + CSS_BLOCK + html[m.end():]

    # --- JS: inject before </body> (last occurrence) ---
    idx = css_added.lower().rfind("</body>")
    if idx == -1:
        return "no-body", "no </body> tag"
    final = css_added[:idx] + JS_BLOCK + "\n" + css_added[idx:]

    path.write_text(final, encoding="utf-8")
    return "patched", f"+CSS@{m.start()} +JS"


def main():
    targets = []
    for name in ("index.html", "about.html", "services.html", "contact.html"):
        p = ROOT / name
        if p.exists():
            targets.append(p)
    targets += sorted((ROOT / "blog").glob("*.html"))

    counts = {"patched": 0, "skipped": 0, "no-anchor": 0, "no-body": 0}
    print(f"Scanning {len(targets)} HTML files...\n")
    for p in targets:
        status, detail = patch_file(p)
        counts[status] += 1
        if status != "skipped" or "already" in detail:
            flag = "OK " if status == "patched" else ("-- " if status == "skipped" else "!! ")
            rel = p.relative_to(ROOT)
            print(f"  {flag}{status:9} {rel}  ({detail})")

    print("\n" + "=" * 60)
    print(f"  patched:   {counts['patched']}")
    print(f"  skipped:   {counts['skipped']}")
    print(f"  NO-ANCHOR: {counts['no-anchor']}  (must be 0)")
    print(f"  NO-BODY:   {counts['no-body']}  (must be 0)")
    if counts["no-anchor"] or counts["no-body"]:
        print("\n  *** FAILURES — some pages not patched ***")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
