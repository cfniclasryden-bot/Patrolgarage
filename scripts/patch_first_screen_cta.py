#!/usr/bin/env python3
"""patch_first_screen_cta.py — the first-screen WhatsApp ask, with an Arabic option.

Lead conversion push, 2026-10-07 (same block as topchallenger.ae). On the
homepage, /services and the five posts with the most leads over 90 days, the
first screen gets:

  * a WhatsApp button reading "Send us the symptom or a short video on WhatsApp"
    (event_label hero-wa)
  * a small "عربي" button that opens WhatsApp with an Arabic prefill
    (event_label hero-wa-ar)

Posts, ranked by leads on the page plus leads from sessions that started there,
2026-07-09 to 2026-10-06, GA4 test bursts excluded: the Y62 complete guide (11),
Y62 problems (3), service cost (3), best oil (2), Y62 transmission problems (2).
Left out on purpose: the tow-bar post (6, owner decision pending on whether the
fitting is offered), and the Y61 guide and Y62-vs-Y63 page (2 each), because a
WhatsApp ask on those reads as a Y61 or Y63 service offer and this site services
the Y62 only.

It also teaches the inline tracker on every page to report data-cta-label as the
event_label (61 pages share one expression), so these two buttons are their own
rows in GA4.

    python3 scripts/patch_first_screen_cta.py           # dry run
    python3 scripts/patch_first_screen_cta.py --write   # writes, preserving mtimes

Idempotent (marker: data-cta-label="hero-wa"). mtimes are preserved because
journal_update.py derives each post's displayed date and the listing order from
them. assemble.py strips the block from its template post, because
cta_lib.set_all_wa_prefill() would otherwise give the Arabic button an English
prefill on every new post.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
WA = "971585143634"
MARKER = 'data-cta-label="hero-wa"'

TEXT = "Send us the symptom or a short video on WhatsApp"
EN = "Hi, I have a Nissan Patrol Y62. Here is the symptom (I can send a short video): "
AR = "مرحباً، لدي نيسان باترول Y62 وأريد أن أرسل لكم وصف المشكلة أو فيديو قصير."

POSTS = [
    "blog/nissan-patrol-y62-dubai-complete-guide.html",
    "blog/nissan-patrol-y62-problems-dubai.html",
    "blog/nissan-patrol-service-cost-dubai.html",
    "blog/best-oil-nissan-patrol-uae-heat.html",
    "blog/nissan-patrol-y62-transmission-problems-dubai.html",
]

CSS = ('<style id="fs-cta-css">.fs-cta{display:flex;flex-wrap:wrap;gap:.6rem;margin:1.4rem 0 0;'
       'align-items:stretch}.fs-wa{background:#25d366;color:#0a0a0a;white-space:normal;text-align:left}'
       '.fs-wa:hover{background:#1fbc5a}.fs-ar{display:inline-flex;align-items:center;justify-content:center;'
       'min-width:52px;min-height:48px;padding:0 1rem;border:1.5px solid rgba(255,255,255,.35);color:#fff;'
       'font-weight:700;font-size:1.05rem;text-decoration:none}.fs-ar:hover{border-color:#25d366;color:#25d366}'
       '</style>\n')

WA_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true">'
          '<path d="M20.5 3.5A11.9 11.9 0 0 0 12 0C5.4 0 0 5.4 0 12c0 2.1.6 4.2 1.6 6L0 24l6.2-1.6A12 '
          '12 0 0 0 12 24c6.6 0 12-5.4 12-12 0-3.2-1.2-6.2-3.5-8.5zM12 21.9c-1.8 0-3.6-.5-5.1-1.4l-.4-.2'
          '-3.7 1 1-3.6-.2-.4A9.9 9.9 0 0 1 2.2 12C2.2 6.6 6.6 2.2 12 2.2S21.8 6.6 21.8 12 17.4 21.9 12 '
          '21.9z"/></svg>')


def anchors():
    return (f'<a class="btn fs-wa" {MARKER} href="https://wa.me/{WA}?text={quote(EN)}" '
            f'target="_blank" rel="noopener">{WA_SVG}{TEXT}</a>'
            f'<a class="fs-ar" data-cta-label="hero-wa-ar" lang="ar" dir="rtl" '
            f'href="https://wa.me/{WA}?text={quote(AR)}" target="_blank" rel="noopener" '
            f'aria-label="WhatsApp in Arabic">عربي</a>')


BLOCK = f'\n      <div class="fs-cta" data-fs="1">{anchors()}</div>'

TRACKER_OLD = "'event_label': window.location.pathname + ' | ' + ctaPos(el)"
TRACKER_NEW = ("'event_label': (el.closest('[data-cta-label]') ? "
               "el.closest('[data-cta-label]').getAttribute('data-cta-label') : "
               "window.location.pathname + ' | ' + ctaPos(el))")

HOME_OLD = re.compile(r'<a href="https://wa\.me/971585143634" target="_blank" rel="noopener" '
                      r'class="btn btn-primary">\s*Get a Quote\s*<svg.*?</svg>\s*</a>', re.S)


def place(path, html):
    """Return html with the block placed, or None if there is nowhere to put it."""
    if path == "index.html":
        new, n = HOME_OLD.subn(lambda _m: anchors(), html, count=1)
        return new if n else None
    if path == "services.html":
        m = re.search(r"</h1>\s*<p class=\"hero-lede\">.*?</p>", html, re.S)
    else:
        m = re.search(r"</h1>", html)
    if not m:
        return None
    return html[:m.end()] + BLOCK + html[m.end():]


def main():
    write = "--write" in sys.argv[1:]
    changed = {}
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.split()
    for f in files:
        html = (ROOT / f).read_text(encoding="utf-8")
        new = html.replace(TRACKER_OLD, TRACKER_NEW)
        if f in ["index.html", "services.html"] + POSTS and MARKER not in new:
            placed = place(f, new)
            if placed is None:
                print(f"[!] {f}: no insertion point found")
                return 1
            new = placed.replace("</head>", CSS + "</head>", 1)
            print(f"[+] {f}: first-screen CTA + Arabic button")
        if new != html:
            changed[f] = new
    print(f"[=] {'writing' if write else 'would write'} {len(changed)} file(s) "
          f"(tracker label support on every page that has the shared tracker)")
    if write:
        for f, new in changed.items():
            p = ROOT / f
            st = p.stat()
            p.write_text(new, encoding="utf-8")
            os.utime(p, (st.st_atime, st.st_mtime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
