#!/usr/bin/env python3
"""Wire /services.html to the new service pages, and consolidate "y62 garage".

(A) HUB LINKS. services.html was retitled as a menu so it stops competing with
the homepage; this gives it something to distribute to. A contextual link is
added inside the matching service card's paragraph, not as a bare list, so the
anchor text sits in prose.

(B) "y62 garage" CONSOLIDATION. Measured: the term is fragmented across EIGHT
URLs, none better than position 8:

    /                                              pos  8.0   66 impr
    /blog/nissan-patrol-y62-transmission-problems  pos  8.0    2 impr
    /blog/nissan-patrol-y62-problems-dubai         pos 10.2   28 impr
    /blog/nissan-patrol-y62-dubai-complete-guide   pos 10.5   13 impr
    /blog/                                         pos 11.4   20 impr
    /blog/nissan-patrol-y62-vs-y63-dubai-compar    pos 13.0    2 impr
    /blog/page/2/                                  pos 10.0    1 impr

The BLOG pages get an in-body link to /y62-garage-dubai.html anchored on the
exact term, so the new page becomes the site's declared answer for it.

THE HOMEPAGE IS DELIBERATELY LEFT ALONE. It holds position 8.0 on 66 impressions
and is the strongest page on the site — it also wins "nissan patrol garage" (4.0)
and "patrol garage" (3.6). Weakening it to feed a page with no history would
trade a proven asset for a hope. Owner's decision, and the right one.

Preserves blog mtimes: journal_update.py derives displayed dates and listing
order from them.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!-- HUBLINK -->"

# services.html: (anchor text already in the card's prose, link to add)
HUB = [
    ("Keep your Patrol running smoothly with scheduled service.",
     "Keep your Patrol running smoothly with scheduled service. "
     '<a href="/services/y62-major-service-dubai.html">See what a Nissan Patrol service covers</a>.'),
    ("The gearbox is the most expensive thing to get wrong on a Patrol.",
     "The gearbox is the most expensive thing to get wrong on a Patrol. "
     '<a href="/services/y62-gearbox-transmission-dubai.html">More on Y62 gearbox and transmission work</a>.'),
]

# Fallback anchors if the exact sentences above are not present.
HUB_FALLBACK = [
    ("y62-major-service-dubai.html", "Full Service &amp; Maintenance",
     "See what a Nissan Patrol service covers"),
    ("y62-gearbox-transmission-dubai.html", "Gearbox &amp; Transmission Service",
     "More on Y62 gearbox and transmission work"),
    ("nissan-patrol-v8-engine.html", "Engine Diagnostics &amp; Repair",
     "About the VK56VD V8"),
]

# Blog pages that currently fragment "y62 garage". Homepage excluded on purpose.
CONSOLIDATE = [
    "nissan-patrol-y62-problems-dubai.html",
    "nissan-patrol-y62-dubai-complete-guide.html",
    "nissan-patrol-y62-transmission-problems-dubai.html",
    "nissan-patrol-y62-vs-y63-dubai-comparison.html",
]
SENTENCE = (' If you are looking for a <a href="/y62-garage-dubai.html">Y62 garage</a> '
            'in Dubai, that is what we are.')


def patch_services(dry):
    p = ROOT / "services.html"
    h = p.read_text(encoding="utf-8")
    if MARKER in h:
        print("  skip   services.html (already wired)")
        return 0
    n = 0
    for old, new in HUB:
        if old in h:
            h = h.replace(old, new, 1); n += 1
    # any card not matched by prose gets the link appended to its paragraph
    for fname, heading, anchor in HUB_FALLBACK:
        if fname in h:
            continue
        m = re.search(rf'<h2>(?:<a[^>]*>)?{re.escape(heading)}(?:</a>)?</h2>\s*<p>(.*?)</p>', h, re.S)
        if m:
            h = (h[:m.end(1)] + f' <a href="/services/{fname}">{anchor}</a>.' + h[m.end(1):])
            n += 1
    h = h.replace("</body>", f"{MARKER}\n</body>", 1)
    if not dry:
        p.write_text(h, encoding="utf-8")
    print(f"  patch  services.html: {n} hub link(s) added")
    return n


def patch_blog(dry):
    n = 0
    for fname in CONSOLIDATE:
        p = ROOT / "blog" / fname
        if not p.exists():
            print(f"  !! missing {fname}")
            continue
        h = p.read_text(encoding="utf-8")
        if "/y62-garage-dubai.html" in h:
            print(f"  skip   {fname} (already links to the new page)")
            continue
        m = re.search(r'(<h2[^>]*>\s*When to [Bb]ring[^<]*</h2>\s*<p>.*?)</p>', h, re.S)
        if not m:
            m = re.search(r'(<article>\s*.*?<p>.*?)</p>', h, re.S)
        if not m:
            print(f"  !! {fname}: no insertion point")
            continue
        h = h[:m.end(1)] + SENTENCE + h[m.end(1):]
        if not dry:
            st = p.stat()
            p.write_text(h, encoding="utf-8")
            os.utime(p, (st.st_atime, st.st_mtime))  # mtime is content
        print(f"  patch  {fname}: 'Y62 garage' link added")
        n += 1
    return n


def patch_sitemap(dry):
    """publish.py's sitemap list is hardcoded — a new page not listed there is
    dropped from the sitemap by the very next cron run."""
    p = ROOT / "scripts" / "publish.py"
    h = p.read_text(encoding="utf-8")
    if "y62-major-service-dubai" in h:
        print("  skip   publish.py (service pages already in the sitemap list)")
        return 0
    old = '        ("/y62-garage-dubai.html", "0.9", "monthly"),\n'
    new = old + ''.join(f'        ("/services/{f}", "0.9", "monthly"),\n' for f in
                        ["y62-major-service-dubai.html",
                         "y62-gearbox-transmission-dubai.html",
                         "nissan-patrol-v8-engine.html"])
    if old not in h:
        print("  !! publish.py: sitemap anchor not found")
        return -1
    h = h.replace(old, new, 1)
    if not dry:
        p.write_text(h, encoding="utf-8")
    print("  patch  publish.py: 3 service pages added to the sitemap list")
    return 1


def main():
    dry = "--dry-run" in sys.argv
    patch_services(dry); patch_blog(dry)
    if patch_sitemap(dry) < 0:
        return 1
    print("\n" + ("DRY RUN — nothing written" if dry else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
