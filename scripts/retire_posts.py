#!/usr/bin/env python3
"""Retire blog posts into other pages: links repointed, files removed, 301s added.

Written for BLOG-AUDIT-2026-11-20 §5 (9 PG posts merged or redirected), kept so
the next merge is the same mechanical job, not a fresh hand edit:

    python3 scripts/retire_posts.py            # dry run
    python3 scripts/retire_posts.py --write    # apply, then gen_redirects / gen_vercel_json

Per shipped page (shipped_pages.py):
  * a <li> holding only a link to a retired post is removed (the "Related
    reading" lists); a list left empty loses its <div class="related-reading">.
  * any other link to it is repointed to the target, anchor kept.
  * blog/index.html and blog/page/* are skipped: journal_update.py rebuilds them.
mtimes are preserved (mtime IS the displayed date and the listing order here).

Then the post and its hero files are deleted, a both-forms 301 block is added
to the hand-written part of _redirects, and any EXISTING rule whose destination
is a retired post is repointed to that post's target (one hop, no chain).
vercel.json is generated from _redirects: run gen_vercel_json.py afterwards.

Content merges (a section in the target) are done separately, by hand.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

RETIRE = {
    "nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026": "/blog/nissan-patrol-differential-repair-cost-uae.html",
    "y62-abs-sensor-replacement-cost-dubai-2026": "/blog/nissan-patrol-warning-lights-meaning.html",
    "nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026": "/blog/nissan-patrol-brake-problems.html",
    "y62-fuel-injector-cleaning-cost-dubai-2026": "/blog/nissan-patrol-losing-power.html",
    "nissan-patrol-y62-cv-joint-replacement-cost-uae-2026": "/blog/nissan-patrol-vibration-when-driving.html",
    "y62-rear-air-bag-replacement-cost-uae-2026": "/blog/nissan-patrol-y62-problems-dubai.html",
    "nissan-patrol-mechanic-al-quoz": "/y62-garage-dubai.html",
    "nissan-patrol-long-term-ownership-abu-dhabi": "/blog/is-the-nissan-patrol-reliable-in-abu-dhabi.html",
    "buying-a-used-nissan-patrol": "/blog/nissan-patrol-pre-purchase-inspection.html",
}
BLOCK_MARK = "# 2026-11-20: BLOG-AUDIT-2026-11-20 §5 merges"


def _href_re(slug):
    return r'(?:https://patrolgarage\.ae)?(?:\.\.)?/blog/' + re.escape(slug) + r'(?:\.html)?(?:#[^"\']*)?'


def rewrite(html):
    out = html
    for old, target in RETIRE.items():
        h = _href_re(old)
        out = re.sub(r'<li>\s*<a href=["\']' + h + r'["\'][^>]*>[^<]*</a>\s*</li>\s*', "", out)
        out = re.sub(r'href=(["\'])' + h + r'\1', lambda m, t=target: f'href={m.group(1)}{t}{m.group(1)}', out)
    out = re.sub(r'<div class="related-reading">\s*<h3>[^<]*</h3>\s*<ul>\s*</ul>\s*</div>', "", out)
    return out


def files():
    import shipped_pages
    for p in shipped_pages.shipped_pages():
        rel = p.relative_to(ROOT).as_posix()
        if rel == "blog/index.html" or rel.startswith("blog/page/"):
            continue
        if rel.startswith("blog/") and p.stem in RETIRE:
            continue
        yield p


def update_redirects(text):
    lines = text.split("\n")
    # repoint existing rules that land on a retired post
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) >= 3 and not line.startswith("#"):
            dest = parts[1]
            for old, target in RETIRE.items():
                if dest in (f"/blog/{old}.html", f"/blog/{old}"):
                    lines[i] = line.replace(dest, target, 1)
    text = "\n".join(lines)
    if BLOCK_MARK in text:
        return text
    block = [BLOCK_MARK,
             "# (merged or redirected into the closest live page; both forms, no file).",
             "# Built by scripts/retire_posts.py."]
    for old, target in RETIRE.items():
        block.append(f"/blog/{old}.html  {target} 301")
        block.append(f"/blog/{old}  {target} 301!")
    anchor = "# Internal docs"
    assert text.count(anchor) == 1
    return text.replace(anchor, "\n".join(block) + "\n\n" + anchor)


def main(argv):
    write = "--write" in argv
    changed = []
    for p in files():
        t = p.read_text(encoding="utf-8")
        n = rewrite(t)
        if n != t:
            changed.append(p.relative_to(ROOT).as_posix())
            if write:
                st = p.stat()
                p.write_text(n, encoding="utf-8")
                os.utime(p, (st.st_atime, st.st_mtime))
    print(f"links rewritten in {len(changed)} page(s): {changed}")
    gone = []
    for old in RETIRE:
        for p in [ROOT / "blog" / f"{old}.html", *sorted((ROOT / "images" / "blog").glob(f"{old}.*"))]:
            if p.exists():
                gone.append(p.relative_to(ROOT).as_posix())
                if write:
                    p.unlink()
    print(f"files removed: {len(gone)}")
    rp = ROOT / "_redirects"
    t = rp.read_text()
    n = update_redirects(t)
    if write and n != t:
        rp.write_text(n)
    print(f"_redirects {'updated' if n != t else 'unchanged'}")
    if write:
        left = [(p.name, o) for p in files() for o in RETIRE
                if re.search(r'href=["\']' + _href_re(o) + r'["\']', p.read_text(encoding="utf-8"))]
        if left:
            print("[!] links still pointing at retired posts:", left)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
