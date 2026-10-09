#!/usr/bin/env python3
"""patch_first_screen_cta.py — the first-screen WhatsApp ask, in Patrol Garage's own design.

History. On 2026-10-07 this script put topchallenger.ae's block on this site
verbatim: the same "Send us the symptom or a short video on WhatsApp" button in
WhatsApp green, the same square "عربي" button beside it, the same fs-cta / fs-ar
class names and the same hero-wa / hero-wa-ar labels. The two sites looked like
one business. Redesigned 2026-10-09 so nothing in it is shared with TC:

  * layout   one button, stacked over a call line and an Arabic line, instead of
             TC's two-button row. On the homepage it replaces the old row of
             WhatsApp + Arabic + phone buttons.
  * style    only this site's own tokens and button: .btn .btn-primary (white,
             uppercase Archivo), JetBrains Mono for the call line, --whatsapp
             only as the Arabic link's underline.
  * words    new button, call and Arabic wording, and new pre-fills.
  * labels   pg-hero-wa, pg-hero-wa-ar, pg-hero-call. Event names are unchanged
             (the shared tracker sends whatsapp_click / phone_click and reads
             data-cta-label as event_label), so GA4 separates these from TC's.

Pages: the homepage, /services and the five posts with the most leads over 90
days (see the 2026-10-07 commit for the ranking). Left out on purpose: the
tow-bar post (owner decision pending), the Y61 guide and the Y62-vs-Y63 page
(a WhatsApp ask there reads as a Y61 / Y63 service offer).

    python3 scripts/patch_first_screen_cta.py           # dry run
    python3 scripts/patch_first_screen_cta.py --write   # writes, preserving mtimes

Idempotent (marker: data-cta-label="pg-hero-wa"). Migrates the old block and
removes its stylesheet everywhere, including posts assemble.py built from the
template while it still carried that stylesheet. assemble.py strips this block
(and its stylesheet) from its template post so new posts do not inherit it.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
WA = "971585143634"
TEL = "+971585143634"
TEL_SHOWN = "+971 58 514 3634"
MARKER = 'data-cta-label="pg-hero-wa"'

BUTTON = "WhatsApp us about your Y62"
CALL = "Rather talk?"
AR_LINK = "تفضّل العربية؟ راسلنا على واتساب"
EN = "Hello Patrol Garage, I need help with my Nissan Patrol Y62: "
AR = "السلام عليكم، عندي نيسان باترول Y62 وأحتاج مساعدة في مشكلة: "

POSTS = [
    "blog/nissan-patrol-y62-dubai-complete-guide.html",
    "blog/nissan-patrol-y62-problems-dubai.html",
    "blog/nissan-patrol-service-cost-dubai.html",
    "blog/best-oil-nissan-patrol-uae-heat.html",
    "blog/nissan-patrol-y62-transmission-problems-dubai.html",
]

CSS = ('<style id="pg-ask-css">'
       '.pg-ask{display:flex;flex-direction:column;align-items:flex-start;gap:.35rem;margin:1.6rem 0 0}'
       '.pg-ask .pg-ask-wa{white-space:normal;text-align:left;margin-bottom:.4rem}'
       '.pg-ask .pg-ask-wa svg{width:16px;height:16px;flex-shrink:0}'
       '.pg-ask-alt{margin:0;font-family:\'JetBrains Mono\',monospace;font-size:.74rem;'
       'letter-spacing:.12em;text-transform:uppercase;color:var(--text-2)}'
       '.pg-ask-alt a,.pg-ask-ar a{display:inline-flex;align-items:center;min-height:44px;'
       'text-decoration:none;color:var(--white)}'
       '.pg-ask-alt a{margin-left:.35rem;border-bottom:1px solid rgba(255,255,255,.3)}'
       '.pg-ask-alt a:hover{border-bottom-color:var(--white)}'
       '.pg-ask-ar{margin:0;font-size:.95rem}'
       '.pg-ask-ar a{color:var(--text);border-bottom:1px solid var(--whatsapp)}'
       '.pg-ask-ar a:hover{color:var(--whatsapp)}'
       '</style>\n')

WA_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
          '<path d="M20.5 3.5A11.9 11.9 0 0 0 12 0C5.4 0 0 5.4 0 12c0 2.1.6 4.2 1.6 6L0 24l6.2-1.6A12 '
          '12 0 0 0 12 24c6.6 0 12-5.4 12-12 0-3.2-1.2-6.2-3.5-8.5zM12 21.9c-1.8 0-3.6-.5-5.1-1.4l-.4-.2'
          '-3.7 1 1-3.6-.2-.4A9.9 9.9 0 0 1 2.2 12C2.2 6.6 6.6 2.2 12 2.2S21.8 6.6 21.8 12 17.4 21.9 12 '
          '21.9z"/></svg>')


def block(indent="      "):
    return (f'{indent}<div class="pg-ask" data-fs="1">\n'
            f'{indent}  <a class="btn btn-primary pg-ask-wa" {MARKER} '
            f'href="https://wa.me/{WA}?text={quote(EN)}" target="_blank" rel="noopener">{WA_SVG}{BUTTON}</a>\n'
            f'{indent}  <p class="pg-ask-alt">{CALL}<a data-cta-label="pg-hero-call" '
            f'href="tel:{TEL}">{TEL_SHOWN}</a></p>\n'
            f'{indent}  <p class="pg-ask-ar" lang="ar" dir="rtl"><a lang="ar" data-cta-label="pg-hero-wa-ar" '
            f'href="https://wa.me/{WA}?text={quote(AR)}" target="_blank" rel="noopener">{AR_LINK}</a></p>\n'
            f'{indent}</div>')


OLD_CSS = re.compile(r'<style id="fs-cta-css">.*?</style>\n?', re.S)
OLD_BLOCK = re.compile(r'[ \t]*<div class="fs-cta" data-fs="1">.*?</div>', re.S)
# Homepage: the whole old button row (WhatsApp + Arabic + phone) becomes the stack.
OLD_HOME_ROW = re.compile(r'[ \t]*<div class="hero-cta">\s*<a class="btn fs-wa".*?</div>', re.S)

TRACKER_OLD = "'event_label': window.location.pathname + ' | ' + ctaPos(el)"
TRACKER_NEW = ("'event_label': (el.closest('[data-cta-label]') ? "
               "el.closest('[data-cta-label]').getAttribute('data-cta-label') : "
               "window.location.pathname + ' | ' + ctaPos(el))")


def place(path, html):
    """html with the PG block in place of the old one (or newly placed), or None."""
    if path == "index.html":
        new, n = OLD_HOME_ROW.subn(lambda _m: block(), html, count=1)
        return new if n else None
    new, n = OLD_BLOCK.subn(lambda _m: block(), html, count=1)
    if n:
        return new
    if path == "services.html":
        m = re.search(r"</h1>\s*<p class=\"hero-lede\">.*?</p>", html, re.S)
    else:
        m = re.search(r"</h1>", html)
    if not m:
        return None
    return html[:m.end()] + "\n" + block() + html[m.end():]


def main():
    write = "--write" in sys.argv[1:]
    changed = {}
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    for f in files:
        html = (ROOT / f).read_text(encoding="utf-8")
        new = OLD_CSS.sub("", html.replace(TRACKER_OLD, TRACKER_NEW))
        if f in ["index.html", "services.html"] + POSTS and MARKER not in new:
            placed = place(f, new)
            if placed is None:
                print(f"[!] {f}: no insertion point found")
                return 1
            new = placed
            print(f"[+] {f}: Patrol Garage first-screen ask")
        if MARKER in new and 'id="pg-ask-css"' not in new:
            new = new.replace("</head>", CSS + "</head>", 1)
        if new != html:
            changed[f] = new
    print(f"[=] {'writing' if write else 'would write'} {len(changed)} file(s)")
    for f in sorted(changed):
        if f not in ["index.html", "services.html"] + POSTS:
            print(f"    {f}: old first-screen stylesheet removed")
    if write:
        for f, new in changed.items():
            p = ROOT / f
            st = p.stat()
            p.write_text(new, encoding="utf-8")
            os.utime(p, (st.st_atime, st.st_mtime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
