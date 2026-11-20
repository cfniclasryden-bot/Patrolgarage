#!/usr/bin/env python3
"""Park a generated post for human review instead of publishing it (2026-11-20).
Identical in topchallenger-site and patrolgarage. Called by run_pipeline.py in
place of publish.py; nothing here deploys.

    python3 scripts/draft.py <slug>

1. Moves blog/<slug>.html and images/blog/<slug>.* into drafts/review/<slug>/
   (drafts/ is in .vercelignore on both sites, so a review draft can never ship).
2. Writes drafts/review/<slug>/REVIEW.md: the backlog entry and its evidence,
   the gate results, and the reviewer checklist (BLOG-AUDIT-2026-11-20 §6.4).
3. In the cloud only, resets every other tracked file the content stages touched
   (a pillar's cluster list, cross links): those links would point at a post
   that is not live. approve.py re-applies them at publish time.
4. Commits drafts/ and research/ and pushes, so the draft is reviewable in the
   repo. No deploy, no sitemap, no IndexNow.

Publishing is approve.py, run by a person after reading the draft.
"""
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_rules as er  # noqa: E402

CHECKLIST = """## Reviewer checklist (BLOG-AUDIT-2026-11-20 §6.4)

- [ ] 1. Every service the post presents as our work is confirmed at the branch it names.
- [ ] 2. No offer, price, "same-day", "best", "expert", warranty/genuine claim or accessory.
- [ ] 3. The answer is in the first 60 words.
- [ ] 4. One service link, to the right page ({service_page}).
- [ ] 5. The CTA is for the right branch / site.
- [ ] 6. The photo is real (TC) or labelled as an illustration, and shows the topic.
- [ ] 7. No fact without a source (owner, manual or measured).

Approve:   python3 scripts/approve.py {slug}
Reject:    delete drafts/review/{slug}/ and set the Supabase row editorial_status = 'rejected'
"""


def _gate(cmd, path, refresh=False):
    extra = ["--refresh"] if (refresh and cmd == "check_post_rules.py") else []
    r = subprocess.run(["python3", f"scripts/{cmd}", *extra, str(path)], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def park(slug):
    post = ROOT / "blog" / f"{slug}.html"
    if not post.exists():
        raise SystemExit(f"[!] draft.py: {post} does not exist")
    dest = er.REVIEW_DIR / slug
    (dest / "images").mkdir(parents=True, exist_ok=True)
    # A REFRESH rewrites a post that is already live (tracked in git). Park the
    # rewrite and put the live version straight back, so neither a local run nor
    # the next deploy loses the published post while the rewrite waits.
    rel_post = f"blog/{slug}.html"
    tracked = subprocess.run(["git", "cat-file", "-e", f"HEAD:{rel_post}"], cwd=ROOT,
                             capture_output=True).returncode == 0
    shutil.move(str(post), str(dest / post.name))
    imgs = sorted((ROOT / "images" / "blog").glob(f"{slug}.*"))
    for img in imgs:
        shutil.move(str(img), str(dest / "images" / img.name))
    if tracked:
        restore = [rel_post] + [f"images/blog/{i.name}" for i in imgs
                                if subprocess.run(["git", "cat-file", "-e", f"HEAD:images/blog/{i.name}"],
                                                  cwd=ROOT, capture_output=True).returncode == 0]
        subprocess.run(["git", "checkout", "HEAD", "--", *restore], cwd=ROOT, check=False)
        print(f"[+] refresh: live {rel_post} restored from git; the rewrite waits in review")

    e = er.entry_for(slug) or {}
    refresh = tracked
    lines = [f"# {'REFRESH of a live post' if refresh else 'Draft'} for review: {slug}", "",
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. NOT LIVE.", "",
             "## Backlog entry", "", "```json"]
    import json
    lines += [json.dumps(e, indent=1, ensure_ascii=False), "```", "", "## Gates on the draft", ""]
    for g in ("check_editorial.py", "check_post_rules.py"):
        code, out = _gate(g, dest / post.name, refresh=refresh)
        lines += [f"### {g}: {'PASS' if code == 0 else 'FAIL'}", "", "```", out[-3000:], "```", ""]
    lines.append(CHECKLIST.format(service_page=e.get("service_page", "the page the post links"), slug=slug))
    (dest / "REVIEW.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[+] draft parked in drafts/review/{slug}/ (not live)")
    return dest


def commit(slug):
    import publish
    if not (publish.in_cloud() and publish._is_repo()):
        print("    [i] not in the cloud: draft left on disk, nothing reset, committed or pushed")
        return True
    # Undo side effects of the content stages on OTHER tracked files.
    publish._git(["checkout", "--", "blog/", "services/", "index.html"], check=False)
    publish._ensure_identity_and_remote()
    # -f for the one review folder only: patrolgarage .gitignores drafts/, and
    # without it the draft never reached the repo (found 2026-11-20). research/
    # is added WITHOUT -f, so a site that ignores it keeps ignoring it.
    publish._git(["add", "-f", f"drafts/review/{slug}"], check=False)
    publish._git(["add", "research/"], check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged.returncode == 0:
        return True
    publish._git(["commit", "-m", f"Draft for review (not published): {slug}"])
    if not publish.git_ready():
        print("    [i] GH_TOKEN unset: committed locally, not pushed")
        return True
    branch = getattr(publish, "BRANCH", "main")
    r = publish._git(["push", "origin", f"HEAD:{branch}"], check=False)
    if r.returncode != 0:
        print("    [!] push failed: the draft exists only in this container")
        return False
    print(f"    [+] draft pushed to origin/{branch}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(1)
    park(sys.argv[1])
    sys.exit(0 if commit(sys.argv[1]) else 1)
