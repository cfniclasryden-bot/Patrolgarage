#!/usr/bin/env python3
"""Regression test for the 2026-11-20 editorial bans (copy_rules.EDITORIAL_RULES,
check_editorial.py). Identical in topchallenger-site and patrolgarage.

    python3 scripts/test_editorial.py

1. Every rule fires on a sentence that carries it and stays quiet on a clean one.
2. A new page (no baseline entry) is blocked by any hit, in body, title, meta
   or JSON-LD.
3. Every shipped page passes against the frozen baseline.
4. patrolgarage only: no EXPERT / SAME_DAY / BOOK_NOW in any title, meta or
   JSON-LD string. Those were removed on 2026-11-20 and may not come back,
   baseline or not.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_editorial  # noqa: E402
import copy_rules  # noqa: E402

fails = []


def rules_in(sent):
    return {r for _s, r, _m, _t in copy_rules.editorial_findings(f"<html><body><p>{sent}</p></body></html>")}


HITS = {
    "EXPERT": "Our expert team checks the gearbox.",
    "SAME_DAY": "Most jobs are a same-day repair.",
    "BOOK_NOW": "Book now and we will look at it.",
    "WARRANTY": "Every repair carries a warranty.",
    "APPROVED": "An approved workshop for the Y62.",
    "CERTIFIED": "Certified technicians do the work.",
    "GENUINE": "We fit genuine parts.",
    "BEST": "The best Y62 garage in Dubai.",
    "NUMBER_ONE": "The #1 Patrol specialist.",
    "DISC_SKIMMING": "We skim the brake discs when they are scored.",
    "RECOVERY": "Call our recovery truck if it will not start.",
    "PARTS_SALES": "We sell Y62 parts over the counter.",
}
for rule, sent in HITS.items():
    if rule not in rules_in(sent):
        fails.append(f"{rule} did not fire on: {sent}")
for clean in ("The gearbox is checked with a scan tool before anything is replaced.",
              "A whine that changes with road speed points to the differential.",
              "Send the model year and the mileage on WhatsApp.",
              # allowed since 2026-11-20 (OWNER-ANSWERS-2026-11-20.md)
              "We check the wheel alignment after desert driving.",
              "Tyre fitting, balancing and rotation are part of the visit."):
    if rules_in(clean):
        fails.append(f"clean sentence flagged {rules_in(clean)}: {clean}")

with tempfile.TemporaryDirectory() as d:
    for where, page in (
        ("body", "<html><head><title>Y62 gearbox</title></head><body><p>Our experts fix it.</p></body></html>"),
        ("title", "<html><head><title>Same-Day Y62 Repair</title></head><body><p>Fine.</p></body></html>"),
        ("meta", '<html><head><meta name="description" content="Book now for a check."></head><body></body></html>'),
        ("json-ld", '<html><head><script type="application/ld+json">{"description": "Best Y62 garage"}'
                    "</script></head><body></body></html>"),
    ):
        p = Path(d) / f"new-post-{where}.html"
        p.write_text(page, encoding="utf-8")
        if not check_editorial.new_findings(p, baseline={}):
            fails.append(f"a new page with a ban in its {where} was not blocked")

bad = {}
baseline = check_editorial.load_baseline()
for p in check_editorial.all_pages():
    nf = check_editorial.new_findings(p, baseline)
    if nf:
        bad[check_editorial.rel(p)] = nf
for page, nf in bad.items():
    for s, r, m, t in nf[:3]:
        fails.append(f"{page} [{s}] {r} {m!r}: {t[:100]}")

if not (ROOT / "scripts" / "site_config.py").exists():      # patrolgarage
    for p in check_editorial.all_pages():
        for s, r, m, t in copy_rules.editorial_findings(p.read_text(encoding="utf-8")):
            if s != "body" and r in ("EXPERT", "SAME_DAY", "BOOK_NOW"):
                fails.append(f"{check_editorial.rel(p)} [{s}] {r} back in a title/meta: {t[:100]}")

for f in fails:
    print("  FAIL ", f)
if fails:
    print(f"[!] editorial bans FAILED - {len(fails)} problem(s)")
    sys.exit(1)
print(f"[OK] editorial bans: {len(HITS)} rules fire, new pages blocked in every scope, "
      f"{len(check_editorial.all_pages())} shipped pages clean against the baseline")
