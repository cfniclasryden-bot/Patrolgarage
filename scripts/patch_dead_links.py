#!/usr/bin/env python3
"""Replace dead outbound links in published pages.

consumer.gov.ae stopped resolving (NXDOMAIN, verified 2026-08-12 — no DNS answer,
no redirect, connection never establishes). 15 published posts linked to it. The
equivalent official material is on the UAE government portal, which is live and
covers consumer rights, complaint channels and the Ministry of Economy's Consumer
Protection Department.

Root cause is fixed separately in generate.py's AUTHORITATIVE_LINKS, so newly
generated posts stop reintroducing the dead domain. This script cleans up the
back catalogue.

Preserves file mtimes. journal_update.py derives each post's DISPLAYED DATE and
the blog listing sort order from mtime, so a bulk rewrite that touches timestamps
re-dates the entire blog to today — and publish.py runs journal_update.py on
every deploy, so it would ship.

Idempotent: reports "clean" for files with no dead link left.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEAD = re.compile(r"https?://(?:www\.)?consumer\.gov\.ae/?")
REPLACEMENT = (
    "https://u.ae/en/information-and-services/justice-safety-and-the-law/"
    "consumer-protection"
)


def targets():
    yield from sorted((ROOT / "blog").glob("*.html"))
    yield from sorted((ROOT / "drafts").glob("*.html"))
    for name in ("index.html", "services.html", "about.html", "contact.html"):
        p = ROOT / name
        if p.exists():
            yield p


def patch_file(path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    hits = len(DEAD.findall(html))
    if not hits:
        return "clean", 0

    new = DEAD.sub(REPLACEMENT, html)

    st = path.stat()
    path.write_text(new, encoding="utf-8")
    os.utime(path, (st.st_atime, st.st_mtime))  # mtime is content — see docstring
    return "patched", hits


def main():
    patched = total = 0
    for p in targets():
        status, hits = patch_file(p)
        if status == "patched":
            patched += 1
            total += hits
            print(f"  patched {p.relative_to(ROOT)}  ({hits} link{'s' if hits > 1 else ''})")
    print(f"\n{patched} file(s) patched, {total} dead link(s) replaced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
