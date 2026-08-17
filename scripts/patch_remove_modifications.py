#!/usr/bin/env python3
"""Remove modifications as an offered service, everywhere it originates.

The workshop does not do modifications. Owner decision 2026-08-13.

BOUNDARY VERIFICATION. An earlier removal script took out an unintended second
card because its regex used a lazy `.*?` that had to cross nested <div>s to
reach three consecutive closing tags, and the preflight only checked the match
COUNT, not what the match actually contained. Every block removal here asserts
on the captured text before writing: exactly one <h3>/<h2>, the expected id or
label present, no second "service-card"/"service-article" inside it. A failed
assertion aborts the whole run.

WHAT CHANGES
  index.html   hero lede; meta description; og:description; schema description;
               the S/04 "Performance & Mods" card, whose link pointed at
               /services.html#modifications-performance-upgrades — a section
               that no longer exists, so it was a dead anchor; journal blurb.
  8 pages      the shared footer line "Y62 service, repair, and modifications."
  contact.html the "Modifications / Upgrades" enquiry-form option.
  generators   money_links.py (the "mods" anchor text AND its slug rule, which
               was actively inserting "Y62 modifications and performance
               upgrades" into matching posts), patch_tap_targets.py (mapping to
               the now-dead section id), directory_prep.py and
               patch_local_and_hub.py (both repeat the footer/meta line).

DELIBERATELY KEPT, per the owner:
  * Two blog headings that discuss modifications as owner information
    ("What modifications are essential for Dubai Y61s?") — information, not an
    offer, same call as the PPI market-data mentions.
  * The whole y62-turbo-upgrade post. "nissan patrol tuning dubai" earns 2
    clicks at position 5.8 and is one of only nine converting queries the site
    has. Retiring it to tidy vocabulary would cost real traffic.
  * The single money-link anchor already published in the tow-bar post is left
    alone here; the generator rule is fixed so it cannot spread.

mtimes preserved on anything under blog/.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HERO_OLD = ("A Dubai workshop built around one car. Diagnostics, repair, and modification "
            "by mechanics who know the Nissan Patrol inside-out.")
HERO_NEW = ("Engine work, gearbox and transmission, major servicing and diagnostics. "
            "One workshop in Ras Al Khor, one car: the Nissan Patrol.")

FOOTER_OLD = "Nissan Patrol specialists in Ras Al Khor, Dubai. Y62 service, repair, and modifications."
FOOTER_NEW = "Nissan Patrol specialists in Ras Al Khor, Dubai. Engine, gearbox, servicing and diagnostics."

# (path, description, old, new). Plain string swaps — no regex, no boundary risk.
SWAPS = [
    ("index.html", "hero lede", HERO_OLD, HERO_NEW),
    ("index.html", "meta description",
     "Patrols only: Y62 service, repair, diagnostics and modifications.",
     "Patrols only: engine, gearbox, major servicing and diagnostics."),
    ("index.html", "og:description",
     "Dubai's dedicated Nissan Patrol Y62 specialist. Y62 service, repair, diagnostics, and modifications.",
     "Dubai's dedicated Nissan Patrol Y62 specialist. Engine, gearbox, major servicing and diagnostics."),
    ("index.html", "schema description",
     "dedicated Nissan Patrol Y62 specialist garage. Y62 service, repair, diagnostics, and modifications.",
     "dedicated Nissan Patrol Y62 specialist garage. Engine, gearbox, major servicing and diagnostics."),
    ("index.html", "journal blurb",
     "Honest advice on common issues, real costs, and modifications — written for UAE conditions.",
     "Honest advice on common issues, real costs, and what the car actually needs — written for UAE conditions."),
    ("contact.html", "form option",
     '<option value="Modifications">Modifications / Upgrades</option>\n                ', ""),
    ("scripts/money_links.py", "mods anchor",
     '    "mods": "Y62 modifications and performance upgrades",\n', ""),
    ("scripts/money_links.py", "mods slug rule",
     '    (r"turbo|intercooler|snorkel|tow-bar|paint-protection|ppf|upgrade|modification", "mods"),\n', ""),
    ("scripts/patch_tap_targets.py", "dead card map",
     '    "Performance & Mods": "modifications-performance-upgrades",\n', ""),
    ("scripts/directory_prep.py", "directory blurb",
     "Nissan Patrol specialists in Dubai. Y62 service, repair, and modifications.",
     "Nissan Patrol specialists in Dubai. Engine, gearbox, servicing and diagnostics."),
    ("scripts/patch_local_and_hub.py", "homepage desc string",
     "Y62 service, repair, diagnostics and modifications.",
     "engine, gearbox, major servicing and diagnostics."),
]

# The footer is shared markup, so it is duplicated into EVERY page including all
# ~46 blog posts and the blog index/pagination. A hardcoded list missed them the
# first time; glob instead so a newly generated post can never be overlooked.
# mtimes under blog/ are preserved (sitemap lastmod reads them).
FOOTER_FILES = sorted(
    str(p.relative_to(ROOT))
    for p in ROOT.rglob("*.html")
    if "node_modules" not in p.parts
)

CARD_RE = re.compile(
    r'\s*<div class="service-card">\s*<div class="service-num"><span>S/04</span>.*?</div>\s*</div>',
    re.S)


def verify_card(captured):
    """Refuse the removal unless the captured text is EXACTLY one card."""
    problems = []
    if captured.count('<div class="service-card">') != 1:
        problems.append(f'{captured.count(chr(60)+"div class=" + chr(34) + "service-card" + chr(34) + chr(62))} service-card opens (want 1)')
    if captured.count("<h3>") != 1:
        problems.append(f"{captured.count('<h3>')} <h3> (want 1)")
    if "modifications-performance-upgrades" not in captured:
        problems.append("expected the modifications anchor, not found")
    if "S/05" in captured or "S/03" in captured:
        problems.append("captured a neighbouring card")
    return problems


def main():
    dry = "--dry-run" in sys.argv
    planned = []

    # --- plain swaps ------------------------------------------------------
    for rel, what, old, new in SWAPS:
        p = ROOT / rel
        if not p.exists():
            print(f"  !! missing {rel}"); return 1
        # a file may already be queued from an earlier swap; chain onto the
        # newest queued text, never a fresh read — the final write keeps only
        # the LAST entry per file, so an unchained swap silently loses the
        # earlier ones (index.html has 5, money_links.py has 2).
        h = next((t for pp, _, t in reversed(planned) if pp == p),
                 p.read_text(encoding="utf-8"))
        n = h.count(old)
        if n == 0:
            print(f"  clean  {rel:<34} {what}")
            continue
        if n > 1:
            print(f"  !! {rel} [{what}]: matched {n}x, expected 1 — aborting"); return 1
        planned.append((p, what, h.replace(old, new, 1)))
        print(f"  swap   {rel:<34} {what}")

    # --- footer line, 8 files --------------------------------------------
    for rel in FOOTER_FILES:
        p = ROOT / rel
        h = p.read_text(encoding="utf-8")
        if FOOTER_OLD not in h:
            print(f"  clean  {rel:<34} footer")
            continue
        if h.count(FOOTER_OLD) != 1:
            print(f"  !! {rel}: footer matched {h.count(FOOTER_OLD)}x — aborting"); return 1
        # a file may already be queued from SWAPS; chain onto the newest text
        base = next((t for pp, _, t in reversed(planned) if pp == p), h)
        planned.append((p, "footer", base.replace(FOOTER_OLD, FOOTER_NEW, 1)))
        print(f"  swap   {rel:<34} footer")

    # --- the dead-anchor card, WITH boundary verification -----------------
    p = ROOT / "index.html"
    base = next((t for pp, _, t in reversed(planned) if pp == p), p.read_text(encoding="utf-8"))
    ms = CARD_RE.findall(base)
    if not ms:
        print("  clean  index.html                        S/04 card (already gone)")
    elif len(ms) > 1:
        print(f"  !! index.html: S/04 pattern matched {len(ms)}x — aborting"); return 1
    else:
        problems = verify_card(ms[0])
        if problems:
            print("  !! S/04 capture failed verification, aborting:")
            for x in problems:
                print(f"       - {x}")
            return 1
        print(f"  remove index.html                        S/04 'Performance & Mods' card "
              f"({len(ms[0])} bytes, verified single card)")
        planned.append((p, "S/04 card", CARD_RE.sub("", base, count=1)))

    # collapse to the final text per file (last entry wins — every stage above
    # chains, so the last entry is cumulative)
    final = {}
    for p, _, text in planned:
        final[p] = text

    # Cross-check the collapse actually kept every edit. This is the guard for
    # the lose-an-earlier-swap bug: if any stage stops chaining, an old string
    # survives into the final text and we abort instead of writing a partial.
    lost = []
    for rel, what, old, _new in SWAPS:
        p = ROOT / rel
        if p in final and old and old in final[p]:
            lost.append(f"{rel} [{what}]")
    for rel in FOOTER_FILES:
        p = ROOT / rel
        if p in final and FOOTER_OLD in final[p]:
            lost.append(f"{rel} [footer]")
    if lost:
        print("\n  !! collapse dropped edits, aborting:")
        for x in lost:
            print(f"       - {x}")
        return 1
    print(f"\n  collapse verified — {len(final)} file(s), no edit lost")

    if dry:
        print("DRY RUN — nothing written")
        return 0
    for p, text in final.items():
        under_blog = "blog" in p.parts
        st = p.stat() if under_blog else None
        p.write_text(text, encoding="utf-8")
        if st:
            os.utime(p, (st.st_atime, st.st_mtime))
    print(f"\nWRITTEN — {len(final)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
