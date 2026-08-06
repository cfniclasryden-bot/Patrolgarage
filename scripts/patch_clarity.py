#!/usr/bin/env python3
"""patch_clarity.py — install the Microsoft Clarity tag on every deployed page.

The site is flat static HTML with no shared head include: each page carries its
own <head> (that's why the gtag block is duplicated 44 times). So a site-wide
tag has to be injected file by file.

New daily posts are covered separately, in assemble.py — see ensure_clarity()
there. This script is for the existing pages, and is safe to re-run at any time.

Idempotent: any file already containing the Clarity tag URL is skipped.
Anchors on </head>, which every page has exactly once — unlike the gtag block,
which exists in both pretty-printed and fully-minified variants.

Preserves file mtimes. journal_update.py derives each post's DISPLAYED DATE and
the listing sort order from mtime, so a bulk rewrite that touches timestamps
re-dates the entire blog to today. Any future site-wide patch script must do
the same.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLARITY_PROJECT_ID = "xnpj1qfkuv"

# Marker doubles as the idempotency check.
MARKER = "clarity.ms/tag/"

SNIPPET = f"""  <!-- Microsoft Clarity -->
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "{CLARITY_PROJECT_ID}");
  </script>
"""


def target_files():
    """Every HTML page that actually gets deployed.

    drafts/ is excluded: it is gitignored, never deployed, and its contents are
    wrapped by assemble.py into the blog template (which carries the tag).
    """
    files = sorted(ROOT.glob("*.html"))
    files += sorted((ROOT / "blog").rglob("*.html"))
    return files


def inject(html):
    """Insert the snippet immediately before </head>. Returns (html, changed)."""
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
            os.utime(path, (st.st_atime, st.st_mtime))  # keep the post's date
            patched.append(path)
        elif MARKER in html:
            skipped.append(path)
        else:
            failed.append(path)

    rel = lambda p: p.relative_to(ROOT).as_posix()
    print(f"[+] Clarity project {CLARITY_PROJECT_ID}")
    print(f"    patched:              {len(patched)}")
    print(f"    already had the tag:  {len(skipped)}")
    if failed:
        print(f"    [!] NO </head>, skipped: {len(failed)}")
        for p in failed:
            print(f"        {rel(p)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
