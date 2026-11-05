#!/usr/bin/env python3
"""mobile_ux.py — the phone layer every shipped page carries (2026-11-05).

Three things, all applied by one idempotent apply(html):

1. LONG .btn LABELS WRAP ON A PHONE. Every page family declares
   `.btn { white-space: nowrap }`, so "Get your quote on WhatsApp ->" and
   "Ask a Patrol specialist on WhatsApp ->" ran 374-488 px wide on 360 and 390
   px screens: 33 of 72 pages had a button cut off at the right edge (body has
   overflow-x: hidden, so it was clipped rather than scrollable). Measured in
   real-width iframes on 2026-11-05, not with --window-size.

2. A STICKY CALL + WHATSAPP BAR ON MOBILE (<= 768 px), in the site's own
   styling: square Archivo uppercase buttons, white Call / WhatsApp-green
   WhatsApp, on the header's translucent black. It replaces the round
   .whatsapp-float on phones (two WhatsApp buttons stacked was the alternative).
   The WhatsApp half copies the page's own .whatsapp-float href, so it keeps
   the page's pre-fill, and cta_lib.set_all_wa_prefill / ad_city routing
   rewrite it like any other WhatsApp link.

   Analytics: the bar sits in [data-cta="sticky_bar"], ctaPos() returns
   'sticky_bar' for it, and every whatsapp_click / phone_click now carries a
   `cta_position` parameter (ctaPos(el)). The six pages that still ran the
   pre-ctaPos tracker (blog listings, services/*) get the standard tracker,
   so cta_position is reported site-wide. Labels: pg-sticky-call /
   pg-sticky-wa.

3. INTERNAL LINKS WITH NO .html. 25 pages carried 355 single-quoted
   href='/services', href='/blog/<slug>' links to 30 targets: Netlify's
   pretty-URL serve-time rewrite, frozen into the files when those pages were
   pulled back from live in de863e4. Vercel answers each with a 301, so every
   one was a redirect hop for users and crawlers. Rewritten to the real
   /<path>.html, and only when that file exists.

Wired into assemble.py (new posts), publish.publish() (every deploy, before
journal_update and the Abu Dhabi routing) and the page builders.
scripts/test_mobile_ux.py fails on any shipped page missing any of it.

    python3 scripts/mobile_ux.py            # dry run
    python3 scripts/mobile_ux.py --write    # mtimes preserved (mtime = post date)
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

PHONE_TEL = "tel:+971558175637"
WA_DEFAULT = "https://wa.me/971558175637"

CSS_ID = "pg-mobile-css"
BAR_MARK = 'data-cta="sticky_bar"'

CSS = """<style id="pg-mobile-css">
  @media (max-width: 768px) {
    body .btn { white-space: normal; max-width: 100%; text-align: center; justify-content: center; line-height: 1.3; overflow-wrap: anywhere; }
    body .whatsapp-float { display: none; }
    body { padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px)); }
    .pg-sticky { position: fixed; left: 0; right: 0; bottom: 0; z-index: 95; display: grid; grid-template-columns: 1fr 1fr; gap: 1px; padding: 8px 8px calc(8px + env(safe-area-inset-bottom, 0px)); background: rgba(10,10,10,0.94); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-top: 1px solid rgba(255,255,255,0.1); }
    .pg-sticky a { display: flex; align-items: center; justify-content: center; gap: 0.5rem; min-height: 44px; padding: 0 0.75rem; font-family: 'Archivo', system-ui, sans-serif; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none; white-space: nowrap; }
    .pg-sticky svg { width: 16px; height: 16px; flex: none; }
    .pg-sticky-call { background: #ffffff; color: #0a0a0a; }
    .pg-sticky-wa { background: #25d366; color: #0a0a0a; }
  }
  @media (min-width: 769px) { .pg-sticky { display: none; } }
  @media print { .pg-sticky { display: none; } }
</style>
"""

PHONE_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 '
             '6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 '
             '1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg>')
WA_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.5 3.5A11.9 11.9 0 0 0 12 0C5.4 0 '
          '0 5.4 0 12c0 2.1.6 4.2 1.6 6L0 24l6.2-1.6c1.7.9 3.7 1.4 5.7 1.4h.1c6.6 0 12-5.4 12-12 0-3.2-1.2-6.2-3.5-8.3zM12 '
          '21.9c-1.8 0-3.6-.5-5.1-1.4l-.4-.2-3.7 1 1-3.6-.2-.4A9.9 9.9 0 0 1 2.2 12C2.2 6.6 6.6 2.2 12 2.2c2.7 0 5.2 1 '
          '7 3a9.8 9.8 0 0 1 2.9 7c0 5.4-4.4 9.7-9.9 9.7zm5.5-7.5c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.1-.2.3-.7.9-.9 '
          '1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.5-2.4-1.5-.9-.8-1.5-1.7-1.6-2-.2-.3 0-.5.1-.6l.4-.5.3-.5c.1-.2 0-.4 '
          '0-.5l-.9-2.1c-.2-.5-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5 4.5 '
          '1.9.8 2.6.9 3.5.7.6-.1 1.7-.7 2-1.4.2-.7.2-1.2.2-1.4-.1-.1-.3-.2-.6-.3z"/></svg>')


def bar_html(wa_href):
    return (f'<div class="pg-sticky" {BAR_MARK} role="navigation" aria-label="Call or WhatsApp Patrol Garage">'
            f'<a class="pg-sticky-call" data-cta-label="pg-sticky-call" href="{PHONE_TEL}">{PHONE_SVG}<span>Call</span></a>'
            f'<a class="pg-sticky-wa" data-cta-label="pg-sticky-wa" href="{wa_href}" target="_blank" rel="noopener">'
            f'{WA_SVG}<span>WhatsApp</span></a></div>\n')


# The standard click tracker (index.html's), with the sticky-bar position and
# the cta_position parameter. Replaces the pre-ctaPos tracker wholesale.
STANDARD_TRACKER = """<script>
document.addEventListener('DOMContentLoaded', function() {
  // Which CTA earned the click. Without this every WhatsApp link reports only
  // the page path, so the early CTA cannot be told apart from the footer one.
  function ctaPos(el) {
    if (el.closest('[data-cta="sticky_bar"]')) return 'sticky_bar';
    if (el.closest('[data-cta="early"]')) return 'early';
    if (el.closest('[data-cta="mid"]')) return 'mid';
    if (el.closest('.whatsapp-float')) return 'float';
    if (el.closest('.cta-banner')) return 'banner';
    if (el.closest('header')) return 'header';
    if (el.closest('footer')) return 'footer';
    return 'body';
  }
  function track(el, name) {
    el.addEventListener('click', function() {
      if (typeof gtag === 'function') {
        gtag('event', name, {
          'event_category': 'engagement',
          'cta_position': ctaPos(el),
          'event_label': (el.closest('[data-cta-label]') ? el.closest('[data-cta-label]').getAttribute('data-cta-label') : window.location.pathname + ' | ' + ctaPos(el))
        });
      }
    });
  }
  document.querySelectorAll('a[href*="wa.me"], a[href*="whatsapp"]').forEach(function(el) {
    track(el, 'whatsapp_click');
  });
  document.querySelectorAll('a[href^="tel:"]').forEach(function(el) {
    track(el, 'phone_click');
  });
});
</script>"""

OLD_TRACKER_RE = re.compile(
    r"<script>\s*document\.addEventListener\('DOMContentLoaded', function\(\) \{\s*"
    r"document\.querySelectorAll\('a\[href\*=\"wa\.me\"\].*?</script>", re.S)
FLOAT_LINE = "if (el.closest('.whatsapp-float')) return 'float';"
STICKY_LINE = "if (el.closest('[data-cta=\"sticky_bar\"]')) return 'sticky_bar';"
EVCAT = "'event_category': 'engagement',"
CTA_PARAM = "'cta_position': ctaPos(el),"

# href='/x' or href="/x" with no extension, no trailing slash. Root-absolute only.
_EXTLESS_RE = re.compile(r"""href=(['"])(/[^'"#?\s]*?[^/'"#?\s])([#?][^'"]*)?\1""")


def fix_links(html):
    """Point extensionless internal links at the real .html file. Returns (html, n)."""
    n = 0

    def repl(m):
        nonlocal n
        path, tail = m.group(2), m.group(3) or ""
        if re.search(r"\.[A-Za-z0-9]{2,12}$", path.rsplit("/", 1)[-1]):
            return m.group(0)
        if not (ROOT / (path.lstrip("/") + ".html")).is_file():
            return m.group(0)
        n += 1
        return f'href="{path}.html{tail}"'
    return _EXTLESS_RE.sub(repl, html), n


def extensionless_links(html):
    """Internal links that still lack .html but whose .html file exists (for the test)."""
    out = []
    for m in _EXTLESS_RE.finditer(html):
        path = m.group(2)
        if re.search(r"\.[A-Za-z0-9]{2,12}$", path.rsplit("/", 1)[-1]):
            continue
        if (ROOT / (path.lstrip("/") + ".html")).is_file():
            out.append(path)
    return out


def fix_tracker(html):
    """Standard tracker with sticky_bar + cta_position. Returns html."""
    if "function ctaPos" not in html:
        html = OLD_TRACKER_RE.sub(lambda _m: STANDARD_TRACKER, html, count=1)
    if STICKY_LINE not in html and FLOAT_LINE in html:
        html = html.replace(FLOAT_LINE, STICKY_LINE + "\n    " + FLOAT_LINE, 1)
    if CTA_PARAM not in html and "function ctaPos" in html:
        i = html.find("gtag('event', name,")
        j = html.find(EVCAT, i) if i >= 0 else -1
        if j >= 0:
            k = j + len(EVCAT)
            indent = re.match(r"\s*", html[k:]).group(0)
            html = html[:k] + indent + CTA_PARAM + html[k:]
    return html


def page_wa_href(html):
    m = re.search(r'<a href="(https://wa\.me/[^"]*)"[^>]*class="whatsapp-float"', html)
    return m.group(1) if m else WA_DEFAULT


def apply(html):
    """All three fixes, idempotent. Returns the new html."""
    html, _ = fix_links(html)
    if f'id="{CSS_ID}"' not in html and "</head>" in html:
        html = html.replace("</head>", CSS + "</head>", 1)
    if BAR_MARK not in html and "</body>" in html:
        # Before the trackers, so their querySelectorAll at DOMContentLoaded binds the bar.
        anchor = html.find("<script>\ndocument.addEventListener('DOMContentLoaded'")
        bar = bar_html(page_wa_href(html))
        if anchor < 0:
            anchor = html.rfind("</body>")
        html = html[:anchor] + bar + "\n" + html[anchor:]
    return fix_tracker(html)


def missing(html):
    """What a page still lacks — empty list means fully applied (for the test)."""
    out = []
    if f'id="{CSS_ID}"' not in html:
        out.append("mobile css")
    if BAR_MARK not in html:
        out.append("sticky bar")
    if STICKY_LINE not in html:
        out.append("ctaPos sticky_bar")
    if CTA_PARAM not in html:
        out.append("cta_position param")
    if extensionless_links(html):
        out.append(f"{len(extensionless_links(html))} links without .html")
    return out


def run(write):
    from shipped_pages import shipped_pages
    changed, links = [], 0
    for p in shipped_pages():
        html = p.read_text(encoding="utf-8")
        _, n = fix_links(html)
        new = apply(html)
        if new != html:
            changed.append(p.relative_to(ROOT).as_posix())
            links += n
            if write:
                st = p.stat()
                p.write_text(new, encoding="utf-8")
                os.utime(p, (st.st_atime, st.st_mtime))
    return changed, links


def main():
    write = "--write" in sys.argv[1:]
    changed, links = run(write)
    print(f"[=] {'wrote' if write else 'would write'} {len(changed)} page(s); "
          f"{links} extensionless link(s) {'fixed' if write else 'to fix'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
