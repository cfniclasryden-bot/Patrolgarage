#!/usr/bin/env python3
"""patch_removed_service_ctas.py — stop published pages OFFERING removed services.

Owner decision 2026-08-17, after the audit. Three services are not sold:
pre-purchase inspection, lift kits / height modification, and modifications
(the last one already handled by patch_modifications_vocab.py).

SCOPE IS DELIBERATELY NARROW — the owner ruled on this explicitly:
  * TITLES ARE NOT TOUCHED. "Suspension Repair & Lift Kits in Dubai" and the
    other four lift-kit posts stay as they are. They are informational, they
    earn impressions, and the word in a title is not an offer.
  * PRICES ARE NOT TOUCHED. Educational cost content is what converts on this
    site, including the lift-kit price ranges in the suspension pillar.
  * Only the OFFER survives here: first-person copy and CTAs that present a
    removed service as ours to sell.

The pre-fills were already clean (cta_lib.PREFILL_TOPIC_OVERRIDES). What was
left is baked cta-banner copy, which is static in the published HTML and is not
regenerated from the title, so no generator fix reaches it.

Every replacement asserts an exact occurrence count and the script writes
nothing if any assertion fails — these are ranking pages. Re-running is a no-op.
mtimes preserved.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS = {
    # ---- CTA banners: the two that offer lift/upgrade work -----------------
    "blog/nissan-patrol-suspension-dubai.html": [
        ("Shock replacement, bushing kits, lift installation.",
         "Shock replacement, bushing kits, HBMC accumulators.", 1),
    ],
    "blog/nissan-patrol-off-road-uae.html": [
        ("Suspension upgrades, tire service, pre-dune inspection.",
         "Suspension repair, tire service, pre-dune checks.", 1),
        # og:description carried the same offer wording.
        ("Off-road Patrol guide: dune driving tips, suspension upgrades, safety",
         "Off-road Patrol guide: dune driving tips, suspension repair, safety", 1),
    ],

    # ---- Y62 pillar: PPI presented as ours ---------------------------------
    "blog/nissan-patrol-y62-dubai-complete-guide.html": [
        # "what we check" is the offer; the guide it links to is buyer information.
        ("Patrol pre-purchase inspection in Dubai: what we check and what it costs",
         "Patrol pre-purchase inspection in Dubai: what a good one covers and what it costs", 1),
        # "on the lift" = our lift. Same facts, observer voice.
        ("We&#39;ve seen buyers avoid AED 20,000 to 40,000 in repairs by finding problems an "
         "inspection flagged before they signed. We&#39;ve also seen buyers walk away from "
         "vehicles that looked perfect on paper but revealed serious issues on the lift.", "", 0),
        ("We've seen buyers avoid AED 20,000 to 40,000 in repairs by finding problems an "
         "inspection flagged before they signed. We've also seen buyers walk away from "
         "vehicles that looked perfect on paper but revealed serious issues on the lift.",
         "Buyers regularly avoid AED 20,000 to 40,000 in repairs by finding problems an "
         "inspection flagged before they signed. Others walk away from vehicles that looked "
         "perfect on paper but revealed serious issues once up on a ramp.", 1),
    ],

    # ---- Today's post: written by the cron 2026-08-17, sells PPI outright ---
    "blog/buying-a-used-nissan-patrol.html": [
        ("At the workshop we run through the following on every used Patrol inspection:",
         "A thorough inspection covers the following on a used Patrol:", 1),
        ("HBMC suspension check on Y62 models. We look for fluid leaks at each corner "
         "and check the ride height.",
         "HBMC suspension check on Y62 models. Look for fluid leaks at each corner "
         "and check the ride height.", 1),
        ("We check freeze-frame data and monitor live readings to see if a code has "
         "been cleared recently.",
         "Freeze-frame data and live readings show whether a code has been cleared "
         "recently.", 1),
        # The closing CTA sold the inspection. Keep the repair offer, send the
        # inspection itself elsewhere. MONEYLINK sentence is left untouched.
        ("If you are looking at a used Patrol anywhere in the UAE and want an independent "
         "opinion before you commit, bring it to us in Ras Al Khor. We work exclusively on "
         "Patrols, we have seen every common fault across Y61, Y62, and early Y63 models, "
         "and we will give you a straight read on what the car needs and what it will cost. "
         "If you have already bought a Patrol and want to get it properly sorted, the same "
         "applies. Book a full inspection and we will go through it systematically and tell "
         "you exactly where it stands.",
         "Get the pre-purchase inspection itself done independently, before you commit. "
         "Once the Patrol is yours and you want it properly sorted, bring it to us in Ras Al "
         "Khor. We work exclusively on Patrols, we have seen every common fault across Y61, "
         "Y62, and early Y63 models, and we will give you a straight read on what the car "
         "needs and what it will cost.", 1),
    ],
}


def main():
    total, skipped, failures = 0, [], []
    staged = {}

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
            elif found == 0 and new and html.count(new) >= max(expected, 1):
                skipped.append(f"{rel}: already applied")
            else:
                failures.append(
                    f"{rel}: expected {expected}x, found {found}x — {old[:64]!r}"
                )
        if html != original:
            staged[path] = html

    # Nothing is written unless every assertion passed: these are ranking pages.
    if failures:
        print("[!] NOTHING WRITTEN — expectations not met:")
        for f in failures:
            print(f"[!]   {f}")
        return 1

    for path, html in staged.items():
        st = path.stat()
        path.write_text(html, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))

    print(f"[+] {total} replacement(s) applied across {len(staged)} file(s), "
          f"{len(skipped)} already applied")
    return 0


def audit():
    """Report CTA surfaces still offering a removed service."""
    import urllib.parse
    rx = re.compile(
        r"lift[- ]?kit|lift installation|suspension upgrade|pre[- ]purchase inspection"
        r"|height modification", re.I)
    hits = 0
    for path in sorted((ROOT / "blog").glob("*.html")):
        if path.name == "index.html":
            continue
        html = path.read_text(encoding="utf-8")
        surfaces = []
        for m in re.findall(r'<section class="cta-banner">(.*?)</section>', html, re.S):
            surfaces.append(("cta-banner", m))
        for m in re.findall(r'<div class="early-cta"[^>]*>(.*?)</div>', html, re.S):
            surfaces.append(("early-cta", m))
        for m in set(re.findall(r"wa\.me/\d+\?text=([^\"&]+)", html)):
            surfaces.append(("prefill", urllib.parse.unquote(m)))
        for kind, raw in surfaces:
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).strip()
            if rx.search(txt):
                print(f"  {path.name} [{kind}] {txt[:150]}")
                hits += 1
    print(f"\n[audit] CTA surfaces offering a removed service: {hits}")
    return hits


if __name__ == "__main__":
    if "--audit" in sys.argv:
        sys.exit(1 if audit() else 0)
    sys.exit(main())
