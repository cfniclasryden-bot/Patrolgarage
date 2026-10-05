"""Logs pipeline events to Supabase. Called from run_pipeline.py.

Best-effort logging — failures here never break the pipeline.
"""
import os
import sys
import json
from datetime import datetime
from urllib import request, error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "")


def _enabled():
    return bool(SUPABASE_URL and SUPABASE_KEY and SITE_DOMAIN)


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _post(path, payload):
    req = request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get(path):
    req = request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers=_headers(),
        method="GET",
    )
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _site_id():
    rows = _get(f"sites?domain=eq.{SITE_DOMAIN}&select=id")
    if not rows:
        raise RuntimeError(f"Site {SITE_DOMAIN} not in Supabase sites table")
    return rows[0]["id"]


def log_article(keyword, slug, url, status="published", content_html=None, title=None):
    """Record a published article (upsert — update if exists, insert if not)."""
    if not _enabled():
        print("[supabase_log] disabled (missing env vars)")
        return
    try:
        row = {
            "site_id": _site_id(),
            "keyword": keyword,
            "slug": slug,
            "url": url,
            "status": status,
            "published_at": datetime.utcnow().isoformat() if status == "published" else None,
            "created_by_luni": True,
        }
        if content_html:
            row["content_html"] = content_html
        if title:
            row["title"] = title
        # Use upsert to handle articles that already exist as pending
        req = request.Request(
            f"{SUPABASE_URL}/rest/v1/articles?on_conflict=site_id,keyword",
            data=json.dumps(row).encode("utf-8"),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as resp:
            resp.read()
        print(f"[supabase_log] article logged: {slug}")
    except Exception as e:
        print(f"[supabase_log] article log failed (non-fatal): {e}", file=sys.stderr)


def log_run(keyword, status, error_message=None):
    """Record a pipeline run outcome."""
    if not _enabled():
        return
    try:
        _post("pipeline_runs", {
            "site_id": _site_id(),
            "keyword": keyword,
            "status": status,
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat(),
        })
        print(f"[supabase_log] run logged: {status}")
    except Exception as e:
        print(f"[supabase_log] run log failed (non-fatal): {e}", file=sys.stderr)

def sync_queue(rows):
    """Upsert keyword queue state. rows is a list of dicts with 'keyword' and 'status'."""
    if not _enabled():
        return
    try:
        site_id = _site_id()
        payload = [
            {
                "site_id": site_id,
                "keyword": r["keyword"],
                "slug": _slug(r["keyword"]),
                "status": r["status"],
                "published_at": (
                    datetime.utcnow().isoformat()
                    if r["status"] == "published" and r.get("date_published")
                    else None
                ),
            }
            for r in rows
        ]
        req = request.Request(
            f"{SUPABASE_URL}/rest/v1/articles?on_conflict=site_id,keyword",
            data=json.dumps(payload).encode("utf-8"),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
            method="POST",
        )
        with request.urlopen(req, timeout=15) as resp:
            resp.read()
        print(f"[supabase_log] queue synced ({len(rows)} keywords)")
    except Exception as e:
        print(f"[supabase_log] queue sync failed (non-fatal): {e}", file=sys.stderr)



def write_queue_mirror(published=None, csv_path=None):
    """Rewrite keywords.csv as a MIRROR of the Supabase queue. Returns row count.

    Added 2026-09-29. Supabase is the queue; this file only reflects it. Until
    then keywords.csv was both a mirror nobody updated and a filter the keyword
    generator trusted: every row stayed `pending` forever, published or not, and
    the generator refused any candidate already in the file. On topchallenger
    that left Supabase with 0 pending while the CSV listed 32 "pending" rows, and
    the 2026-09-28 run dropped four keywords that had passed every gate as
    "duplicates". The generator now dedupes against Supabase alone and nothing
    reads this file as input.

    `published` is the keyword OR slug of a post going out in this run. At commit
    time Supabase still says `pending` for it (run_pipeline marks it published
    after publish.py returns), so it is marked published here, dated today, and
    the file is committed with the post.

    Never raises into a publish: callers wrap it, and a failure leaves the
    previous file in place.
    """
    from pathlib import Path
    csv_path = Path(csv_path) if csv_path else Path(__file__).resolve().parent.parent / "keywords.csv"
    rows = _get(f"articles?site_id=eq.{_site_id()}"
                "&select=keyword,slug,status,published_at,created_at&order=created_at.asc")
    mark = (published or "").lower().strip()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out = []
    for a in rows:
        kw = (a.get("keyword") or "").strip()
        if not kw:
            continue
        status = a.get("status") or ""
        date = (a.get("published_at") or "")[:10]
        if mark and mark in (kw.lower(), (a.get("slug") or "").lower(), _slug(kw)):
            status, date = "published", date or today
        out.append({"keyword": kw, "status": status,
                    "date_published": date if status == "published" else ""})
    import csv
    tmp = csv_path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "status", "date_published"])
        w.writeheader()
        w.writerows(out)
    tmp.replace(csv_path)
    print(f"[supabase_log] keywords.csv mirrored from Supabase ({len(out)} rows"
          + (f", {published} marked published" if published else "") + ")")
    return len(out)

def _slug(text):
    import re
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")


# ---------------------------------------------------------------- stuck keywords
#
# Added 2026-10-05. A run that fails leaves its keyword `pending` at the head of
# the queue, so the next run picks the same keyword and usually fails the same
# way. That is what happened to topchallenger's "y62 service cost dubai": blocked
# by check_claims on 2026-10-02 and again on 2026-10-05, with the Wednesday run
# lined up to do it a third time. One keyword held the whole site.
#
# The streak is read from pipeline_runs, which already gets one row per run with
# the keyword and status, so no schema change was needed. A `requeued` row ends a
# streak, as a `success` does: a keyword moved to the back gets two fresh
# attempts when it comes round again, rather than being moved again on its
# first failure.

REQUEUE_AFTER = 2


def streak_from_runs(rows):
    """Consecutive `failed` runs at the head of `rows` (newest first).

    `success` and `requeued` end the streak. Any other status (the table also
    holds `started` rows written by other tooling) neither counts nor ends it.
    """
    n = 0
    for r in rows:
        status = r.get("status")
        if status == "failed":
            n += 1
        elif status in ("success", "requeued"):
            break
    return n


def failure_streak(keyword):
    """How many runs in a row have failed on `keyword`. None if unreadable."""
    if not _enabled():
        return None
    from urllib.parse import quote
    try:
        rows = _get(f"pipeline_runs?site_id=eq.{_site_id()}"
                    f"&keyword=eq.{quote(keyword, safe='')}"
                    "&select=status,started_at&order=started_at.desc&limit=20")
        return streak_from_runs(rows)
    except Exception as e:
        print(f"[supabase_log] failure streak unreadable (non-fatal): {e}", file=sys.stderr)
        return None


def requeue_to_back(article_id, keyword, reason):
    """Move a pending article to the back of the queue. True on success.

    The runner takes the oldest pending row by created_at, so "the back" is
    created_at = now. The reason goes in editorial_notes and in a `requeued`
    pipeline_runs row, which also ends the failure streak.
    """
    if not _enabled():
        return False
    from urllib.parse import quote
    try:
        req = request.Request(
            f"{SUPABASE_URL}/rest/v1/articles?id=eq.{quote(str(article_id), safe='')}"
            "&status=eq.pending",
            data=json.dumps({"created_at": datetime.utcnow().isoformat() + "Z",
                             "editorial_notes": reason}).encode("utf-8"),
            headers=_headers(),
            method="PATCH",
        )
        with request.urlopen(req, timeout=10) as resp:
            moved = json.loads(resp.read() or b"[]")
        if not moved:
            print(f"[supabase_log] requeue matched no pending row for {keyword!r}",
                  file=sys.stderr)
            return False
        log_run(keyword=keyword, status="requeued", error_message=reason)
        return True
    except Exception as e:
        print(f"[supabase_log] requeue failed (non-fatal): {e}", file=sys.stderr)
        return False
