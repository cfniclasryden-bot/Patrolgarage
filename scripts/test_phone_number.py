#!/usr/bin/env python3
"""Regression for the 2026-11-02 number change to +971 55 817 5637. Spends nothing.

  * no shipped page (root/blog/services HTML, llms.txt) and no generator script
    carries an old number in any format;
  * every tel: link is tel:+971558175637;
  * every wa.me / api.whatsapp.com link targets 971558175637;
  * every JSON-LD "telephone" is +971558175637.

    python3 scripts/test_phone_number.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import copy_pins     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NEW = "971558175637"
OLD = re.compile(r"585143634|58 514 3634|582211201|58 221 1201")
# site_update.py is the old-to-new migration script and names the old number on purpose;
# this test and copy_pins.py name them as the patterns to look for.
SKIP_SCRIPTS = {"site_update.py", "test_phone_number.py", "copy_pins.py"}
# test fixture placeholders (e.g. 971500000000 in test_check_claims.py) are not the site number
FIXTURE = re.compile(r"971500000000")

fails = []
pages = copy_pins.phone_pages()
for path in pages:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    for m in OLD.finditer(text):
        fails.append(f"{rel}: old number {m.group(0)!r}")
    for m in re.finditer(r"tel:([+0-9]+)", text):
        if m.group(1) != "+" + NEW:
            fails.append(f"{rel}: tel link {m.group(0)!r}")
    for m in re.finditer(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\d+)", text):
        if m.group(1) != NEW:
            fails.append(f"{rel}: WhatsApp link to {m.group(1)}")
    for m in re.finditer(r'"telephone":\s*"([^"]+)"', text):
        if m.group(1) != "+" + NEW:
            fails.append(f"{rel}: JSON-LD telephone {m.group(1)!r}")

for path in sorted((ROOT / "scripts").glob("*.py")):
    if path.name in SKIP_SCRIPTS:
        continue
    text = path.read_text(encoding="utf-8")
    for m in OLD.finditer(text):
        fails.append(f"scripts/{path.name}: old number {m.group(0)!r}")
    for m in re.finditer(r"(?:wa\.me/|tel:\+?)(\d{9,})", text):
        if m.group(1) != NEW and not FIXTURE.fullmatch(m.group(1)):
            fails.append(f"scripts/{path.name}: link to {m.group(1)}")

if fails:
    print(f"[!] phone number regression FAILED - {len(fails)} problem(s):")
    for f in fails[:50]:
        print("    -", f)
    sys.exit(1)
print(f"[+] phone number regression passed: {len(pages)} shipped file(s) and all generators use +{NEW}.")
