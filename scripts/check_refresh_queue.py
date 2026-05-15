#!/usr/bin/env python3
"""
Queue checker: polls article_refreshes for queued items belonging to this site,
runs the refresh pipeline for each one, updates row status.

Runs frequently via Railway cron (every 5 min).
"""
import os
import sys
import requests
import subprocess
from pathlib import Path
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")

if not (SUPABASE_URL and SUPABASE_KEY):
    print("[check_refresh_queue] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(0)

H = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def log(msg):
    print(f"[check_refresh_queue] {datetime.utcnow().isoformat()} {msg}", flush=True)

def get_site_id():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/sites",
        headers=H,
        params={"domain": f"eq.{SITE_DOMAIN}", "select": "id"},
    )
    rows = r.json()
    if not rows:
        log(f"FATAL: site {SITE_DOMAIN} not in sites table")
        sys.exit(1)
    return rows[0]["id"]

def fetch_queued(site_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/article_refreshes",
        headers=H,
        params={
            "site_id": f"eq.{site_id}",
            "status": "eq.queued",
            "select": "id,article_id,requested_at",
            "order": "requested_at.asc",
        },
    )
    return r.json()

def fetch_article(article_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/articles",
        headers=H,
        params={"id": f"eq.{article_id}", "select": "*"},
    )
    rows = r.json()
    return rows[0] if rows else None

def update_refresh(refresh_id, **fields):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/article_refreshes",
        headers=H,
        params={"id": f"eq.{refresh_id}"},
        json=fields,
    )

def update_article(article_id, **fields):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/articles",
        headers=H,
        params={"id": f"eq.{article_id}"},
        json=fields,
    )

def process_refresh(refresh, article):
    refresh_id = refresh["id"]
    article_id = article["id"]
    keyword = article.get("keyword")
    slug = article.get("slug")

    log(f"Processing refresh {refresh_id[:8]}: {keyword}")

    update_refresh(refresh_id, status="running", started_at=datetime.utcnow().isoformat())
    update_article(article_id, refresh_status="running", refresh_started_at=datetime.utcnow().isoformat())

    try:
        # Run the existing pipeline in refresh mode
        # The existing run_pipeline.py picks the next pending keyword from CSV.
        # For refresh, we want to regenerate THIS specific keyword/slug.
        # Use a new script we'll create, or invoke run_pipeline.py with --refresh flag.
        result = subprocess.run(
            ["python3", "scripts/run_pipeline.py", "--refresh", keyword, slug],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min max
        )

        if result.returncode != 0:
            err = (result.stderr or result.stdout or "unknown error")[-500:]
            log(f"FAILED: {err}")
            update_refresh(refresh_id, status="failed", completed_at=datetime.utcnow().isoformat(), error=err)
            update_article(article_id, refresh_status="failed")
            return

        log(f"Success: {keyword}")
        update_refresh(refresh_id, status="success", completed_at=datetime.utcnow().isoformat())
        update_article(
            article_id,
            refresh_status="success",
            refresh_completed_at=datetime.utcnow().isoformat(),
            last_refreshed_at=datetime.utcnow().isoformat(),
            refresh_count=(article.get("refresh_count") or 0) + 1,
        )
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT on {keyword}")
        update_refresh(refresh_id, status="failed", completed_at=datetime.utcnow().isoformat(), error="timeout (30min)")
        update_article(article_id, refresh_status="failed")
    except Exception as e:
        log(f"EXCEPTION: {e}")
        update_refresh(refresh_id, status="failed", completed_at=datetime.utcnow().isoformat(), error=str(e)[:500])
        update_article(article_id, refresh_status="failed")

def main():
    site_id = get_site_id()
    queued = fetch_queued(site_id)

    if not queued:
        log(f"No queued refreshes for {SITE_DOMAIN}")
        return 0

    log(f"Found {len(queued)} queued refresh(es)")

    for refresh in queued:
        article = fetch_article(refresh["article_id"])
        if not article:
            log(f"Article {refresh['article_id']} not found, marking failed")
            update_refresh(refresh["id"], status="failed", error="article not found", completed_at=datetime.utcnow().isoformat())
            continue
        process_refresh(refresh, article)

    return 0

if __name__ == "__main__":
    sys.exit(main())
