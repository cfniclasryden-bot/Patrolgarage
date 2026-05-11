from pathlib import Path
import re

root = Path.home() / "Desktop/Projects/patrolgarage"
files = list(root.glob("*.html")) + list((root / "blog").glob("*.html"))

old_strip_pattern = re.compile(
    r'<div class="top-strip-right">\s*'
    r'<span>SUN.THU 09:00.19:00</span>\s*'
    r'<span>SAT 09:00.14:00</span>\s*'
    r'<span>FRI CLOSED</span>\s*'
    r'</div>',
    re.MULTILINE
)

new_strip = '<span class="top-strip-right">NISSAN PATROL SPECIALISTS</span>'

updated = 0
skipped = 0
for f in files:
    html = f.read_text()
    if old_strip_pattern.search(html):
        html = old_strip_pattern.sub(new_strip, html)
        f.write_text(html)
        updated += 1
        print(f"[+] {f.relative_to(root)}")
    else:
        skipped += 1

print(f"\n[✓] Updated: {updated} files")
print(f"[-] Skipped (already updated or different structure): {skipped} files")
