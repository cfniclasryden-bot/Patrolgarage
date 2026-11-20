#!/usr/bin/env python3
"""The blog rules from BLOG-AUDIT-2026-11-20 §6, as code. Identical in
topchallenger-site and patrolgarage; the site is detected from the tree
(topchallenger-site has scripts/site_config.py, patrolgarage does not).

    python3 scripts/editorial_rules.py            # backlog report: what is eligible, what is not, why
    python3 scripts/editorial_rules.py --next     # the topic the pipeline would draft next

WHAT IT ENFORCES

1. Evidence-based topic choice. The ONLY source of topics is
   scripts/editorial_backlog.json, in its order. Every entry carries its
   evidence; an entry qualifies only with at least one of:
     - gsc: a query we already show for (5+ impressions in 90 days, position
       20 or better), with the numbers;
     - rank_fix: an open gap in research/RANK-FIX-PLAN-2026-11-12.md;
     - volume (+ volume_source) or paa: measured demand (KEYWORD-RESEARCH-2026-10).
   Supabase rows that are not in the backlog are never picked.
2. Confirmed services only. TC: the entry's service_page must be one of the
   confirmed service pages (site_config.SERVICE_PAGES). PG: one of PG's own
   service / service-area pages. Plus the topic blocklist (accessories, mods,
   unconfirmed services, and on PG cost/price topics), and an entry that waits
   on an owner answer (blocked_by) or a measurement date (hold_until) is skipped.
3. One service link + branch CTA, real photos on TC only: the backlog names the
   service page and the branch; check_post_rules.py verifies the built post.
4. Mix: on TC at most 1 in 4 posts is Abu Dhabi (the last three drafted or
   published plus the candidate).
5. Draft only. The pipeline stops at drafts/review/<slug>/; approve.py publishes.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

SITE = "tc" if (ROOT / "scripts" / "site_config.py").exists() else "pg"
BACKLOG = ROOT / "scripts" / "editorial_backlog.json"
RELATED = ROOT / "scripts" / "related_posts.json"
REVIEW_DIR = ROOT / "drafts" / "review"

PG_SERVICE_PAGES = {
    "/services/y62-gearbox-transmission-dubai.html",
    "/services/nissan-patrol-v8-engine.html",
    "/services/y62-major-service-dubai.html",
    "/services.html",
    "/y62-garage-dubai.html",
    "/nissan-patrol-abu-dhabi.html",
}

# TC workshop photos that may head a post (BLOG-AUDIT-2026-11-20 §6.2). Alts are
# the ones already written against each photograph on the service pages and in
# HERO_OVERRIDES. Left out on purpose: the roundel photos (diagnostics-scan,
# scan-tool-cabin, drain-pan-underside, team-*) still await the client's
# decision, and the frames whose alt says "genuine" (gearbox-atf, cooling-parts,
# brake-pads) would put a banned word on the page. PG never uses these: they
# show Top Challenger's premises.
TC_PHOTOS = {
    "top-challenger-gearbox-bench": {
        "width": 1200, "height": 1500, "object_position": "50% 50%",
        "alt": "Gearbox case with its pan off and a torque converter beside it on the bench at the "
               "Top Challenger workshop in Ras Al Khor, Dubai, a technician working on cylinder heads "
               "further down the same bench"},
    "top-challenger-gearbox-on-jack": {
        "width": 1200, "height": 800, "object_position": "90% 65%",
        "alt": None},  # alt taken from HERO_OVERRIDES at use time
    "top-challenger-engine-bay-open": {
        "width": 1600, "height": 1067, "object_position": "38% 50%",
        "alt": None},
    "top-challenger-engine-rebuild": {
        "width": 1200, "height": 1500, "object_position": "50% 50%",
        "alt": "White Nissan Patrol Y62, V8 badge on the front wing, with its front bumper removed and "
               "the headlight and bumper reinforcement exposed, parked beside workshop racking stacked "
               "with cylinder heads and engine blocks"},
    "top-challenger-ac-compressor": {
        "width": 1200, "height": 1500, "object_position": "50% 50%",
        "alt": "Two air conditioning compressors side by side on the workshop floor, a corroded "
               "original next to a clean replacement unit"},
    "top-challenger-cooling-stack": {
        "width": 1600, "height": 1280, "object_position": "50% 50%",
        "alt": "Front-end cooling stack out of a vehicle and standing on a workshop rack at Top "
               "Challenger in Ras Al Khor, Dubai, the air conditioning condenser in front of the "
               "radiator, its receiver-drier bottle at the right and both horns still mounted on the "
               "front carrier above, the fins dusty and stained but not blocked"},
    "top-challenger-suspension-hub": {
        "width": 1200, "height": 1500, "object_position": "50% 50%",
        "alt": "Front wheel removed on a Nissan Patrol Y62, brake disc, hub and coil spring exposed "
               "while the suspension is inspected"},
}

EVIDENCE_GSC_MIN_IMPR = 5
EVIDENCE_GSC_MAX_POS = 20.0


def load_backlog():
    data = json.loads(BACKLOG.read_text(encoding="utf-8"))
    if data.get("site") != SITE:
        raise SystemExit(f"[!] {BACKLOG.name} is for site {data.get('site')!r}, this tree is {SITE!r}")
    return data["topics"]


def entry_for(slug_or_keyword):
    s = slugify(slug_or_keyword)
    for e in load_backlog():
        if e["slug"] == s or slugify(e["keyword"]) == s:
            return e
    return None


def slugify(text):
    t = re.sub(r"[^\w\s-]", "", str(text).lower().strip())
    return re.sub(r"[\s_-]+", "-", t).strip("-")


def confirmed_service_pages():
    if SITE == "tc":
        import site_config
        return {v["url"] for v in site_config.SERVICE_PAGES.values()}
    return set(PG_SERVICE_PAGES)


def evidence_problems(e):
    ev = e.get("evidence") or {}
    ok = []
    g = ev.get("gsc")
    if g and g.get("impressions", 0) >= EVIDENCE_GSC_MIN_IMPR and g.get("position", 99) <= EVIDENCE_GSC_MAX_POS:
        ok.append("gsc")
    if ev.get("rank_fix"):
        ok.append("rank_fix")
    if ev.get("volume") and ev.get("volume_source"):
        ok.append("volume")
    if ev.get("paa"):
        ok.append("paa")
    return [] if ok else ["no evidence (needs GSC 5+ impressions at pos <= 20, a rank-fix gap, "
                          "measured volume, or a People Also Ask question)"]


def live_slugs():
    return {p.stem for p in (ROOT / "blog").glob("*.html") if p.name != "index.html"}


def in_review_slugs():
    return {p.name for p in REVIEW_DIR.glob("*") if p.is_dir()} if REVIEW_DIR.exists() else set()


def topic_problems(e, today=None):
    """Why this backlog entry may not be drafted now. Empty list = eligible."""
    import topic_blocklist
    today = today or date.today().isoformat()
    out = list(evidence_problems(e))
    if e.get("service_page") not in confirmed_service_pages():
        out.append(f"service page {e.get('service_page')!r} is not a confirmed service page")
    for t in (e["keyword"], e["slug"]):
        if topic_blocklist.is_blocked(t):
            out.append(f"blocked topic ({topic_blocklist.blocked_topic(t)})")
            break
    if e.get("blocked_by"):
        out.append(f"waits on {e['blocked_by']}")
    if e.get("hold_until") and e["hold_until"] > today:
        out.append(f"on hold until {e['hold_until']}")
    if e["slug"] in live_slugs():
        out.append("already published")
    if e["slug"] in in_review_slugs():
        out.append("draft already waiting for review")
    if SITE == "tc" and e.get("photo") and e["photo"] not in TC_PHOTOS:
        out.append(f"photo {e['photo']!r} is not in TC_PHOTOS")
    if SITE == "pg" and e.get("photo"):
        out.append("PG never uses Top Challenger photos")
    return out


def is_ad(e):
    return e.get("area") == "abu-dhabi"


def next_topic(recent_slugs=(), skip_slugs=(), today=None):
    """First eligible backlog entry, in backlog order, or None.

    recent_slugs: the last posts drafted or published, newest first (for the TC
    Abu Dhabi mix). skip_slugs: slugs to pass over this run (e.g. requeued).
    """
    entries = load_backlog()
    by_slug = {x["slug"]: x for x in entries}
    recent_ad = sum(1 for s in list(recent_slugs)[:3]
                    if (by_slug.get(s, {}).get("area") == "abu-dhabi"
                        or re.search(r"abu-dhabi|mussafah", s)))
    for e in entries:
        if e["slug"] in skip_slugs or topic_problems(e, today):
            continue
        if SITE == "tc" and is_ad(e) and recent_ad >= 1:
            continue
        return e
    return None


def photo_for(slug):
    """TC: the hero override dict for a backlog entry's chosen workshop photo, or None."""
    if SITE != "tc":
        return None
    e = entry_for(slug)
    if not e or not e.get("photo"):
        return None
    stem = e["photo"]
    p = dict(TC_PHOTOS[stem])
    if not p.get("alt"):
        import site_config
        for o in site_config.HERO_OVERRIDES.values():
            if o.get("stem") == stem and o.get("alt"):
                p["alt"] = o["alt"]
                break
    if not p.get("alt"):
        return None
    p["stem"] = stem
    return p


# --- Supabase: the pipeline's picker -----------------------------------------

def pick_row(base_url, headers, site_id, requests_mod, write=True, log=print):
    """The next backlog topic as a Supabase articles row: (row, reason).

    Replaces the old pickers (oldest pending row, keyword_generator refill).
    Skips a topic whose row is retired, archived, rejected, published or already
    in review, and one moved to the back of the queue in the last 7 days after
    two failed runs (run_pipeline.requeue_if_stuck). Creates the row when the
    topic has none (write=True), so Supabase still logs every run.
    """
    from datetime import datetime, timedelta, timezone
    rows = requests_mod.get(f"{base_url}/rest/v1/articles", headers=headers,
                            params={"site_id": f"eq.{site_id}",
                                    "select": "id,keyword,slug,status,editorial_status,editorial_notes,created_at,published_at"}).json()
    by_slug = {}
    for r in rows:
        by_slug.setdefault(r.get("slug") or slugify(r["keyword"]), r)
    published = sorted((r for r in rows if r["status"] == "published" and r.get("published_at")),
                       key=lambda r: r["published_at"], reverse=True)
    recent = [r.get("slug") or slugify(r["keyword"]) for r in published][:3]
    recent = sorted(in_review_slugs()) + recent
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    skip = set()
    for sl, r in by_slug.items():
        if r["status"] in ("retired", "archived", "published") or r.get("editorial_status") in ("rejected", "review"):
            skip.add(sl)
        elif "Moved to the back of the queue" in (r.get("editorial_notes") or "") and (r.get("created_at") or "") > cutoff:
            skip.add(sl)
    e = next_topic(recent_slugs=recent, skip_slugs=skip)
    if not e:
        return None, "no eligible topic in editorial_backlog.json (see `python3 scripts/editorial_rules.py`)"
    row = by_slug.get(e["slug"])
    if row is None and write:
        ev = json.dumps(e.get("evidence", {}), ensure_ascii=False)
        r = requests_mod.post(f"{base_url}/rest/v1/articles",
                              headers={**headers, "Content-Type": "application/json", "Prefer": "return=representation"},
                              json={"site_id": site_id, "keyword": e["keyword"], "slug": e["slug"],
                                    "status": "pending", "editorial_status": "queued",
                                    "editorial_notes": f"From editorial_backlog.json. Evidence: {ev}"[:2000]})
        row = (r.json() or [None])[0] if r.ok else None
        if row is None:
            return None, f"could not create the Supabase row for {e['slug']}: {r.status_code} {r.text[:200]}"
    if row is None:
        row = {"id": None, "keyword": e["keyword"], "slug": e["slug"]}
    row["keyword"], row["slug"] = e["keyword"], e["slug"]
    log(f"[backlog] next topic: {e['keyword']} -> {e['service_page']} "
        f"(evidence: {', '.join(k for k in (e.get('evidence') or {}))})")
    return row, None


# --- related posts on service pages (on publish) -----------------------------

RP_START = "<!-- RELATED-POSTS:START -->"
RP_END = "<!-- RELATED-POSTS:END -->"


def load_related():
    try:
        return json.loads(RELATED.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def add_related(service_page, slug, title):
    data = load_related()
    items = data.setdefault(service_page, [])
    if not any(i["slug"] == slug for i in items):
        items.append({"slug": slug, "title": title})
    RELATED.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _post_href(slug):
    return f"/blog/{slug}" if SITE == "tc" else f"/blog/{slug}.html"


def related_block(items):
    lis = "".join(f'<li><a href="{_post_href(i["slug"])}">{i["title"]}</a></li>' for i in items)
    if SITE == "tc":
        inner = (f'<div class="container"><div class="svc-related"><h3>From the blog</h3>'
                 f'<ul>{lis}</ul></div></div>')
    else:
        inner = ('<section class="related-posts" style="padding:3rem 1.5rem;">'
                 '<div style="max-width:1100px;margin:0 auto;"><h3 style="margin:0 0 1rem;">From the blog</h3>'
                 f'<ul style="list-style:none;margin:0;padding:0;line-height:2.2;">{lis}</ul></div></section>')
    return f"{RP_START}{inner}{RP_END}"


def page_file(service_page):
    rel = service_page.lstrip("/")
    if SITE == "tc" and not rel.endswith(".html"):
        rel += ".html"
    return ROOT / rel


def apply_related(write=True):
    """Write each registered service page's 'From the blog' block. mtime kept.
    Idempotent; a page with no registered posts is left untouched."""
    import os
    changed = []
    for service_page, items in load_related().items():
        items = [i for i in items if i["slug"] in live_slugs()]
        f = page_file(service_page)
        if not items or not f.exists():
            continue
        html = f.read_text(encoding="utf-8")
        block = related_block(items)
        if RP_START in html:
            new = re.sub(re.escape(RP_START) + r".*?" + re.escape(RP_END), lambda _m: block, html, flags=re.S)
        else:
            anchor = None
            for a in ("</main>", '<section class="cta-banner">', "<footer"):
                if a in html:
                    anchor = a
                    break
            if not anchor:
                continue
            new = html.replace(anchor, block + "\n" + anchor, 1)
        if new != html:
            changed.append(f.relative_to(ROOT).as_posix())
            if write:
                st = f.stat()
                f.write_text(new, encoding="utf-8")
                os.utime(f, (st.st_atime, st.st_mtime))
    return changed


def main(argv):
    today = date.today().isoformat()
    if "--next" in argv:
        e = next_topic(today=today)
        print(json.dumps(e, indent=1) if e else "no eligible topic")
        return 0
    for i, e in enumerate(load_backlog(), 1):
        probs = topic_problems(e, today)
        print(f"{i:2}. {'OK  ' if not probs else 'SKIP'} {e['keyword']}  -> {e['service_page']}"
              + (f"   [{'; '.join(probs)}]" if probs else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
