#!/usr/bin/env python3
"""Regression for the Patrol Garage first-screen ask (2026-10-09). Spends nothing.

  * every target page carries the PG block with its three labels, the site's
    WhatsApp and phone numbers, and its stylesheet;
  * no shipped page carries topchallenger.ae's block, class names or wording;
  * the Arabic link keeps its Arabic pre-fill through cta_lib.set_all_wa_prefill
    (assemble.py and patch_cta.py run it over every WhatsApp link);
  * the patch script is idempotent.

    python3 scripts/test_first_screen_cta.py
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import cta_lib                   # noqa: E402
import patch_first_screen_cta as p   # noqa: E402

fails = []
TC_TRACES = ['class="fs-cta"', 'class="fs-ar"', 'fs-cta-css', 'data-cta-label="hero-wa"',
             'data-cta-label="hero-wa-ar"', "Send us the symptom or a short video on WhatsApp",
             "howitworks-wa", "hiw-steps", "ad-directions", "Start on WhatsApp"]

for f in ["index.html", "services.html"] + p.POSTS:
    html = (ROOT / f).read_text(encoding="utf-8")
    for need in ('data-cta-label="pg-hero-wa"', 'data-cta-label="pg-hero-wa-ar"',
                 'data-cta-label="pg-hero-call"', 'id="pg-ask-css"',
                 f'href="https://wa.me/{p.WA}?text={quote(p.EN)}"',
                 f'href="https://wa.me/{p.WA}?text={quote(p.AR)}"', f'href="tel:{p.TEL}"'):
        if need not in html:
            fails.append(f"{f}: missing {need[:60]}")
    if html.count('class="pg-ask"') != 1:
        fails.append(f"{f}: expected exactly one first-screen block")

shipped = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split()
for f in shipped:
    html = (ROOT / f).read_text(encoding="utf-8")
    for t in TC_TRACES:
        if t in html:
            fails.append(f"{f}: still carries topchallenger's {t!r}")

block = p.block()
after = cta_lib.set_all_wa_prefill(block, "English article prefill")
if quote(p.AR) not in after or quote(p.EN) in after:
    fails.append("set_all_wa_prefill: Arabic link lost its pre-fill, or English link kept the old one")

dry = subprocess.run(["python3", "scripts/patch_first_screen_cta.py"], cwd=ROOT,
                     capture_output=True, text=True).stdout
if "would write 0 file(s)" not in dry:
    fails.append("patch_first_screen_cta.py is not idempotent: " + dry.strip()[-120:])

if fails:
    print(f"[!] first-screen CTA regression FAILED - {len(fails)} problem(s):")
    for f in fails:
        print("    -", f)
    sys.exit(1)
print(f"[+] first-screen CTA regression passed: {2 + len(p.POSTS)} pages carry the PG block, "
      f"no topchallenger traces on {len(shipped)} pages, Arabic pre-fill survives, idempotent.")
