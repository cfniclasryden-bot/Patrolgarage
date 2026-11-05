#!/usr/bin/env python3
"""Regression for the 2026-11-05 phone layer (scripts/mobile_ux.py). Spends nothing.

  * every shipped page carries the mobile CSS (.btn wraps <= 768 px) exactly once;
  * every shipped page carries exactly one sticky Call + WhatsApp bar, with
    tel:+971558175637 and a wa.me/971558175637 link;
  * the click tracker reports the bar as 'sticky_bar' and sends cta_position;
  * no shipped page links internally to an extensionless path whose .html exists;
  * mobile_ux.apply() is idempotent on every shipped page;
  * assemble.py, publish.py and the page builders call mobile_ux.

    python3 scripts/test_mobile_ux.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mobile_ux                      # noqa: E402
from shipped_pages import shipped_pages, SITE  # noqa: E402

fails = []
pages = shipped_pages()
for p in pages:
    rel = p.relative_to(SITE).as_posix()
    html = p.read_text(encoding="utf-8")
    for what in mobile_ux.missing(html):
        fails.append(f"{rel}: missing {what}")
    if html.count(f'id="{mobile_ux.CSS_ID}"') > 1:
        fails.append(f"{rel}: mobile css injected more than once")
    bars = re.findall(r'<div class="pg-sticky".*?</div>', html, re.S)
    if len(bars) != 1:
        fails.append(f"{rel}: {len(bars)} sticky bars")
    else:
        if 'href="tel:+971558175637"' not in bars[0]:
            fails.append(f"{rel}: sticky Call is not tel:+971558175637")
        if not re.search(r'href="https://wa\.me/971558175637[?"]', bars[0]):
            fails.append(f"{rel}: sticky WhatsApp is not wa.me/971558175637")
    if mobile_ux.apply(html) != html:
        fails.append(f"{rel}: mobile_ux.apply() would still change it")

for script in ["assemble.py", "publish.py", "build_service_pages.py",
               "build_y62_garage_page.py", "build_abu_dhabi_page.py"]:
    if "mobile_ux" not in (SITE / "scripts" / script).read_text(encoding="utf-8"):
        fails.append(f"scripts/{script}: does not call mobile_ux")

if fails:
    print(f"[FAIL] {len(fails)} problem(s):")
    for f in fails[:60]:
        print("  " + f)
    sys.exit(1)
print(f"[OK] phone layer on all {len(pages)} shipped pages: .btn wrap css, one sticky "
      f"Call/WhatsApp bar, cta_position = sticky_bar, no extensionless internal links")
