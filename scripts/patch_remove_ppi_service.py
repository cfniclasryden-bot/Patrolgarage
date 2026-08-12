#!/usr/bin/env python3
"""Remove pre-purchase inspection as an OFFERED SERVICE, at every source.

Context. The owner deleted PPI from the site and it came back — the second edit
of theirs to be undone. The trace (2026-08-13):

  * PPI is present in services.html in EVERY commit in the repo's history. The
    deletion never reached git, so nothing "restored" it in version control;
    the edit simply never persisted.
  * Root cause is the same revert trap that ate the prices: publish.py commits
    only blog/, images/, sitemap.xml and scripts/ — NEVER the root static
    pages — but the nightly run deploys with `netlify deploy --dir .` from the
    CONTAINER's own copy. So any edit to services.html / index.html /
    contact.html that is not followed by `railway up` is overwritten at 05:00.
  * Deleting the services.html card alone would not have held anyway, because
    PPI is an offered service in EIGHT other places, four of which are code
    that regenerates content.

This script removes it from every source of truth so it cannot come back:

  static pages
    services.html  the service card
    index.html     the S/06 service card AND the LocalBusiness schema
                   serviceType array
    contact.html   the enquiry-form dropdown option

  generators (the ones that would re-introduce it into NEW content)
    generate.py           the market-pricing line, so new daily posts stop
                          citing PPI pricing
    money_links.py        the "inspection" anchor + slug rule, which was
                          actively inserting "our Y62 pre-purchase inspection"
                          as an in-body money link on matching posts
    build_pillar_v3.py    pillar copy + price lines
    directory_prep.py     directory-listing blurb
    patch_tap_targets.py  the homepage card -> section id map

NOT touched, deliberately: blog posts. Discussing a pre-purchase inspection as
something a BUYER should get is legitimate educational content and is not an
offer. But several posts say "we offer / we run pre-purchase inspections at
Patrol Garage for AED X" — those are offers WITH prices and need rewriting.
They are published, ranking pages, so this script REPORTS them instead of
editing them. See the PPI_OFFER_CLAIMS output.

Idempotent. Run with --dry-run first.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (path, description, regex) — each must match at most once.
REMOVALS = [
    ("services.html", "service card",
     re.compile(r'\s*<div class="service-article" id="pre-purchase-inspection">.*?</div>\s*</div>\s*</div>', re.S)),
    ("index.html", "homepage S/06 card",
     re.compile(r'\s*<div class="service-card">\s*<div class="service-num"><span>S/06</span>.*?</div>\s*</div>', re.S)),
    ("contact.html", "enquiry-form option",
     re.compile(r'\s*<option value="Pre-Purchase">[^<]*</option>')),
]

# Simple string edits in the generators.
EDITS = [
    ("index.html", "schema serviceType",
     '"serviceType": ["Nissan Patrol Service", "Nissan Patrol Repair", "Nissan Patrol Diagnostics", "Suspension Lift Kits", "AC Repair", "Pre-Purchase Inspection"]',
     '"serviceType": ["Nissan Patrol Service", "Nissan Patrol Repair", "Nissan Patrol Diagnostics", "Suspension Lift Kits", "AC Repair"]'),
    ("scripts/generate.py", "market-pricing line",
     "- Pre-purchase inspection: AED 500-800\n", ""),
    ("scripts/money_links.py", "anchor text",
     '    "inspection": "our Y62 pre-purchase inspection",\n', ""),
    ("scripts/money_links.py", "slug rule",
     '    (r"pre-purchase|inspection", "inspection"),\n', ""),
    ("scripts/patch_tap_targets.py", "homepage card map",
     '    "Pre-Purchase Inspection": "pre-purchase-inspection",\n', ""),
    ("scripts/build_pillar_v3.py", "pillar price line A",
     "- Pre-purchase inspection AED 400-800\n", ""),
    ("scripts/directory_prep.py", "directory blurb",
     "suspension work, or pre-purchase ", "suspension work, or diagnostic "),
]

OFFER_CLAIM = re.compile(
    r'[^.<>]*\b(?:we (?:offer|run|provide|do)|our)\b[^.<>]*pre-?purchase inspection[^.<>]*\.',
    re.I)


def apply(dry):
    changed = 0
    for rel, what, rx in REMOVALS:
        p = ROOT / rel
        h = p.read_text(encoding="utf-8")
        n = len(rx.findall(h))
        if n == 0:
            print(f"  clean  {rel:<22} {what}")
            continue
        if n > 1:
            print(f"  !! {rel}: {what} matched {n}x — refusing, tighten the pattern")
            return -1
        if not dry:
            p.write_text(rx.sub("", h, count=1), encoding="utf-8")
        print(f"  remove {rel:<22} {what}")
        changed += 1

    for rel, what, old, new in EDITS:
        p = ROOT / rel
        h = p.read_text(encoding="utf-8")
        if old not in h:
            print(f"  clean  {rel:<22} {what}")
            continue
        if not dry:
            p.write_text(h.replace(old, new, 1), encoding="utf-8")
        print(f"  edit   {rel:<22} {what}")
        changed += 1
    return changed


def report_offer_claims():
    print("\n=== PPI OFFER CLAIMS IN PUBLISHED POSTS (reported, NOT edited) ===")
    hits = 0
    for p in sorted((ROOT / "blog").glob("*.html")):
        if p.name == "index.html":
            continue
        text = re.sub(r"<[^>]+>", " ", p.read_text(errors="ignore"))
        for m in OFFER_CLAIM.finditer(text):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            if "inspection" in s.lower():
                hits += 1
                print(f"  {p.name}\n     \"{s[:150]}\"")
    print(f"\n  {hits} passage(s) present PPI as something Patrol Garage offers.")
    print("  These are published, ranking pages — rewrite them deliberately, not with a regex.")


def main():
    dry = "--dry-run" in sys.argv
    n = apply(dry)
    if n < 0:
        print("\nABORTED")
        return 1
    report_offer_claims()
    print("\n" + ("DRY RUN — nothing written" if dry else f"WRITTEN — {n} source(s) changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
