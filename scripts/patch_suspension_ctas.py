#!/usr/bin/env python3
"""Hardcode the suspension pillar's WhatsApp CTAs off "lift kits", and finish
the lift-kit split in the generators.

Owner decision 2026-08-13 (option 1 of three): the workshop does suspension
REPAIR, not lift kits. The post KEEPS its title, meta and informational
"Lift Kit Installation" section — GSC over the 90 days to 2026-08-10 shows the
page at 0 clicks / 18 impressions / pos 7.3 and NOT ONE lift, suspension or
hbmc query with any impressions, so there is nothing to protect either way, and
owner-information content stays per the turbo-post precedent.

What was actually wrong is narrower: the four WhatsApp pre-fills read
"I read your Patrol suspension repair & lift kits guide — can I get an exact
quote for my Patrol?". That is an OFFER of a lift-kit quote. It is generated,
not hand-written — cta_lib.topic_phrase() derives it from the <title> — so
patching the HTML alone would regenerate on the next assemble. cta_lib now
carries a PREFILL_TOPIC_OVERRIDES entry; this script fixes the four already
published copies to match.

  blog/nissan-patrol-suspension-dubai.html   4 WhatsApp pre-fills
  money_links.py                             anchor text; lift-kit slug routing
  patch_tap_targets.py                       stale label -> section id map

NOT CHANGED, still open with the owner:
  journal_update.py:93 files any slug containing "suspension" or "upgrade"
  under the category label UPGRADES, so this repair pillar shows as UPGRADES
  on the live blog listing. Changing it moves every suspension-slugged post.

mtime preserved on the blog file — journal_update.py derives the displayed date
AND the listing sort order from it, and publish.py runs on every deploy.
patch_cta.py is NOT used here precisely because it does not preserve mtimes.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cta_lib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

POST = ROOT / "blog" / "nissan-patrol-suspension-dubai.html"
SLUG = "nissan-patrol-suspension-dubai"
TITLE = "Nissan Patrol Suspension Repair & Lift Kits in Dubai (2026)"

OLD_PREFILL = "Hi, I read your Patrol suspension repair & lift kits guide — can I get an exact quote for my Patrol?"
NEW_PREFILL = cta_lib.prefill_for(TITLE, SLUG)

SWAPS = [
    ("scripts/money_links.py", "suspension anchor",
     '    "suspension": "Y62 suspension and lift kit work",',
     '    "suspension": "Y62 suspension and HBMC repair",'),
    ("scripts/money_links.py", "lift-kit routing",
     '    (r"suspension|air-bag|lift-kit|shock|hbmc", "suspension"),',
     '    (r"suspension|air-bag|shock|hbmc", "suspension"),'),
    ("scripts/patch_tap_targets.py", "label -> id map",
     '    "Suspension & Lift Kits": "suspension-upgrade-lift-kits",',
     '    "Suspension & HBMC": "suspension-hbmc-repair",'),
]


def main():
    dry = "--dry-run" in sys.argv
    planned = []

    if NEW_PREFILL == OLD_PREFILL:
        print("  !! cta_lib override is not in effect — prefill still names lift kits")
        return 1
    if "lift kit" in NEW_PREFILL.lower():
        print(f"  !! new prefill still mentions lift kits: {NEW_PREFILL!r}")
        return 1
    print(f"  prefill: {NEW_PREFILL!r}")

    # --- the four published CTAs -----------------------------------------
    h = POST.read_text(encoding="utf-8")
    old_enc = cta_lib.enc(OLD_PREFILL)
    new_enc = cta_lib.enc(NEW_PREFILL)
    n = h.count(old_enc)
    if n == 0:
        print(f"  clean  {POST.name} (no lift-kit pre-fill found)")
    else:
        h2 = h.replace(old_enc, new_enc)
        if old_enc in h2:
            print("  !! replacement left an old pre-fill behind — aborting"); return 1
        planned.append((POST, h2))
        print(f"  swap   {POST.name}: {n} WhatsApp pre-fill(s)")

    # --- generators --------------------------------------------------------
    for rel, what, old, new in SWAPS:
        p = ROOT / rel
        if not p.exists():
            print(f"  !! missing {rel}"); return 1
        t = next((x for pp, x in reversed(planned) if pp == p), p.read_text(encoding="utf-8"))
        c = t.count(old)
        if c == 0:
            print(f"  clean  {rel:<28} {what}")
            continue
        if c > 1:
            print(f"  !! {rel} [{what}]: matched {c}x — aborting"); return 1
        planned.append((p, t.replace(old, new, 1)))
        print(f"  swap   {rel:<28} {what}")

    final = {}
    for p, t in planned:
        final[p] = t

    # Outcome checks, independent of the patterns above.
    lost = []
    post_text = final.get(POST, POST.read_text(encoding="utf-8"))
    if old_enc in post_text:
        lost.append("post still has a lift-kit WhatsApp pre-fill")
    if new_enc not in post_text:
        lost.append("post has no new pre-fill — CTAs would point nowhere useful")
    ml = final.get(ROOT / "scripts/money_links.py",
                   (ROOT / "scripts/money_links.py").read_text(encoding="utf-8"))
    if "lift kit" in ml or "lift-kit" in ml:
        lost.append("money_links.py still references lift kits")
    tt = final.get(ROOT / "scripts/patch_tap_targets.py",
                   (ROOT / "scripts/patch_tap_targets.py").read_text(encoding="utf-8"))
    if "suspension-upgrade-lift-kits" in tt:
        lost.append("patch_tap_targets.py still maps to the dead section id")
    if lost:
        print("\n  !! verification failed, aborting:")
        for x in lost:
            print(f"       - {x}")
        return 1
    print(f"\n  verified — {len(final)} file(s)")

    if dry:
        print("DRY RUN — nothing written")
        return 0

    for p, t in final.items():
        under_blog = "blog" in p.parts
        st = p.stat() if under_blog else None
        p.write_text(t, encoding="utf-8")
        if st:
            os.utime(p, (st.st_atime, st.st_mtime))
    print(f"WRITTEN — {len(final)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
