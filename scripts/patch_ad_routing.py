#!/usr/bin/env python3
"""patch_ad_routing.py — Mussafah WhatsApp routing on every Abu Dhabi page.

Added 2026-10-09. Applies ad_city.apply_routing() to the hub and to every
shipped post whose slug names Abu Dhabi: the Abu Dhabi first-screen ask under
the H1 (event labels pg-ad-wa / pg-ad-wa-ar / pg-ad-call) and every WhatsApp
pre-fill starting "Mussafah:". assemble.py does the same for new posts, and
publish.publish() runs this before every deploy, so a refresh or a rebuild
cannot drop it. File mtimes are preserved (mtime is the displayed post date).

    python3 scripts/patch_ad_routing.py           # dry run
    python3 scripts/patch_ad_routing.py --write
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ad_city  # noqa: E402


def ad_pages():
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                           text=True).stdout.split()
    found = {f for f in files if ad_city.is_ad_page(f)}
    # A post published this run is not tracked yet.
    found |= {f"blog/{p.name}" for p in (ROOT / "blog").glob("*.html")
              if ad_city.is_ad_page(f"blog/{p.name}")}
    if (ROOT / ad_city.HUB).exists():
        found.add(ad_city.HUB)
    return sorted(found)


def run(write):
    changed = []
    for rel in ad_pages():
        p = ROOT / rel
        html = p.read_text(encoding="utf-8")
        new = ad_city.apply_routing(html)
        if new != html:
            changed.append(rel)
            if write:
                st = p.stat()
                p.write_text(new, encoding="utf-8")
                os.utime(p, (st.st_atime, st.st_mtime))
    return changed


def main():
    write = "--write" in sys.argv[1:]
    changed = run(write)
    for rel in changed:
        print(f"[+] {rel}: Mussafah routing")
    print(f"[=] {'wrote' if write else 'would write'} {len(changed)} file(s) "
          f"of {len(ad_pages())} Abu Dhabi page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
