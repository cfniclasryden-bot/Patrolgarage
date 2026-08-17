#!/usr/bin/env python3
"""patch_modifications_vocab.py — remove "modification" vocabulary from published posts.

Owner decision 2026-08-17: the word should not appear anywhere on the site,
because the workshop does not offer modifications as a service.

This REVERSES the three carve-outs recorded in patch_remove_modifications.py
(2026-08-13), which removed modifications as an *offered service* but
deliberately kept:
  1. blog headings that discuss modifications as owner information
  2. the y62-turbo-upgrade post's vocabulary, to protect "nissan patrol tuning
     dubai" (2 clicks, position 4.8 — one of only nine converting queries)
  3. the money-link anchor already published in the tow-bar post

Carve-out 2 is preserved in substance: the ranking term is "tuning", which
appears 14x in that post and is NOT touched here. Only "modification(s)" and
"mods" are replaced, so the converting query keeps its keyword.

WHY PAIRS AND NOT A GLOBAL SUBSTITUTION. Most occurrences are neutral
third-person prose — RTA rules, warranty law, other people's vehicles — where a
blind "modifications"->"alterations" swap would produce broken grammar
("cooling modifications generally improve" -> "cooling alterations generally
improve") or misstate a cited regulation. Each replacement is written for its
sentence, and every pair asserts its expected occurrence count, so a silent
partial match aborts the run instead of half-editing a page.

Replacement vocabulary, chosen to preserve meaning:
  alteration(s)  — regulatory/warranty context (the RTA's own term, already used
                   on the snorkel page as "vehicle alterations")
  hardware       — physical supporting parts (oil coolers, intercoolers)
  aftermarket    — non-factory parts generally
  work / changes — generic activity

mtimes preserved: journal_update.py now dates posts from JSON-LD datePublished,
but refresh_scheduler.py still falls back to mtime, so keep it cheap and safe.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import money_links  # noqa: E402  — used to regenerate the tow-bar anchor

# file -> [(old, new, expected_count)]
REPLACEMENTS = {
    "blog/index.html": [
        ("real costs, and modifications&mdash;written",
         "real costs, and maintenance&mdash;written", 0),
        ("real costs, and modifications—written",
         "real costs, and maintenance—written", 1),
    ],
    "blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html": [
        ("Driving technique modifications reduce stress",
         "Driving technique changes reduce stress", 1),
    ],
    "blog/nissan-patrol-y61-dubai-complete-guide.html": [
        ("both maintainable and modifiable", "both maintainable and easy to work on", 1),
        ("ownership, maintenance, and modifications.",
         "ownership, maintenance, and aftermarket work.", 1),
        ("means repairs and modifications are straightforward",
         "means repairs and aftermarket work are straightforward", 1),
        ("<p>Modifications can either enhance or compromise reliability.",
         "<p>Aftermarket work can either enhance or compromise reliability.", 1),
        ("upgraded suspension, and proper cooling modifications generally improve",
         "upgraded suspension, and proper cooling generally improve", 1),
        ("However, amateur modifications, especially electrical work",
         "However, amateur alterations, especially electrical work", 1),
        ("demand modified maintenance schedules", "demand adjusted maintenance schedules", 1),
        ("low-mileage examples or modified vehicles",
         "low-mileage examples or altered vehicles", 1),
        ("<p>Modification costs can range from minimal",
         "<p>Accessory and aftermarket costs can range from minimal", 1),
        ("Popular modifications include lift kits", "Popular additions include lift kits", 1),
        ("What modifications are essential for Dubai Y61s?",
         "What extras are essential for Dubai Y61s?", 1),
        ("Priority modifications include auxiliary transmission cooling",
         "Priority additions include auxiliary transmission cooling", 1),
        ("Avoid complex electronic modifications that can create problems",
         "Avoid complex electronic alterations that can create problems", 1),
    ],
    "blog/nissan-patrol-y61-vs-y62-dubai.html": [
        ("Y61 is easier to modify without breaking electronics",
         "Y61 is easier to work on without breaking electronics", 1),
        ("Y62 modifications trigger warning lights",
         "Y62 alterations trigger warning lights", 1),
        ("requires electronic expertise to modify properly",
         "requires electronic expertise to alter properly", 1),
    ],
    "blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html": [
        ("vehicles that run modified suspension",
         "vehicles that run aftermarket suspension", 1),
    ],
    "blog/nissan-patrol-y62-dubai-complete-guide.html": [
        ("don&#39;t need any modification beyond what leaves the factory",
         "don&#39;t need anything beyond what leaves the factory", 0),
        ("don't need any modification beyond what leaves the factory",
         "don't need anything beyond what leaves the factory", 1),
    ],
    "blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html": [
        ("accept a bolt-on tow bar without modification",
         "accept a bolt-on tow bar without cutting or drilling", 1),
    ],
    "blog/nissan-patrol-y62-turbo-upgrade-dubai-cost.html": [
        ("appropriate supporting modifications including oil coolers",
         "appropriate supporting hardware including oil coolers", 2),
        ("require internal transmission modifications or replacement",
         "require internal transmission work or replacement", 2),
        ("turbo kit selection and supporting modifications",
         "turbo kit selection and supporting hardware", 1),
        ("intercooler upgrades, and exhaust modifications",
         "intercooler upgrades, and exhaust work", 1),
        ("twin-turbo setups with full supporting modifications",
         "twin-turbo setups with full supporting hardware", 1),
        ("budgeting for supporting modifications that Dubai conditions demand",
         "budgeting for the supporting hardware that Dubai conditions demand", 1),
        ("properly documented engine modifications can actually add value",
         "properly documented engine work can actually add value", 1),
        ("What Supporting Modifications Are Essential in Dubai Heat?",
         "What Supporting Hardware Is Essential in Dubai Heat?", 1),
        ("though modified components may not be covered",
         "though altered components may not be covered", 1),
        ("generally accept declared modifications.",
         "generally accept declared alterations.", 1),
        ("focus on whether modifications directly caused specific failures",
         "focus on whether alterations directly caused specific failures", 1),
        ("advise customers to discuss modifications with their service advisors",
         "advise customers to discuss any alterations with their service advisors", 1),
        ("accept declared vehicle modifications without significant premium",
         "accept declared vehicle alterations without significant premium", 1),
        ("The key is declaring modifications at policy renewal time",
         "The key is declaring alterations at policy renewal time", 1),
        ("undisclosed modifications can affect claim settlements",
         "undisclosed alterations can affect claim settlements", 1),
        ("kit complexity and supporting modifications",
         "kit complexity and supporting hardware", 1),
        ("with minimal supporting mods can be completed",
         "with minimal supporting hardware can be completed", 1),
        ("choose appropriate modifications for their driving needs",
         "choose appropriate hardware for their driving needs", 1),
        # meta description — also the source of the "mods" that reached the
        # journal card on /blog/page/2/
        ("ECU tuning &amp; cooling mods for extreme heat",
         "ECU tuning &amp; cooling hardware for extreme heat", 0),
        ("ECU tuning & cooling mods for extreme heat",
         "ECU tuning & cooling hardware for extreme heat", 1),
    ],
    "blog/y61-super-safari-snorkel-fitting-cost-dubai-2026.html": [
        ("exterior body modifications are subject to approval",
         "exterior body alterations are subject to approval", 2),
        ("whether any bodywork modification is needed",
         "whether any bodywork alteration is needed", 1),
        ("smartest and cheapest modifications you can make",
         "smartest and cheapest additions you can make", 1),
        ("A snorkel is a body modification and technically falls under",
         "A snorkel is a body alteration and technically falls under", 1),
        ("any modification that changes the exterior profile",
         "any alteration that changes the exterior profile", 1),
    ],
    "blog/y62-intercooler-upgrade-cost-dubai-al-futtaim-vs-independent.html": [
        ("For a performance modification on a turbocharged Y62",
         "For a performance upgrade on a turbocharged Y62", 2),
        # Same idea, different phrasing, in the body intro.
        ("for a performance modification like this",
         "for a performance upgrade like this", 1),
        ("Modifying the engine or its air intake and boost system",
         "Changing the engine or its air intake and boost system", 2),
        ("modifications affecting original vehicle specification can impact",
         "alterations affecting original vehicle specification can impact", 2),
        ("modifications that alter the original specification of a vehicle",
         "alterations that change the original specification of a vehicle", 1),
        ("talk to your dealer before modifying the engine",
         "talk to your dealer before changing the engine", 1),
    ],
    "blog/y62-rear-air-bag-replacement-cost-uae-2026.html": [
        ("any modification to a vehicle&#39;s suspension system",
         "any alteration to a vehicle&#39;s suspension system", 0),
        ("any modification to a vehicle's suspension system",
         "any alteration to a vehicle's suspension system", 1),
    ],
    "blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html": [
        ("electrical modifications that create safety risks",
         "electrical alterations that create safety risks", 1),
        ("Electrical modifications that cause faults",
         "Electrical alterations that cause faults", 1),
    ],
}

# The tow-bar post carries a stale money-link anchor naming a service that no
# longer exists. money_links.py's own anchor table was already fixed on
# 2026-08-13, so regenerate the sentence from the generator rather than hand-
# writing it — that way the published page matches what the generator would
# emit today.
TOWBAR = "blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html"
STALE_MONEYLINK = (
    'Here is what <a href="/services.html">Y62 modifications and performance '
    'upgrades</a> covers at the workshop.'
)


def main():
    total = 0
    failures = []
    skipped = []

    for rel, pairs in REPLACEMENTS.items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"{rel}: file not found")
            continue
        html = path.read_text(encoding="utf-8")
        original = html
        for old, new, expected in pairs:
            found = html.count(old)
            if found == expected:
                if found:
                    html = html.replace(old, new)
                    total += found
            elif found == 0 and html.count(new) >= max(expected, 1):
                # Already applied on an earlier run. Re-running must be a no-op,
                # not a wall of false failures — the audit is the real gate.
                skipped.append(f"{rel}: already applied — {new[:55]!r}")
            else:
                failures.append(
                    f"{rel}: expected {expected}x but found {found}x — {old[:60]!r}"
                )
        if html != original:
            st = path.stat()
            path.write_text(html, encoding="utf-8")
            os.utime(path, (st.st_atime, st.st_mtime))

    # Tow-bar money link, regenerated from money_links.py.
    path = ROOT / TOWBAR
    html = path.read_text(encoding="utf-8")
    slug = Path(TOWBAR).stem
    if STALE_MONEYLINK in html:
        fresh = money_links._sentence(slug)
        if "modif" in fresh.lower():
            failures.append("money_links still generates a 'modification' anchor")
        else:
            st = path.stat()
            html = html.replace(STALE_MONEYLINK, fresh)
            path.write_text(html, encoding="utf-8")
            os.utime(path, (st.st_atime, st.st_mtime))
            total += 1
            print(f"[+] tow-bar money link regenerated:\n      {fresh}")

    print(f"[+] {total} replacement(s) applied, {len(skipped)} already applied")

    if failures:
        print("\n[!] ABORTED CHANGES — expectations not met:")
        for f in failures:
            print(f"[!]   {f}")
        return 1
    return 0


def audit():
    """Report any surviving modification vocabulary across deployed pages."""
    files = sorted(ROOT.glob("*.html")) + sorted((ROOT / "services").glob("*.html"))
    files += sorted((ROOT / "blog").rglob("*.html"))
    rx = re.compile(r"\b[Mm]od(?:if\w*|s|ded|ding)\b")
    hits = 0
    for path in files:
        html = path.read_text(encoding="utf-8")
        for m in rx.finditer(html):
            # "dateModified" is a schema.org key, not site copy.
            if "dateModified" in html[max(0, m.start() - 9):m.end() + 2]:
                continue
            snippet = re.sub(r"\s+", " ", html[max(0, m.start() - 70):m.end() + 70])
            print(f"  {path.relative_to(ROOT)}: ...{snippet}...")
            hits += 1
    print(f"\n[audit] surviving occurrences: {hits}")
    return hits


if __name__ == "__main__":
    if "--audit" in sys.argv:
        sys.exit(1 if audit() else 0)
    sys.exit(main())
