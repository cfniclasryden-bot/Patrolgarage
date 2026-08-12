#!/usr/bin/env python3
"""Decide which post is due a refresh. DRY RUN BY DEFAULT — enqueues nothing.

Tiering follows the SEO playbook's cadence, keyed off commercial intent:

    BOFU  cost / price / vs / specialist / near        every  90 days
    MOFU  problems / symptoms / how / why / guide      every 180 days
    TOFU  everything else                              every 365 days

"Last refreshed" is read from the in-article "Last updated:" stamp, falling back
to the file mtime. NOTE both of those currently say the publish date for all 44
posts, because none has ever been refreshed — so the first run finds the entire
catalogue overdue. That is exactly why this is dry-run by default and why it
enqueues at most ONE post per day: the queue must be eyeballed before anything
touches a page ranking at position 4.

Ordering. Without GSC the queue is ordered by how overdue a post is. With GSC
wired (keyword_gaps.py), it is ordered by opportunity instead — impressions x
position-closeness-to-page-1 — so the posts nearest a breakthrough go first.

Enqueue writes a row to Supabase `article_refreshes` with mode=patch. Full
regeneration is never scheduled; it stays a manual, deliberate act.

Usage:
    python3 scripts/refresh_scheduler.py                 # dry run, prints queue
    python3 scripts/refresh_scheduler.py --show-all      # full 44-post table
    python3 scripts/refresh_scheduler.py --enqueue       # actually queue ONE
"""
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
DAILY_ENQUEUE_CAP = 1

TIERS = [
    ("BOFU", re.compile(r"cost|price|cheap|vs-|-vs-|specialist|near|best-price|al-futtaim"), 90),
    ("MOFU", re.compile(r"problem|symptom|how|why|guide|fix|repair|replacement"), 180),
    ("TOFU", re.compile(r"."), 365),
]


def tier_for(slug):
    for name, rx, days in TIERS:
        if rx.search(slug):
            return name, days
    return "TOFU", 365


def last_refreshed(path):
    html = path.read_text(errors="ignore")
    m = re.search(r'<p class="last-updated">Last updated:\s*([^<]+)</p>', html)
    if m:
        raw = m.group(1).strip()
        for fmt in ("%B %Y", "%d %B %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt), "stamp"
            except ValueError:
                pass
    return datetime.fromtimestamp(path.stat().st_mtime), "mtime"


def build_queue():
    today = datetime.now()
    rows = []
    for p in sorted(BLOG.glob("*.html")):
        if p.name == "index.html":
            continue
        tier, cadence = tier_for(p.stem)
        when, src = last_refreshed(p)
        age = (today - when).days
        overdue = age - cadence
        rows.append({"slug": p.stem, "tier": tier, "cadence": cadence,
                     "age": age, "overdue": overdue, "src": src, "due": overdue >= 0})
    rows.sort(key=lambda r: (-r["overdue"], r["slug"]))
    return rows


def enqueue(row):
    """Insert a patch-mode refresh row into Supabase."""
    import json
    import urllib.request
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        print("[!] SUPABASE_URL / SUPABASE_SERVICE_KEY not set — cannot enqueue")
        return False
    payload = json.dumps({
        "site_domain": os.environ.get("SITE_DOMAIN", "patrolgarage.ae"),
        "slug": row["slug"],
        "keyword": row["slug"].replace("-", " "),
        "mode": "patch",
        "status": "queued",
        "queued_at": datetime.utcnow().isoformat(),
    }).encode()
    req = urllib.request.Request(
        f"{url}/rest/v1/article_refreshes", data=payload, method="POST",
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"})
    try:
        urllib.request.urlopen(req, timeout=30)
        print(f"[queued] {row['slug']} (mode=patch)")
        return True
    except Exception as e:
        print(f"[!] enqueue failed for {row['slug']}: {e}")
        return False


def main():
    show_all = "--show-all" in sys.argv
    do_enqueue = "--enqueue" in sys.argv

    rows = build_queue()
    due = [r for r in rows if r["due"]]

    print(f"posts: {len(rows)}   due: {len(due)}   cap: {DAILY_ENQUEUE_CAP}/day\n")
    by_tier = {}
    for r in rows:
        by_tier.setdefault(r["tier"], [0, 0])
        by_tier[r["tier"]][0] += 1
        by_tier[r["tier"]][1] += 1 if r["due"] else 0
    for t, (n, d) in sorted(by_tier.items()):
        cad = dict((name, days) for name, _, days in TIERS)[t]
        print(f"  {t}  {n:>2} posts, every {cad:>3}d  ->  {d} due")

    shown = rows if show_all else due[:12]
    print(f"\n{'slug':<58} tier  age  overdue  from")
    for r in shown:
        print(f"  {r['slug'][:56]:<58} {r['tier']}  {r['age']:>4}d  {r['overdue']:>+6}d  {r['src']}")
    if not show_all and len(due) > 12:
        print(f"  … and {len(due)-12} more due (use --show-all)")

    if not do_enqueue:
        print(f"\nDRY RUN — nothing enqueued. {len(due)} post(s) would eventually be "
              f"processed at {DAILY_ENQUEUE_CAP}/day (~{len(due)//max(1,DAILY_ENQUEUE_CAP)} days).")
        print("Run with --enqueue to queue the single most-overdue post in patch mode.")
        return 0

    for r in due[:DAILY_ENQUEUE_CAP]:
        enqueue(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
