#!/usr/bin/env python3
"""Rewrite titles on cost-intent posts + one weak meta description.

Measured problem (2026-08-13). Google truncates by PIXEL WIDTH, not characters:
21 of 44 titles exceeded the ~600px desktop cut. In every single case the only
thing being cut was the brand suffix "| Patrol Garage Dubai" — keywords and the
year always survived. So the pages were not losing keywords, they were spending
~180px rendering "Patrol Garag…" mid-word.

Option A (owner's decision): reclaim that space with a differentiator, NOT with
a price. Prices stay out of titles because the per-article figures come from the
same unverified generation that produced the price block replaced in
generate.py. That includes removing the AED range from the water-pump title,
which was the one post that already carried one.

Every replacement below was measured at 20px Arial and fits inside 600px.
Primary keyword and year are preserved in all of them, so ranking signals are
unchanged.

Also fixes nissan-patrol-service-cost-dubai's description — the only cost post
whose description contained no figure at all, despite the article carrying them.

Preserves mtimes: journal_update.py derives displayed dates and listing order
from mtime, and publish.py runs it on every deploy.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

# slug -> new <title>.  Measured px in the comment.
TITLES = {
    "nissan-patrol-transmission-rebuild-cost-dubai-aed":
        "Nissan Patrol Transmission Rebuild Cost Dubai AED 2026",            # 517
    "nissan-patrol-y62-driveshaft-repair-cost-dubai-2026":
        "Nissan Patrol Y62 Driveshaft Repair Cost Dubai 2026",               # 475
    "y62-spark-plug-replacement-cost-al-futtaim-vs-independent":
        "Y62 Spark Plug Cost 2026: Al-Futtaim vs Independent",               # 480
    "y62-water-pump-replacement-cost-uae-2026":
        "Y62 Water Pump Replacement Cost UAE 2026",                          # price removed
    "nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026":
        "Y62 Coolant Temperature Sensor Cost UAE 2026: Part + Labour",       # 573
    "nissan-patrol-y62-head-gasket-replacement-cost-uae":
        "Y62 Head Gasket Replacement Cost UAE 2026: What Drives It",         # 561
    "y62-crankshaft-position-sensor-replacement-cost-dubai-2026":
        "Y62 Crankshaft Position Sensor Cost Dubai 2026: Which One",         # 548
    "y62-fuel-pressure-regulator-replacement-cost-dubai-2026":
        "Y62 Fuel Pressure Regulator Cost Dubai 2026: In-Tank Job",          # 527
    "nissan-patrol-differential-repair-cost-uae":
        "Nissan Patrol Differential Repair Cost UAE 2026",                   # 428
    "y61-super-safari-snorkel-fitting-cost-dubai-2026":
        "Y61 Super Safari Snorkel Fitting Cost Dubai 2026",                  # 440
    "y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026":
        "Y62 VK56 Valve Cover Gasket Cost Dubai 2026",                       # 427
    "y63-dashcam-installation-specialist-dubai-best-price-2026":
        "Y63 Dashcam Installation Dubai 2026: Hardwired Setup",              # 495
}

# slug -> new meta description.
DESCRIPTIONS = {
    "nissan-patrol-service-cost-dubai":
        "What a Nissan Patrol service costs in Dubai: minor service AED 400-700, "
        "major AED 1,000-1,500, plus AC, brakes and gearbox. What each one includes.",
}


def patch(path, dry):
    slug = path.stem
    html = path.read_text(encoding="utf-8")
    original = html
    notes = []

    if slug in TITLES:
        new = TITLES[slug]
        old_m = re.search(r"<title>(.*?)</title>", html, re.S)
        old = old_m.group(1) if old_m else ""
        if old != new:
            html = re.sub(r"<title>.*?</title>", f"<title>{new}</title>", html, count=1, flags=re.S)
            notes.append("title")
            # Keep og/twitter titles in step ONLY where they mirrored the old one.
            for attr, tag in (("property", "og:title"), ("name", "twitter:title")):
                rx = re.compile(rf'(<meta {attr}="{tag}" content=")([^"]*)(">)')
                m = rx.search(html)
                if m and m.group(2).strip() == old.strip():
                    html = rx.sub(rf'\g<1>{new}\g<3>', html, count=1)
                    notes.append(tag)

    if slug in DESCRIPTIONS:
        new = DESCRIPTIONS[slug]
        rx = re.compile(r'(<meta name="description" content=")([^"]*)(">)')
        if rx.search(html) and rx.search(html).group(2) != new:
            html = rx.sub(rf'\g<1>{new}\g<3>', html, count=1)
            notes.append("description")

    if html == original:
        return None
    if not dry:
        st = path.stat()
        path.write_text(html, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))  # mtime is content
    return notes


def main():
    dry = "--dry-run" in sys.argv
    want = set(TITLES) | set(DESCRIPTIONS)
    done = 0
    for slug in sorted(want):
        p = BLOG / f"{slug}.html"
        if not p.exists():
            print(f"  !! MISSING {p.name}")
            continue
        notes = patch(p, dry)
        if notes:
            done += 1
            print(f"  patched {slug}  [{', '.join(notes)}]")
        else:
            print(f"  nochange {slug}")
    print("\n" + ("DRY RUN — nothing written" if dry else f"WRITTEN — {done}/{len(want)} posts"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
