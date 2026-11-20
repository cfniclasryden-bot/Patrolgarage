#!/usr/bin/env python3
"""Regression test for the 2026-11-20 pipeline rules (BLOG-AUDIT-2026-11-20 §6).
Identical in topchallenger-site and patrolgarage.

    python3 scripts/test_draft_only.py

1. Draft only: run_pipeline.py never calls publish.py; both the new-post path
   and the refresh path end in draft.py; the keyword_generator refill is off;
   check_editorial.py and check_post_rules.py are blocking gates.
2. draft.py moves the post and its images out of blog/ into drafts/review/,
   and drafts/ is excluded from the deploy.
3. The backlog: every slug is its keyword slugified; every service page is a
   confirmed one; every eligible topic has evidence; no topic is on the
   blocklist; on patrolgarage the order is problem/symptom, then reference,
   then comparison; on topchallenger every named photo exists on disk.
4. The picker: the first eligible topic, Abu Dhabi held back after a recent
   Abu Dhabi post (TC), nothing returned for a topic in review.
5. Service-page links: apply_related() writes one marked block, idempotently.
"""
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_rules as er  # noqa: E402

fails = []


def check(label, ok, detail=""):
    if not ok:
        fails.append(f"{label}{': ' + str(detail) if detail else ''}")


# 1 -------------------------------------------------------------- draft only
rp = (ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
code = "\n".join(l for l in rp.splitlines() if not l.lstrip().startswith("#"))
check("run_pipeline.py still calls publish.py", '"scripts/publish.py"' not in code)
check("run_pipeline.py does not park drafts", code.count('"scripts/draft.py"') >= 1)
check("refill still runs", "if False:  # keyword_generator refill disabled" in rp)
for g in ("check_editorial.py", "check_post_rules.py"):
    check(f"{g} is not a gate", f'"scripts/{g}"' in code)
vi = (ROOT / ".vercelignore").read_text(encoding="utf-8")
check("drafts/ is deployable", re.search(r"^drafts/\s*$", vi, re.M) is not None)

# 1b ------------------------------------------------------------- refresh path
import importlib  # noqa: E402
import check_post_rules as cpr  # noqa: E402
sys.argv = [sys.argv[0]]
rpm = importlib.import_module("run_pipeline")
live = sorted(p for p in (ROOT / "blog").glob("*.html") if p.name != "index.html")
if live:
    probs = cpr.problems(live[0], refresh=True)
    check("refresh path still demands a backlog entry", not any("editorial_backlog.json" in p for p in probs), probs)
    check("new-post path accepts a non-backlog post", any("editorial_backlog.json" in p for p in cpr.problems(live[0])))
rpm.REFRESH_MODE = True
g = [" ".join(c[0]) for c in rpm.gate_stages("x")]
check("refresh gate lacks --refresh", any("check_post_rules.py --refresh" in c for c in g), g)
check("refresh skips the banned-word gate", any("check_editorial.py" in c for c in g), g)
rpm.REFRESH_MODE = False
check("new-post gate runs with --refresh", not any("--refresh" in " ".join(c[0]) for c in rpm.gate_stages("x")))

# 1c ------------------------------------------- codes / meta openers / procedure
check("part code not caught", cpr.PART_CODE.search("a slipping JR710E gearbox") and cpr.PART_CODE.search("the VK56VD engine"))
check("fault code wrongly caught as a part code", not cpr.PART_CODE.search("P0430 and P0420 on a Y62"))
check("meta opener not caught", cpr.META_OPENER.search("This post covers the seven signs") and cpr.META_OPENER.search("In this article, the causes"))
check("answer-first meta wrongly caught", not cpr.META_OPENER.search("Check the fuse first and the cluster last."))
check("procedure claim not caught", cpr.FIRST_PERSON_PROC.search("We check bore dimensions once the unit is out.")
      and cpr.FIRST_PERSON_PROC.search("If the fluid is dark, we change it first."))
check("contact line wrongly caught", not cpr.FIRST_PERSON_PROC.search("Send us the mileage and we will tell you what it needs."))

# 2 --------------------------------------------------------------- draft.py
import draft  # noqa: E402
with tempfile.TemporaryDirectory() as d:
    t = Path(d)
    (t / "blog").mkdir()
    (t / "images" / "blog").mkdir(parents=True)
    (t / "blog" / "x-test.html").write_text("<html><title>x</title></html>", encoding="utf-8")
    (t / "images" / "blog" / "x-test.jpg").write_bytes(b"jpg")
    saved = draft.ROOT, er.REVIEW_DIR
    draft.ROOT, er.REVIEW_DIR = t, t / "drafts" / "review"
    try:
        draft.park("x-test")
    finally:
        draft.ROOT, er.REVIEW_DIR = saved
    check("draft left the post in blog/", not (t / "blog" / "x-test.html").exists())
    check("draft did not park the post", (t / "drafts" / "review" / "x-test" / "x-test.html").exists())
    check("draft did not move the image", (t / "drafts" / "review" / "x-test" / "images" / "x-test.jpg").exists())
    check("draft wrote no REVIEW.md", (t / "drafts" / "review" / "x-test" / "REVIEW.md").exists())

# 3 ---------------------------------------------------------------- backlog
topics = er.load_backlog()
confirmed = er.confirmed_service_pages()
import topic_blocklist  # noqa: E402
for e in topics:
    check(f"slug != slugify(keyword): {e['slug']}", e["slug"] == er.slugify(e["keyword"]))
    check(f"unconfirmed service page: {e['slug']}", e["service_page"] in confirmed, e["service_page"])
    check(f"blocklisted topic in the backlog: {e['slug']}",
          not topic_blocklist.is_blocked(e["keyword"]) or e.get("blocked_by"))
    if not e.get("blocked_by") and not e.get("hold_until"):
        probs = [p for p in er.topic_problems(e) if p not in ("already published", "draft already waiting for review")]
        if probs and not any(p.startswith("no evidence") for p in probs):
            fails.append(f"eligible-looking topic fails: {e['slug']}: {probs}")
eligible = [e for e in topics if not er.topic_problems(e)]
check("no eligible topic at all", eligible)
for e in eligible:
    check(f"eligible without evidence: {e['slug']}", not er.evidence_problems(e))
if er.SITE == "pg":
    rank = {"symptom": 0, "problem": 0, "reference": 1, "comparison": 2}
    seq = [rank.get(e.get("type"), 1) for e in topics]
    check("PG backlog order: problem/symptom, then reference, then comparison", seq == sorted(seq), seq)
    check("PG backlog names a photo", not any(e.get("photo") for e in topics))
else:
    for e in topics:
        if e.get("photo"):
            check(f"photo missing on disk: {e['photo']}", (ROOT / "images" / f"{e['photo']}.jpg").exists())
            check(f"photo not usable (no alt): {e['photo']}", er.photo_for(e["slug"]) is not None)

# 4 ----------------------------------------------------------------- picker
first = eligible[0]["slug"] if eligible else None
check("picker does not take the first eligible topic", er.next_topic() and er.next_topic()["slug"] == first)
if er.SITE == "tc":
    ad = [e for e in eligible if e.get("area") == "abu-dhabi"]
    if ad:
        non_ad = [e["slug"] for e in eligible if e.get("area") != "abu-dhabi"]
        pick = er.next_topic(recent_slugs=["y62-limp-mode-abu-dhabi"], skip_slugs=set(non_ad))
        check("Abu Dhabi topic picked right after an Abu Dhabi post (1 in 4 rule)", pick is None, pick)
if first:
    nxt = er.next_topic(skip_slugs={first})
    check("skip list ignored", nxt is None or nxt["slug"] != first)

# 5 ------------------------------------------------------- service-page links
with tempfile.TemporaryDirectory() as d:
    page = Path(d) / "svc.html"
    page.write_text("<html><body><main><p>x</p></main><footer>f</footer></body></html>", encoding="utf-8")
    block = er.related_block([{"slug": "a-post", "title": "A post"}])
    html = page.read_text()
    once = html.replace("</main>", block + "\n</main>", 1)
    twice = re.sub(re.escape(er.RP_START) + r".*?" + re.escape(er.RP_END), lambda _m: block, once, flags=re.S)
    check("related block not idempotent", once == twice)
    check("related block has no link", "/blog/a-post" in block)

for f in fails:
    print("  FAIL ", f)
if fails:
    print(f"[!] draft-only / backlog regression FAILED - {len(fails)} problem(s)")
    sys.exit(1)
print(f"[OK] draft only: no publish in the pipeline, drafts parked outside the deploy; "
      f"backlog {len(topics)} topics, {len(eligible)} eligible, all evidenced and on confirmed pages")
