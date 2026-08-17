#!/usr/bin/env python3
"""Split suspension REPAIR (kept) from lift kits / height modification (removed).

Owner decision 2026-08-13. Worn shocks, HBMC accumulators and bushes are
mechanical work the workshop does. Raising the car is not.

WHAT CHANGES
  index.html    S/02 card: "Suspension & Lift Kits" -> "Suspension & HBMC",
                repair-framed copy, link retargeted to the renamed section.
  index.html    LocalBusiness schema serviceType "Suspension Lift Kits"
                -> "Suspension Repair".
  services.html the section keeps its repair content and loses the lift-kit
                content; id suspension-upgrade-lift-kits -> suspension-hbmc-
                repair; both WhatsApp CTAs reworded off "Suspension Upgrade".
  contact.html  form option "Suspension / Lift Kit" -> "Suspension / HBMC".
  about.html    "suspension upgrades" -> "suspension and HBMC repair".

  ALSO (52 pages): the shared header carries one orphan </div> immediately
  after the top-strip block, so 52 of 63 pages are structurally invalid at
  +1 close. index.html and services.html are already clean. Two formatting
  variants exist; both are handled.

NOT TOUCHED HERE — reported to the owner first:
  money_links.py anchor + slug rule, patch_tap_targets.py label->id map,
  journal_update.py UPGRADES category, and the suspension pillar post's
  title/meta/CTAs.

BOUNDARY VERIFICATION, as in patch_remove_modifications.py: every block
replacement asserts on the captured text before writing, and the collapse
step re-checks that no queued edit was dropped. mtimes preserved under blog/.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD_ID = "suspension-upgrade-lift-kits"
NEW_ID = "suspension-hbmc-repair"

# --- index.html S/02 card ---------------------------------------------------
CARD_OLD = '''          <h3><a href="/services.html#suspension-upgrade-lift-kits">Suspension<br>&amp; Lift Kits</a></h3>
          <p>Full rebuilds, OME and Ironman kits, custom off-road setups for desert and dune work.</p>'''
CARD_NEW = '''          <h3><a href="/services.html#suspension-hbmc-repair">Suspension<br>&amp; HBMC</a></h3>
          <p>Worn shocks and springs, HBMC accumulator and hydraulic faults, cracked bushes and knocking front ends.</p>'''

# --- services.html section --------------------------------------------------
SEC_OLD = '''      <div class="service-article" id="suspension-upgrade-lift-kits">
        <h2><a href="https://wa.me/971585143634?text=Suspension%20Upgrade%20for%20my%20Patrol" target="_blank" rel="noopener">Suspension Upgrade & Lift Kits</a></h2>
        <p>Want better ground clearance and off-road capability? We install suspension lifts, replace shocks and springs, align your wheels, and set up custom off-road configurations. OEM, Ironman, and custom options available.</p>'''
SEC_NEW = '''      <div class="service-article" id="suspension-hbmc-repair">
        <h2><a href="https://wa.me/971585143634?text=Suspension%20Repair%20for%20my%20Patrol" target="_blank" rel="noopener">Suspension &amp; HBMC Repair</a></h2>
        <p>Bouncy ride, body roll, clunks over speed bumps or a corner sitting low? We diagnose the fault and replace what has actually worn — shocks and springs, HBMC accumulators and hydraulic lines, bushes and top mounts — then road-test the car before it goes back to you.</p>'''

CTA_OLD = '<a href="https://wa.me/971585143634?text=Suspension%20Upgrade%20for%20my%20Patrol" target="_blank" rel="noopener" class="btn btn-primary">Quote via WhatsApp</a>'
CTA_NEW = '<a href="https://wa.me/971585143634?text=Suspension%20Repair%20for%20my%20Patrol" target="_blank" rel="noopener" class="btn btn-primary">Quote via WhatsApp</a>'

SWAPS = [
    ("index.html", "S/02 card", CARD_OLD, CARD_NEW),
    ("index.html", "schema serviceType", '    "Suspension Lift Kits",\n', '    "Suspension Repair",\n'),
    ("services.html", "section head", SEC_OLD, SEC_NEW),
    ("services.html", "section CTA button", CTA_OLD, CTA_NEW),
    ("contact.html", "form option",
     '<option value="Suspension">Suspension / Lift Kit</option>',
     '<option value="Suspension">Suspension / HBMC</option>'),
    ("about.html", "history line",
     "complex engine work, suspension upgrades to full restorations",
     "complex engine work, suspension and HBMC repair to full restorations"),
]

# The orphan </div> after the top-strip block. Variant A has the three closes on
# their own lines; variant B joins the last two. Anchored on top-strip-right so
# the match cannot wander — no lazy dot crossing nested divs.
ORPHAN_A = ('''<span class="top-strip-right">NISSAN PATROL SPECIALISTS</span>
    </div>
  </div>
  </div>''',
            '''<span class="top-strip-right">NISSAN PATROL SPECIALISTS</span>
    </div>
  </div>''')
ORPHAN_B = ('''<span class="top-strip-right">NISSAN PATROL SPECIALISTS</span>
    </div>
  </div></div>''',
            '''<span class="top-strip-right">NISSAN PATROL SPECIALISTS</span>
    </div>
  </div>''')


def div_balance(h):
    return len(re.findall(r"<div\b", h)) - len(re.findall(r"</div>", h))


def main():
    dry = "--dry-run" in sys.argv
    planned = []

    def queue(p, what, text):
        planned.append((p, what, text))

    def newest(p):
        return next((t for pp, _, t in reversed(planned) if pp == p),
                    p.read_text(encoding="utf-8"))

    # --- targeted swaps ---------------------------------------------------
    for rel, what, old, new in SWAPS:
        p = ROOT / rel
        if not p.exists():
            print(f"  !! missing {rel}"); return 1
        h = newest(p)
        n = h.count(old)
        if n == 0:
            print(f"  clean  {rel:<16} {what}")
            continue
        if n > 1:
            print(f"  !! {rel} [{what}]: matched {n}x, expected 1 — aborting"); return 1
        queue(p, what, h.replace(old, new, 1))
        print(f"  swap   {rel:<16} {what}")

    # --- stray </div>, every affected page ---------------------------------
    fixed = 0
    for p in sorted(ROOT.rglob("*.html")):
        if "node_modules" in p.parts:
            continue
        h = newest(p)
        before = div_balance(h)
        if before == 0:
            continue
        if before != -1:
            print(f"  !! {p.relative_to(ROOT)}: balance {before:+d}, not the known "
                  f"single-orphan case — skipping, needs a look"); continue
        for old, new in (ORPHAN_A, ORPHAN_B):
            if h.count(old) == 1:
                h2 = h.replace(old, new, 1)
                break
        else:
            print(f"  !! {p.relative_to(ROOT)}: +1 close but neither known orphan "
                  f"variant matched — skipping"); continue
        if div_balance(h2) != 0:
            print(f"  !! {p.relative_to(ROOT)}: still unbalanced after fix — aborting"); return 1
        queue(p, "orphan </div>", h2)
        fixed += 1
    print(f"  div    {fixed} page(s) rebalanced")

    # --- collapse + verify -------------------------------------------------
    final = {}
    for p, _, text in planned:
        final[p] = text

    lost = []
    for rel, what, old, _new in SWAPS:
        p = ROOT / rel
        if p in final and old in final[p]:
            lost.append(f"{rel} [{what}]")
    for p, text in final.items():
        if div_balance(text) != 0:
            lost.append(f"{p.relative_to(ROOT)} [div balance]")

    # A swap reported "clean" means EITHER already-applied OR the expected
    # string was wrong (an &amp; vs & slip hid the section head the first time).
    # These outcome checks are independent of the patterns above, so a wrong
    # pattern can no longer pass silently.
    idx = final.get(ROOT / "index.html", (ROOT / "index.html").read_text(encoding="utf-8"))
    svc = final.get(ROOT / "services.html", (ROOT / "services.html").read_text(encoding="utf-8"))
    for label, text, must_go in (
        ("index.html link", idx, OLD_ID),
        ("services.html id", svc, OLD_ID),
        ("index.html schema", idx, "Suspension Lift Kits"),
        ("services.html heading", svc, "Lift Kits"),
        ("services.html lift copy", svc, "We install suspension lifts"),
        ("services.html CTA", svc, "Suspension%20Upgrade"),
    ):
        if must_go in text:
            lost.append(f"{label}: still contains {must_go!r}")
    if NEW_ID not in idx or NEW_ID not in svc:
        lost.append(f"{NEW_ID!r} missing from index.html or services.html — link would 404")

    if lost:
        print("\n  !! collapse dropped edits, aborting:")
        for x in lost:
            print(f"       - {x}")
        return 1
    print(f"\n  collapse verified — {len(final)} file(s), no edit lost, all balanced")

    if dry:
        print("DRY RUN — nothing written")
        return 0

    for p, text in final.items():
        under_blog = "blog" in p.parts
        st = p.stat() if under_blog else None
        p.write_text(text, encoding="utf-8")
        if st:
            os.utime(p, (st.st_atime, st.st_mtime))
    print(f"WRITTEN — {len(final)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
