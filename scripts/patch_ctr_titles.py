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

ROUND 2, 2026-11-12 (CTR notes; compare on or after 2026-12-10, 4 weeks).
Round 1 did not move CTR: GSC page totals, final data,
  complete guide  08-10..10-06 5,651 impr, 39 clicks, 0.69%, pos 6.9
                  10-08..11-09 1,258 impr, 10 clicks, 0.79%, pos 7.3   (round-1 title)
  fuel post       08-10..10-06 2,528 impr,  4 clicks, 0.16%, pos 7.1
                  10-08..11-09 2,982 impr,  9 clicks, 0.30%, pos 6.5   (round-1 title)
Top queries 08-10..11-09 (impr, pos, CTR):
  guide: "nissan patrol y61 y62 y63 present" 1,589 5.3 0.1% (a generations lookup,
      expect low CTR whatever the title); "y62" 506 5.7 0.6%; "nissan patrol y62"
      337 13.9 0.0% (a ranking problem, not a title one); "nissan patrol y62 buying
      guide" 183 10.5 3.8%; "nissan y62" 181 6.1 1.1%; "patrol y62" 127 6.0 0.0%.
  fuel: "nissan patrol fuel consumption" 89 7.0 0.0%; "nissan patrol 2026 fuel
      consumption" 58 5.7 0.0%; "nissan patrol mileage per liter" 58 6.2 0.0%;
      "nissan patrol mileage" 48 13.2 2.1%; "nissan patrol fuel average" 43 9.4 0.0%.
Changes, user-approved 2026-11-12:
  guide: broad Y62 title (no Y63, not colliding with the problems, Y61-vs-Y62 and
      pre-purchase posts); description without Y63.
  fuel: "2026" dropped (it matched 2026-model, i.e. Y63, searches); the round-1
      description said "13-14 on the highway" but the body says 14 to 16 L/100km:
      fixed; km/l from the body's figures (100/22 to 100/18 = 4.5 to 5.6). H1 changed
      by hand from "Patrol Fuel Costs Explained" to "Nissan Patrol Fuel Consumption
      in the UAE" (this script does not touch H1s).
  links: in-text link to the guide added by hand in the first paragraph of
      nissan-patrol-y62-vs-y63-dubai-comparison (anchor "Nissan Patrol Y62") and of
      nissan-patrol-y61-vs-y62-dubai (anchor "Y62"), so the guide is the page for
      "y62" / "nissan patrol y62". Hub banner unchanged.
Read on 2026-12-10: page CTR and position from 11-13 on, and the position of
"nissan patrol y62" on the guide (13.9 before).

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
    # Round 2, 2026-11-12 (see the note at the top). Round 1 (2026-10-07) was:
    #   "Nissan Patrol Y62 Buying Guide: vs Y61 and Y63 in the UAE"
    #   "Nissan Patrol Fuel Consumption 2026: Real UAE L/100km & km/l"
    "nissan-patrol-y62-dubai-complete-guide": (
        "Nissan Patrol Y62: Complete UAE Owner and Buyer Guide",
        "Buying or running a Y62 Patrol in the UAE? How it compares with the Y61, "
        "the common faults to look for, and the checks to do before you buy.",
    ),
    "nissan-patrol-fuel-consumption": (
        "Nissan Patrol Fuel Consumption: Real km/l and L/100km, UAE",
        "Y62 Patrol fuel average in the UAE: 18 to 22 L/100km in city traffic (about "
        "4.5 to 5.6 km/l) and 14 to 16 on the highway. Why summer AC pushes it up.",
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
