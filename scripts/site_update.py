#!/usr/bin/env python3
"""site_update.py — bulk update phone number and top strip across all HTML files"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OLD_PHONE = "582211201"
NEW_PHONE = "585314281"
OLD_PHONE_FORMATTED = "+971 58 221 1201"
NEW_PHONE_FORMATTED = "+971 58 531 4281"

# All HTML files in project
html_files = list(PROJECT_ROOT.glob("*.html")) + list(PROJECT_ROOT.glob("blog/*.html"))

count_phone = 0
count_strip = 0

for f in html_files:
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    original = content

    # 1. Replace phone numbers (all formats)
    content = content.replace(f"+971{OLD_PHONE}", f"+971{NEW_PHONE}")
    content = content.replace(f"971{OLD_PHONE}", f"971{NEW_PHONE}")
    content = content.replace(OLD_PHONE_FORMATTED, NEW_PHONE_FORMATTED)
    content = content.replace(OLD_PHONE, NEW_PHONE)

    # 2. Improve top strip: remove green dot + OPEN NOW, restructure hours
    # Match the entire top-strip section
    new_strip = '''<div class="top-strip">
    <div class="top-strip-inner">
      <span>RAS AL KHOR · DUBAI</span>
      <div class="top-strip-right">
        <span>SUN–THU 09:00–19:00</span>
        <span>SAT 09:00–14:00</span>
        <span>FRI CLOSED</span>
      </div>
    </div>
  </div>'''

    # Replace the full top-strip div
    content = re.sub(
        r'<div class="top-strip">.*?</div>\s*</div>',
        new_strip,
        content,
        count=1,
        flags=re.DOTALL
    )

    if content != original:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  ✓ Updated: {f.relative_to(PROJECT_ROOT)}")
        if OLD_PHONE in original:
            count_phone += 1
        if "OPEN NOW" in original or "dot" in original:
            count_strip += 1

print(f"\n[+] Updated phone number in {count_phone} files")
print(f"[+] Updated top strip in {count_strip} files")
print(f"[+] Total files processed: {len(html_files)}")
