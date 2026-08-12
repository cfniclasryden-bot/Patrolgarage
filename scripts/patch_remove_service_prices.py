#!/usr/bin/env python3
"""Remove Patrol Garage's OWN service pricing from the static pages.

Scope, per the 2026-08-12 decision: no prices for OUR services. Educational cost
content in the blog stays — those articles explain typical UAE market costs and
are what the cost-intent queries rank for. This script deliberately does NOT
touch blog/, and does NOT touch generate.py's "TYPICAL UAE WORKSHOP PRICING
(plausible ranges)" block, which is market context for that educational content.

What it removes:
  services.html  8x  <span>PRICE: AED …</span>
                 1x  <span>DIAGNOSTIC FEE: AED 300 (waived with repair)</span>
                     The sibling <span>TIME: …</span> stays — that is scope, not
                     price, and each card already ends in "Quote via WhatsApp".
  index.html     1x  "priceRange": "AED 500 - 5000" in the LocalBusiness schema.
                     That is the business's own advertised price band.

Left in place on index.html: the journal card excerpt "Real AED prices for minor
service…", which is the meta description of the service-cost ARTICLE, i.e.
educational content, not a service price. Flagged rather than changed.

Idempotent: reports "clean" when there is nothing left to remove.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A price span, with the whitespace before it so removal leaves no blank line.
PRICE_SPAN = re.compile(
    r'\s*<span>(?:PRICE|DIAGNOSTIC FEE)\s*:[^<]*</span>', re.I)

# "priceRange": "AED 500 - 5000",   (with or without a trailing comma)
PRICE_RANGE = re.compile(r'\s*"priceRange"\s*:\s*"[^"]*"\s*,?')


def patch_services(dry):
    p = ROOT / "services.html"
    html = p.read_text(encoding="utf-8")
    hits = PRICE_SPAN.findall(html)
    if not hits:
        print("  clean  services.html (no service price spans)")
        return 0
    new = PRICE_SPAN.sub("", html)
    for h in hits:
        print(f"    - {h.strip()}")
    if not dry:
        p.write_text(new, encoding="utf-8")
    print(f"  patch  services.html: removed {len(hits)} price span(s)")
    return len(hits)


def patch_index(dry):
    p = ROOT / "index.html"
    html = p.read_text(encoding="utf-8")
    hits = PRICE_RANGE.findall(html)
    if not hits:
        print("  clean  index.html (no priceRange)")
        return 0
    new = PRICE_RANGE.sub("", html)
    for h in hits:
        print(f"    - {h.strip()}")
    # The schema must still parse after the property is dropped.
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         new, re.S):
        try:
            json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(f"  !! index.html ld+json would not parse after removal: {e}")
            return -1
    if not dry:
        p.write_text(new, encoding="utf-8")
    print(f"  patch  index.html: removed {len(hits)} priceRange")
    return len(hits)


def main():
    dry = "--dry-run" in sys.argv
    a = patch_services(dry)
    b = patch_index(dry)
    if a < 0 or b < 0:
        print("\nABORTED — schema validation failed, nothing written")
        return 1
    print("\n" + ("DRY RUN — nothing written" if dry else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
