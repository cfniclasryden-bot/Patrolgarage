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


def log_article(keyword, slug, url, status="published"):
    """Record a published article."""
    if not _enabled():
        print("[supabase_log] disabled (missing env vars)")
        return
    try:
        _post("articles", {
            "site_id": _site_id(),
            "keyword": keyword,
            "slug": slug,
            "url": url,
            "status": status,
            "published_at": datetime.utcnow().isoformat() if status == "published" else None,
        })
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


def _slug(text):
    import re
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")
