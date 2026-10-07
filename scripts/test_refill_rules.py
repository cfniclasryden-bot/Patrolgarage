#!/usr/bin/env python3
"""Regression for keyword_generator.refill_rule() (Gate 0b, 2026-10-07).

Reads the rule block straight out of keyword_generator.py rather than importing
the module, which needs API keys at import. Spends nothing.

    python3 scripts/test_refill_rules.py
"""
import re
import sys
from pathlib import Path

SRC = (Path(__file__).resolve().parent / "keyword_generator.py").read_text(encoding="utf-8")
ns = {}
exec("import re\n" + SRC[SRC.index("TC_TERRITORY = "):SRC.index("def slugify")], ns)
rule = ns["refill_rule"]

MUST_REJECT = [
    "nissan patrol specialist vs dealer",      # retired 2026-10-07 for this reason
    "nissan patrol garage near me",
    "nissan patrol service abu dhabi",
    "y62 repair mussafah",
    "nissan patrol limp mode",                 # queued on topchallenger.ae
    "nissan patrol battery problems",
    "nissan patrol liwa trip",
]
MUST_ACCEPT = [
    "nissan patrol rough idle",
    "nissan patrol jerking when accelerating",
    "nissan patrol temperature gauge rising",
    "nissan patrol hard start",
    "nissan patrol reliability abu dhabi",     # ownership question, allowed
    "owning a nissan patrol in abu dhabi",
    "nissan patrol losing power",              # the three still pending
    "nissan patrol long term ownership",
    "nissan patrol brake problems",
]

fails = [f"should reject: {k}" for k in MUST_REJECT if not rule(k)]
fails += [f"should accept: {k} ({rule(k)})" for k in MUST_ACCEPT if rule(k)]
for f in fails:
    print(f"  FAIL  {f}")
if fails:
    sys.exit(1)
print(f"[+] refill rules regression passed: {len(MUST_REJECT)} must-reject, {len(MUST_ACCEPT)} must-accept.")
