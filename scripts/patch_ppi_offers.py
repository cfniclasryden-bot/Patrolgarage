#!/usr/bin/env python3
"""Strip pre-purchase inspection as something Patrol Garage SELLS, from published posts.

Approved 2026-08-13. The garage does not offer PPI. The buyer's-guide content
stays — it ranks and it is genuinely useful — but every passage presenting PPI
as our service is reframed as advice about what a good inspection involves and
what the market charges.

Deliberately KEPT (owner's decision): two passages that quote a PPI price while
describing OTHER workshops. They are market data, which is the educational cost
content that is allowed:
  * specialist-abu-dhabi: "We see pre-purchase inspections priced between AED 400
    and 800 at specialist workshops"
  * y63-independent (cost list): "Pre-purchase inspection on a used Y63: AED 400
    to AED 800"

Every replacement below must match EXACTLY ONCE or the script aborts without
writing anything — these are ranking pages and a sloppy regex is worse than no
edit. No em dashes are introduced (site style rule). MONEYLINK markers and
/services.html links are untouched. mtimes preserved, because journal_update.py
derives displayed dates and listing order from them.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

EDITS = [
    # ---- the PPI guide itself: CTA banner pivots to what we actually sell ----
    ("nissan-patrol-pre-purchase-inspection.html", "CTA banner",
     "<h2>Get Expert Inspection Before Buying</h2><p>We provide comprehensive "
     "pre-purchase inspections for Patrol Y61 & Y62. Uncover hidden issues before "
     "you commit.</p>",
     "<h2>Just Bought a Patrol?</h2><p>Once it is yours, we can go through it "
     "properly. VK56VD diagnostics, JR710E gearbox checks and cooling work at our "
     "Ras Al Khor workshop.</p>"),

    # ---- Y62 complete guide (4) ----
    ("nissan-patrol-y62-dubai-complete-guide.html", "quick answer",
     "Before buying any used Patrol, a pre-purchase inspection is non-negotiable. "
     "We run them at our Ras Al Khor workshop for AED 500 to 800.",
     "Before buying any used Patrol, a pre-purchase inspection is non-negotiable. "
     "Independent specialists in the UAE typically charge AED 500 to 800 for one."),

    ("nissan-patrol-y62-dubai-complete-guide.html", "calibrated-to-Y62 para",
     "At Patrol Garage, our pre-purchase inspections are specifically calibrated to "
     "catch the Y62 failure patterns we see repeatedly:",
     "A good Y62 inspection is calibrated to the failure patterns that show up "
     "repeatedly on this model:"),

    ("nissan-patrol-y62-dubai-complete-guide.html", "highest-ROI para",
     "problems our inspection flagged before they signed.",
     "problems an inspection flagged before they signed."),

    ("nissan-patrol-y62-dubai-complete-guide.html", "30-point scope A",
     "Our Y62 pre-purchase inspection covers 30+ points calibrated specifically to "
     "this model's known failure patterns:",
     "A thorough Y62 pre-purchase inspection covers 30+ points calibrated to this "
     "model's known failure patterns:"),

    ("nissan-patrol-y62-dubai-complete-guide.html", "30-point scope B",
     "You get a written report with every item rated and a clear recommendation on "
     "whether the vehicle is worth buying at the asking price. We also quote for any "
     "work required so you can negotiate accordingly.",
     "A good one gives you a written report with every item rated and a clear "
     "recommendation on whether the vehicle is worth buying at the asking price, plus "
     "a quote for any work required so you can negotiate accordingly."),

    # ---- PPF cost post ----
    ("nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html", "offer + price",
     "We offer pre-purchase inspections at Patrol Garage from AED 400 to AED 800, and "
     "we check panel gaps and paint depth readings even where film is present.",
     "Specialist workshops in the UAE charge from AED 400 to AED 800, and a good one "
     "checks panel gaps and paint depth readings even where film is present."),

    # ---- specialist Abu Dhabi vs Dubai ----
    ("nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html", "service list + CTA",
     "suspension overhauls, AC work, and pre-purchase inspections for buyers in both "
     "Dubai and Abu Dhabi. If you are seeing transmission symptoms, planning a major "
     "service on a high-mileage Y62, or want a proper inspection before buying a used "
     "example, call us or request a quote.",
     "suspension overhauls and AC work for owners in both Dubai and Abu Dhabi. If you "
     "are seeing transmission symptoms, planning a major service on a high-mileage "
     "Y62, or want a second opinion on a quote you have received elsewhere, call us or "
     "request a quote."),

    # ---- Y62 vs Y63 (2) ----
    ("nissan-patrol-y62-vs-y63-dubai-comparison.html", "recommend + our check",
     "We always recommend a pre-purchase inspection (AED 400-800 at Patrol Garage) for "
     "any used Y62 — our 30-point Y62-specific check catches the common issues "
     "before you commit to a purchase. We cover transmission condition, AC system "
     "health, and suspension components, including",
     "We always recommend a pre-purchase inspection (AED 400-800 at UAE specialist "
     "workshops) for any used Y62. A proper 30-point Y62-specific check catches the "
     "common issues before you commit to a purchase. It should cover transmission "
     "condition, AC system health, and suspension components, including"),

    ("nissan-patrol-y62-vs-y63-dubai-comparison.html", "we specialize list",
     "We specialize in Patrol-specific services, from pre-purchase inspections to "
     "comprehensive maintenance programs designed for UAE conditions.",
     "We specialize in Patrol-specific services, from diagnostics to comprehensive "
     "maintenance programs designed for UAE conditions."),

    # ---- Y63 independent service centre ----
    ("y63-independent-service-centre-abu-dhabi-vs-dubai-2026.html", "closing CTA list",
     "If you have a Y63 and need a major service, a pre-purchase inspection on a used "
     "example, adaptive suspension work, or a second opinion on a quote you have "
     "received elsewhere, call us first.",
     "If you have a Y63 and need a major service, adaptive suspension work, or a "
     "second opinion on a quote you have received elsewhere, call us first."),
]


def main():
    dry = "--dry-run" in sys.argv

    # Preflight: every old string must appear exactly once. Abort as a whole if not.
    problems = []
    for fn, what, old, new in EDITS:
        p = BLOG / fn
        if not p.exists():
            problems.append(f"{fn}: MISSING FILE")
            continue
        n = p.read_text(encoding="utf-8").count(old)
        if n != 1:
            problems.append(f"{fn} [{what}]: matched {n}x, expected exactly 1")
    if problems:
        print("PREFLIGHT FAILED — nothing written:")
        for x in problems:
            print("  !!", x)
        return 1
    print(f"preflight OK — all {len(EDITS)} edits match exactly once\n")

    # Apply, grouped per file so each file is written once.
    by_file = {}
    for fn, what, old, new in EDITS:
        by_file.setdefault(fn, []).append((what, old, new))

    for fn, edits in by_file.items():
        p = BLOG / fn
        html = p.read_text(encoding="utf-8")
        before_dashes = html.count("—") + html.count("–")
        for what, old, new in edits:
            html = html.replace(old, new, 1)
            print(f"  {fn}  [{what}]")
        after_dashes = html.count("—") + html.count("–")
        if after_dashes > before_dashes:
            print(f"  !! {fn}: em/en dash count rose {before_dashes} -> {after_dashes}, aborting")
            return 1
        if not dry:
            st = p.stat()
            p.write_text(html, encoding="utf-8")
            os.utime(p, (st.st_atime, st.st_mtime))  # mtime is content

    print("\n" + ("DRY RUN — nothing written" if dry else
                 f"WRITTEN — {len(EDITS)} edits across {len(by_file)} posts"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
