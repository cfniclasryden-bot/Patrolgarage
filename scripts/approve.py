#!/usr/bin/env python3
"""Publish a reviewed draft (2026-11-20). Identical in topchallenger-site and
patrolgarage. The ONLY way a pipeline post reaches the live site: the cron
stops at drafts/review/<slug>/ (draft.py) and a person runs this after reading
the draft and its REVIEW.md.

    python3 scripts/approve.py <slug> --check     # gates only, nothing moves
    python3 scripts/approve.py <slug>             # publish

On publish, in order:
  1. re-runs check_editorial.py and check_post_rules.py on the draft (any block
     stops here, nothing moves);
  2. moves the post and its images back into blog/ and images/blog/;
  3. TC: rewrites the cluster pillar's "In this cluster" list and any cross
     link that points at this post (assemble.update_pillar / backfill);
  4. links the post from its service page ("From the blog" block,
     scripts/related_posts.json, editorial_rules.apply_related);
  5. publish.publish(): blog hub / listing (journal_update.py), sitemap, commit
     and push, deploy, then IndexNow for the changed URLs;
  6. Supabase (when SUPABASE_URL / SUPABASE_SERVICE_KEY are set): the row is
     marked published, editorial_status 'approved'.
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
import editorial_rules as er  # noqa: E402


def gates(path):
    ok = True
    for g in ("check_editorial.py", "check_post_rules.py"):
        r = subprocess.run(["python3", f"scripts/{g}", str(path)], cwd=ROOT)
        ok = ok and r.returncode == 0
    return ok


def supabase_mark(slug):
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        print("    [i] Supabase env not set: mark the row published by hand")
        return
    import requests
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.patch(f"{url}/rest/v1/articles", headers=h, params={"slug": f"eq.{slug}"},
                       json={"status": "published", "editorial_status": "approved",
                             "published_at": datetime.now(timezone.utc).isoformat()})
    print(f"    Supabase: {r.status_code}")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 1
    slug = args[0]
    src = er.REVIEW_DIR / slug / f"{slug}.html"
    if not src.exists():
        print(f"[!] no draft at {src}")
        return 1
    if not gates(src):
        print("[!] the draft fails a gate: fix it (or reject it) before publishing")
        return 2
    if "--check" in argv:
        print("[OK] gates pass; nothing moved (--check)")
        return 0

    post = ROOT / "blog" / f"{slug}.html"
    shutil.move(str(src), str(post))
    for img in (er.REVIEW_DIR / slug / "images").glob("*"):
        shutil.move(str(img), str(ROOT / "images" / "blog" / img.name))

    if er.SITE == "tc":
        import assemble
        import site_config
        entry = site_config.CLUSTERS.get(slug, {})
        if entry.get("role") == "spoke" and entry.get("pillar"):
            assemble.update_pillar(entry["pillar"])
        elif entry.get("role") == "pillar":
            assemble.backfill_cross_links(slug)

    e = er.entry_for(slug)
    title = re.sub(r"\s*\|.*$", "", re.search(r"<title>(.*?)</title>", post.read_text(encoding="utf-8"), re.S).group(1)).strip()
    er.add_related(e["service_page"], slug, title)
    changed = er.apply_related(write=True)
    print(f"[+] service page link: {changed or 'already in place'}")

    shutil.rmtree(er.REVIEW_DIR / slug, ignore_errors=True)

    import publish
    keyword = e["keyword"] if er.SITE == "tc" else slug
    ok = publish.publish(keyword)
    if ok:
        supabase_mark(slug)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
