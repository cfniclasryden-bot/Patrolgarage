#!/usr/bin/env python3
"""CTR title and description rewrites, 2026-10-07 (PERFORMANCE-REVIEW-2026-10-07.md).

Four posts with real impressions and a CTR that the title explains. Each new
title was written against the page's own 90-day GSC queries (7 Jul - 4 Oct):

  nissan-patrol-y62-dubai-complete-guide   6,724 impr, pos 7.2. Ranks 6-8 for
      "y62" (474), "nissan y62" (199), "patrol y62" (122), and 16.8 for
      "nissan patrol y62" (370), under a title that led with Y61. Its best click
      source is "nissan patrol y62 buying guide" (118 impr, 7 clicks), which is
      already the H1. Title now leads with exactly that.
  nissan-patrol-fuel-consumption           2,413 impr, CTR 0.2%. Searches ask for
      a number in the unit they use: "mileage per liter", "km/l", "fuel average",
      "2026 fuel consumption". The description now gives the figures the body
      states, with the km/l conversion (100 / 18-22 L/100km = 4.5-5.5 km/l).
  nissan-patrol-best-year-to-buy           388 impr, CTR 0.8%, pos 4.8. Searches
      are "best nissan patrol year (model)". The page's answer, since the round-3
      reframe, is that the service history matters more than the year, so the
      title asks the searcher's question and gives that answer.
  nissan-patrol-diesel-vs-petrol           241 impr, CTR 0.4%. Searches are a
      yes/no question ("is nissan patrol diesel or petrol"); the title answers it.

Not colliding with topchallenger.ae: no title here uses specialist, garage,
workshop, repair or a location claim, and topchallenger.ae has no buying, fuel or
diesel posts. Every title measured at 20px Arial under the ~600px desktop cut
(538, 578, 545, 536), descriptions 149-155 characters.

<title>, meta description, og:title/og:description and twitter:title/description
are set together, because Google uses og:title for the title link on this site
(see the note in index.html). Article bodies, H1s and JSON-LD are untouched.

    python3 scripts/patch_ctr_titles.py           # dry run
    python3 scripts/patch_ctr_titles.py --write   # writes, preserving mtimes
"""
import html as _html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

PAGES = {
    "nissan-patrol-y62-dubai-complete-guide": (
        "Nissan Patrol Y62 Buying Guide: vs Y61 and Y63 in the UAE",
        "The Nissan Patrol Y62 explained for UAE buyers: how it compares with the Y61 "
        "and the new Y63, what goes wrong on each, and what to check before you buy.",
    ),
    "nissan-patrol-fuel-consumption": (
        "Nissan Patrol Fuel Consumption 2026: Real UAE L/100km & km/l",
        "Real Nissan Patrol fuel use in the UAE: a Y62 V8 does 18-22 L/100km (about "
        "4.5-5.5 km/l) in city traffic and 13-14 on the highway. Y61 and Y63 V6 compared.",
    ),
    "nissan-patrol-best-year-to-buy": (
        "Best Nissan Patrol Y62 Year? Check the Service History First",
        "Which Nissan Patrol year is best? On a used Y62 in the UAE the service history "
        "matters more than the build year. What to check, and the known faults.",
    ),
    "nissan-patrol-diesel-vs-petrol": (
        "Is the Nissan Patrol Diesel or Petrol? The Y62 Is Petrol-Only",
        "The Y62 and the new Y63 are petrol-only in the UAE; diesel exists only on the "
        "older Y61. Fuel use, upkeep and off-road ability compared for UAE owners.",
    ),
}


def _set_meta(page, attr, key, value):
    rx = re.compile(rf'(<meta {attr}="{re.escape(key)}" content=")([^"]*)(")')
    if not rx.search(page):
        raise SystemExit(f"[!] no <meta {attr}=\"{key}\"> found")
    return rx.sub(lambda m: m.group(1) + value + m.group(3), page, count=1)


def patch(slug, title, desc):
    path = BLOG / f"{slug}.html"
    page = path.read_text(encoding="utf-8")
    t, d = _html.escape(title, quote=True), _html.escape(desc, quote=True)
    new = re.sub(r"<title>.*?</title>", lambda _m: f"<title>{t}</title>", page, count=1, flags=re.S)
    new = _set_meta(new, "name", "description", d)
    new = _set_meta(new, "property", "og:title", t)
    new = _set_meta(new, "property", "og:description", d)
    new = _set_meta(new, "name", "twitter:title", t)
    new = _set_meta(new, "name", "twitter:description", d)
    return path, page, new


def main():
    write = "--write" in sys.argv[1:]
    for slug, (title, desc) in PAGES.items():
        path, old, new = patch(slug, title, desc)
        if old == new:
            print(f"[=] {slug}: already current")
            continue
        was = re.search(r"<title>(.*?)</title>", old, re.S).group(1)
        print(f"[+] {slug}\n      was: {was}\n      now: {title}")
        if write:
            st = path.stat()
            path.write_text(new, encoding="utf-8")
            os.utime(path, (st.st_atime, st.st_mtime))  # mtime is the displayed date


if __name__ == "__main__":
    main()
