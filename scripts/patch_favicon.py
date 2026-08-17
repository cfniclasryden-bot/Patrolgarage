#!/usr/bin/env python3
"""patch_favicon.py — declare the favicon in the <head> of every deployed page.

The site shipped with no favicon at all until 2026-08-17 — no /favicon.ico, no
<link rel="icon"> — so Google rendered the generic globe next to every result.
scripts/make_favicon.py produces the image assets; this puts the references in.

Same shape as patch_clarity.py, and for the same reason: flat static HTML with
no shared head include, so every page carries its own <head> and a site-wide
change has to be made file by file. New daily posts are covered separately by
assemble.py, which calls inject() before writing.

PATHS MUST BE ROOT-ABSOLUTE. Posts live at /blog/<slug>.html and the listing
pages at /blog/page/2/, so a relative href resolves to a different (missing)
file per directory depth. "/favicon.ico" is also what Google's crawler probes
directly, independent of any <link>.

Idempotent via MARKER. Anchors on </head>, which every page has exactly once.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Marker doubles as the idempotency check.
MARKER = 'rel="icon"'

SNIPPET = """  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
"""


def target_files():
    """Every HTML page that actually gets deployed.

    Unlike patch_clarity.py's list this includes services/, which did not exist
    when that script was written. drafts/ stays excluded: gitignored, never
    deployed, and wrapped by assemble.py into the blog template.
    """
    files = sorted(ROOT.glob("*.html"))
    files += sorted((ROOT / "services").glob("*.html"))
    files += sorted((ROOT / "blog").rglob("*.html"))
    return files


def inject(html):
    """Insert the icon links immediately before </head>. Returns (html, changed)."""
    if MARKER in html:
        return html, False
    if "</head>" not in html:
        return html, False
    return html.replace("</head>", SNIPPET + "</head>", 1), True


def main():
    patched, skipped, failed = [], [], []

    for path in target_files():
        html = path.read_text(encoding="utf-8")
        new_html, changed = inject(html)
        if changed:
            st = path.stat()
            path.write_text(new_html, encoding="utf-8")
            # journal_update.py now dates posts from their JSON-LD datePublished,
            # so mtime no longer sets the listing date. refresh_scheduler.py still
            # falls back to mtime when a post has no "Last updated" stamp, so
            # preserving it stays the cheap, safe default.
            os.utime(path, (st.st_atime, st.st_mtime))
            patched.append(path)
        elif MARKER in html:
            skipped.append(path)
        else:
            failed.append(path)

    rel = lambda p: p.relative_to(ROOT).as_posix()
    print("[+] Favicon <link> tags")
    print(f"    patched:                {len(patched)}")
    print(f"    already had icon links: {len(skipped)}")
    if failed:
        print(f"    [!] NO </head>, skipped: {len(failed)}")
        for p in failed:
            print(f"        {rel(p)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
