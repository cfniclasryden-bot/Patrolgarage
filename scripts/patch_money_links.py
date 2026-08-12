#!/usr/bin/env python3
"""Back-fill one in-body /services link (plus a home link on pillars) into every
published post. See money_links.py for the rule and the reasoning.

New posts get this automatically via assemble.py; this script covers the posts
that were already published.

Preserves file mtimes. journal_update.py derives each post's DISPLAYED DATE and
the blog listing sort order from mtime, so a bulk rewrite that touches timestamps
re-dates the entire blog to today — and publish.py runs journal_update.py on
every deploy, so it would ship.

Usage:
    python3 scripts/patch_money_links.py --dry-run
    python3 scripts/patch_money_links.py
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import money_links

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"


def patch_file(path, dry_run):
    html = path.read_text(encoding="utf-8", errors="ignore")
    slug = path.stem

    m = re.search(r"<article>(.*?)</article>", html, re.S)
    if not m:
        return "no-article", ""

    body = m.group(1)
    if money_links.already_linked(body):
        return "skip", "already linked"

    new_body = money_links.add_money_links(body, slug)
    if new_body == body:
        return "no-slot", "no safe insertion point"

    # Report the sentence that was added.
    added = new_body[len(os.path.commonprefix([body, new_body])):]
    added = re.sub(r"\s+", " ", added.split(money_links.MARKER)[0]).strip()

    if not dry_run:
        new_html = html[:m.start(1)] + new_body + html[m.end(1):]
        st = path.stat()
        path.write_text(new_html, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))  # mtime is content

    return "patched", added


def main():
    dry_run = "--dry-run" in sys.argv
    counts = {}
    for p in sorted(BLOG.glob("*.html")):
        if p.name == "index.html":
            continue
        status, note = patch_file(p, dry_run)
        counts[status] = counts.get(status, 0) + 1
        if status in ("patched", "no-slot"):
            pillar = " [PILLAR]" if p.stem in money_links.PILLARS else ""
            print(f"  {status:8} {p.name}{pillar}")
            if note and status == "patched":
                print(f"           -> {note}")

    print("\n" + ("DRY RUN — nothing written" if dry_run else "WRITTEN"))
    print("  " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
