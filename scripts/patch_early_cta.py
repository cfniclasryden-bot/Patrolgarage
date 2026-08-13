#!/usr/bin/env python3
"""Backfill the early CTA into published posts, and make CTA position measurable.

See early_cta.py for the measurement that motivated this. Two changes per post:

1. INSERT the early CTA directly after the quick-answer block (9% of page depth),
   or after the first paragraph on the 9 posts that have no quick-answer block.

2. UPGRADE THE CLICK TRACKING. Every WhatsApp and tel link currently reports
   event_label = window.location.pathname, so an early-CTA click is
   indistinguishable from a footer click. Adding a CTA without this would be
   unmeasurable: total clicks might move and you would not know which position
   earned them. The snippet is byte-identical across all 44 posts (verified by
   hashing), so it can be replaced wholesale.

   After this, whatsapp_click / phone_click report "<path> | <position>" where
   position is one of: early, mid, banner, float, header, footer, body.

Preserves mtimes — journal_update.py derives each post's displayed date and the
blog listing order from them, and publish.py runs it on every deploy.
"""
import hashlib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import early_cta

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

TRACK_RE = re.compile(
    r"<script>\s*document\.addEventListener\('DOMContentLoaded'.*?</script>", re.S)

NEW_TRACKING = """<script>
document.addEventListener('DOMContentLoaded', function() {
  // Which CTA earned the click. Without this every WhatsApp link reports only
  // the page path, so the early CTA cannot be told apart from the footer one.
  function ctaPos(el) {
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
          'event_label': window.location.pathname + ' | ' + ctaPos(el)
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


def patch_file(path, dry):
    html = path.read_text(encoding="utf-8")
    notes = []

    m = re.search(r"<article>(.*?)</article>", html, re.S)
    if m and not early_cta.already_present(m.group(1)):
        body = early_cta.insert(m.group(1), path.stem)
        if body != m.group(1):
            html = html[:m.start(1)] + body + html[m.end(1):]
            notes.append(f"cta:{early_cta.post_type(path.stem)}")

    # The workshop's own advertised price band, still in 32 posts' AutoRepair
    # schema after the 2026-08-12 price removal (which only covered static pages).
    new_html, n = re.subn(r',\s*\n\s*"priceRange":\s*"[^"]*"', "", html, count=1)
    if n:
        html = new_html
        notes.append("priceRange")

    if "ctaPos" not in html:
        new, n = TRACK_RE.subn(lambda _: NEW_TRACKING, html, count=1)
        if n:
            html = new
            notes.append("tracking")

    if not notes:
        return None
    if not dry:
        st = path.stat()
        path.write_text(html, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))  # mtime is content
    return notes


def main():
    dry = "--dry-run" in sys.argv
    posts = [p for p in sorted(BLOG.glob("*.html")) if p.name != "index.html"]

    # The tracking snippet must be identical everywhere for a wholesale swap.
    hashes = set()
    for p in posts:
        mm = TRACK_RE.search(p.read_text(errors="ignore"))
        hashes.add(hashlib.md5(mm.group(0).encode()).hexdigest() if mm else "NONE")
    print(f"  tracking snippet variants across {len(posts)} posts: {len(hashes)}")
    if "NONE" in hashes:
        print("  !! some posts have no tracking snippet — aborting")
        return 1

    counts = {}
    for p in posts:
        notes = patch_file(p, dry)
        if notes:
            for n in notes:
                counts[n] = counts.get(n, 0) + 1
    # static pages get the tracking upgrade too, so labels are consistent sitewide
    for name in ("index.html", "services.html", "about.html", "contact.html",
                 "y62-garage-dubai.html"):
        p = ROOT / name
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        if "ctaPos" in h:
            continue
        new, n = TRACK_RE.subn(lambda _: NEW_TRACKING, h, count=1)
        if n:
            if not dry:
                p.write_text(new, encoding="utf-8")
            counts["tracking(static)"] = counts.get("tracking(static)", 0) + 1

    for k, v in sorted(counts.items()):
        print(f"  {k:<20} {v}")
    print("\n" + ("DRY RUN — nothing written" if dry else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
