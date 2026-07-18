#!/usr/bin/env python3
"""patch_cta.py — conversion fixes across all live pages. Idempotent.

Three fixes (see cta_lib.py for the actual copy logic):
  1. Context-rich WhatsApp pre-fills on EVERY wa.me link (floating bubble, hero,
     footer, banner). Blog articles get a per-article message derived from the
     title; root pages get the generic quote ask.
  2. Intent-tailored end-of-article banner on blog articles whose banner is still
     the generic "Need Help With Your Y62?" boilerplate. Already-custom banners
     are left untouched.
  3. A mid-article inline WhatsApp CTA on high-intent (cost/problems) articles,
     placed mid-way so a convinced mobile reader can tap without scrolling to the
     bottom (the header CTA is hidden on mobile).

Future cron-published articles inherit the same behaviour via assemble.py, which
imports the same cta_lib functions.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cta_lib

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
ROOT_PAGES = ("index.html", "about.html", "services.html", "contact.html")
# Pages that are not articles (no per-article context, no banner/mid rewrite).
NON_ARTICLE = set(ROOT_PAGES) | {"index.html"}

BANNER_RE = re.compile(r'(<section class="cta-banner">.*?</section>)', re.S)
BANNER_H2_RE = re.compile(r'(<h2>)(.*?)(</h2>)', re.S)
BANNER_P_RE = re.compile(r'(<p>)(.*?)(</p>)', re.S)


def title_of(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else ""


def rewrite_banner(html, title, slug):
    """Rewrite the cta-banner copy (h2 + p + button label) IF it's still generic."""
    m = BANNER_RE.search(html)
    if not m:
        return html, "no-banner"
    banner = m.group(1)
    if not cta_lib.banner_is_generic(banner):
        return html, "banner-custom-kept"
    h2, p, label = cta_lib.banner_for(title, slug)
    new = BANNER_H2_RE.sub(lambda x: x.group(1) + h2 + x.group(3), banner, count=1)
    new = BANNER_P_RE.sub(lambda x: x.group(1) + p + x.group(3), new, count=1)
    # strengthen the WhatsApp button label (the bare "WhatsApp" text → active label)
    new = re.sub(r'(class="btn btn-dark">)WhatsApp(</a>)', r"\1" + label + r"\2", new, count=1)
    return html[: m.start()] + new + html[m.end():], "banner-tailored"


def add_mid_cta(html, title, slug):
    """Insert the mid-article CTA inside <article> on cost/problems pages."""
    if not cta_lib.wants_mid_cta(slug, title):
        return html, "mid-skip-intent"
    if 'data-cta="mid"' in html:
        return html, "mid-present"
    m = re.search(r"(<article>)(.*?)(</article>)", html, re.S)
    if not m:
        return html, "no-article"
    new_body = cta_lib.insert_mid_cta(m.group(2), cta_lib.mid_cta_html(title, slug))
    if new_body == m.group(2):
        return html, "mid-no-slot"
    return html[: m.start()] + m.group(1) + new_body + m.group(3) + html[m.end():], "mid-added"


def patch_file(path):
    html = path.read_text(encoding="utf-8")
    if "wa.me/" + cta_lib.WA_NUM not in html:
        return "skipped", "no whatsapp link"

    name = path.name
    slug = path.stem
    title = title_of(html)
    is_article = (path.parent.name == "blog") and name != "index.html"

    notes = []
    if is_article:
        prefill = cta_lib.prefill_for(title, slug)
        # banner first (sets label/copy), then set_all overwrites all hrefs consistently
        html, b = rewrite_banner(html, title, slug)
        html, mid = add_mid_cta(html, title, slug)
        html = cta_lib.set_all_wa_prefill(html, prefill)
        notes += [f"prefill={prefill[:42]}...", b, mid]
    else:
        html = cta_lib.set_all_wa_prefill(html, cta_lib.GENERIC_QUOTE)
        notes += ["prefill=GENERIC_QUOTE"]

    path.write_text(html, encoding="utf-8")
    return "patched", " | ".join(notes)


def main():
    targets = [ROOT / n for n in ROOT_PAGES if (ROOT / n).exists()]
    targets += sorted(BLOG.glob("*.html"))

    print(f"Scanning {len(targets)} HTML files...\n")
    counts = {}
    for p in targets:
        status, detail = patch_file(p)
        counts[status] = counts.get(status, 0) + 1
        flag = "OK " if status == "patched" else "-- "
        print(f"  {flag}{status:8} {p.relative_to(ROOT)}\n        {detail}")

    print("\n" + "=" * 60)
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
