#!/usr/bin/env python3
"""Regression for the 2026-11-02 number change to +971 55 817 5637. Spends nothing.

  * no shipped page (root/blog/services HTML, llms.txt) and no generator script
    carries an old number in any format;
  * every tel: link is tel:+971558175637;
  * every wa.me / api.whatsapp.com link targets 971558175637;
  * no JSON-LD carries a "telephone" at all (owner, 2026-11-03): the number is on
    the buttons only, and no generator script may write one into structured data;
  * every shipped HTML page has a call link to +971558175637.

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
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
# A generator that would put a telephone into JSON-LD: a "telephone" key with a
# value, in a dict literal, a JSON string or a subscript assignment.
GEN_TEL_RE = re.compile(r"""["']telephone["']\s*[:\]]""")

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
    # No JSON-LD carries a telephone (owner, 2026-11-03); the buttons keep the number.
    for block in LD_RE.findall(text):
        if re.search(r'"telephone"\s*:', block):
            fails.append(f"{rel}: JSON-LD carries a telephone")
    if rel.suffix == ".html" and "tel:+" + NEW not in text:
        fails.append(f"{rel}: no call link to +{NEW}")

for path in sorted((ROOT / "scripts").glob("*.py")):
    if path.name in SKIP_SCRIPTS:
        continue
    text = path.read_text(encoding="utf-8")
    for m in OLD.finditer(text):
        fails.append(f"scripts/{path.name}: old number {m.group(0)!r}")
    if GEN_TEL_RE.search(text):
        fails.append(f"scripts/{path.name}: writes a telephone into JSON-LD")
    for m in re.finditer(r"(?:wa\.me/|tel:\+?)(\d{9,})", text):
        if m.group(1) != NEW and not FIXTURE.fullmatch(m.group(1)):
            fails.append(f"scripts/{path.name}: link to {m.group(1)}")

if fails:
    print(f"[!] phone number regression FAILED - {len(fails)} problem(s):")
    for f in fails[:50]:
        print("    -", f)
    sys.exit(1)
print(f"[+] phone number regression passed: {len(pages)} shipped file(s) and all generators use +{NEW}.")
