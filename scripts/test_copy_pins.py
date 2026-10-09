#!/usr/bin/env python3
"""Regression for scripts/copy_pins.py (2026-10-09). Spends nothing.

  * every pin is applied on disk: no pinned passage is back on a shipped page,
    and no pin has drifted (neither old nor new text present);
  * every replacement passes the guards it was written for: no CROWD or
    FIRST_HAND claim, no copy_rules finding, no double quote (it lands in
    JSON-LD), no em dash, and nothing that suggests premises, a team
    inspecting cars or a customer base, because this site has none;
  * a second apply changes nothing.

    python3 scripts/test_copy_pins.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copy_pins     # noqa: E402
import copy_rules    # noqa: E402

PREMISES = re.compile(
    r"\b(?:workshop|bay|garage|facility|premises|in stock|bring it in|brought in|come in|"
    r"drop[- ]off|our team|technicians?|mechanics?|customers?|clients?)\b", re.I)
fails = []

pending, already, drift = copy_pins.apply_all(write=False)
if pending:
    fails.append(f"{pending} pin(s) not applied on disk (an old passage is back)")
fails += [f"drift: {d}" for d in drift]

for page, pins in copy_pins.PINS.items():
    for old, new in pins:
        text = re.sub(r"<[^>]+>", "", new)
        if '"' in new:
            fails.append(f"{page}: double quote in replacement: {new[:60]!r}")
        if "—" in new or "–" in new:
            fails.append(f"{page}: dash in replacement: {new[:60]!r}")
        if copy_rules.unverified_claims(text):
            fails.append(f"{page}: replacement still a CROWD/FIRST_HAND claim: {new[:60]!r}")
        if copy_rules.sentence_findings(text):
            fails.append(f"{page}: replacement trips copy_rules: {copy_rules.sentence_findings(text)}")
        m = PREMISES.search(new)
        if m:
            fails.append(f"{page}: replacement implies premises/customers ({m.group(0)!r}): {new[:60]!r}")

again = copy_pins.apply_all(write=False)
if again[0]:
    fails.append("a second apply would change pages again (not idempotent)")

total = sum(len(p) for p in copy_pins.PINS.values())
if fails:
    print(f"[!] copy pins regression FAILED - {len(fails)} problem(s):")
    for f in fails:
        print("    -", f)
    sys.exit(1)
print(f"[+] copy pins regression passed: {total} pin(s) on {len(copy_pins.PINS)} page(s) applied, "
      f"replacements clean, idempotent.")
