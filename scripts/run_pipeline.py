#!/usr/bin/env python3
"""Daily autonomous pipeline runner."""

import csv
import subprocess
import sys
import re
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from supabase_log import log_article, log_run, sync_queue

CSV_FILE = ROOT / "keywords.csv"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
log_file = LOG_DIR / f"run_{today}.log"

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def run(cmd, desc):
    log(f"→ {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        log(f"[!] FAILED: {desc}")
        log(f"    stderr: {result.stderr[:500]}")
        return False
    log(f"  ✓ {desc} done")
    return True

def run_refresh_mode(keyword, slug):
    """Re-run pipeline stages for an existing article. Same slug, fresh content."""
    log(f"=== REFRESH MODE: {keyword} ({slug}) ===")

    stages = [
        (["python3", "scripts/research.py", keyword], f"research: {keyword}"),
        (["python3", "scripts/generate.py", slug], f"regenerate draft"),
        (["python3", "scripts/assemble.py", slug], f"assemble final HTML"),
        (["python3", "scripts/image_gen.py", slug], f"regenerate hero image"),
        (["python3", "scripts/publish.py", slug], f"publish + sitemap + deploy"),
    ]

    for cmd, desc in stages:
        if not run(cmd, desc):
            log(f"=== REFRESH FAILED at: {desc} ===")
            return 1

    # Read updated HTML and push to Supabase
    try:
        article_path = ROOT / "blog" / f"{slug}.html"
        if article_path.exists():
            content_html = article_path.read_text()
            title_match = re.search(r"<title>(.*?)</title>", content_html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else None

            # Update the article row with new content
            import requests
            SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
            SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
            if SUPABASE_URL and SUPABASE_KEY:
                H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/articles",
                    headers=H,
                    params={"slug": f"eq.{slug}"},
                    json={"content_html": content_html, "title": title},
                )
                log(f"Updated content_html in Supabase for {slug}")
    except Exception as e:
        log(f"[warn] content_html upload failed: {e}")

    log(f"=== REFRESH COMPLETE: {keyword} ===")
    return 0


def main():
    # Check for refresh mode
    if len(sys.argv) >= 4 and sys.argv[1] == "--refresh":
        return run_refresh_mode(sys.argv[2], sys.argv[3])

    log(f"=== PIPELINE RUN START ===")

    # Get next pending keyword from Supabase (source of truth)
    import requests as _req
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")

    if not (SUPABASE_URL and SUPABASE_KEY):
        log("FATAL: missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1

    SH = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

    # Get site_id from domain
    r = _req.get(f"{SUPABASE_URL}/rest/v1/sites", headers=SH,
                 params={"domain": f"eq.{SITE_DOMAIN}", "select": "id"})
    site_rows = r.json()
    if not site_rows:
        log(f"FATAL: site {SITE_DOMAIN} not found in sites table")
        return 1
    site_id = site_rows[0]["id"]

    # Auto-replenish queue if running low (still uses CSV for keyword generation source)
    r = _req.get(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
                 params={"site_id": f"eq.{site_id}", "status": "eq.pending", "select": "id"})
    pending_count = len(r.json())
    log(f"Pending in queue: {pending_count}")

    if pending_count < 5:
        log(f"Queue low. Auto-generating more keywords...")
        kw_result = subprocess.run(
            ["python3", "scripts/keyword_generator.py"],
            capture_output=True, text=True, cwd=ROOT
        )
        if kw_result.returncode == 0:
            log("  ✓ Keyword queue replenished")
        else:
            log(f"  [!] Keyword generation failed: {kw_result.stderr[:300]}")

    # Fetch the oldest pending article from Supabase
    r = _req.get(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
                 params={"site_id": f"eq.{site_id}", "status": "eq.pending",
                         "select": "id,keyword,slug", "order": "created_at.asc", "limit": "1"})
    pending_articles = r.json()
    if not pending_articles:
        log("No pending keywords. Pipeline idle.")
        return 0

    article_row = pending_articles[0]
    keyword = article_row["keyword"]
    slug = article_row.get("slug") or slugify(keyword)
    article_id = article_row["id"]
    log(f"Target keyword: {keyword}")
    log(f"Slug: {slug}")
    log(f"Article ID: {article_id}")
    log(f"Target keyword: {keyword}")
    log(f"Slug: {slug}")

    stages = [
        (["python3", "scripts/research.py", keyword], f"research: {keyword}"),
        (["python3", "scripts/generate.py", slug], f"generate draft"),
        (["python3", "scripts/assemble.py", slug], f"assemble final HTML"),
        (["python3", "scripts/image_gen.py", slug], f"generate hero image"),
        (["python3", "scripts/publish.py", slug], f"publish + sitemap + deploy"),
    ]

    for cmd, desc in stages:
        if not run(cmd, desc):
            log(f"=== PIPELINE FAILED at: {desc} ===")
            log_run(keyword=keyword, status="failed", error_message=f"Failed at: {desc}")
            return 1

    # Mark this article as published in Supabase (source of truth)
    _req.patch(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
               params={"id": f"eq.{article_id}"},
               json={"status": "published",
                     "published_at": datetime.utcnow().isoformat() + "Z",
                     "slug": slug})
    log(f"Article marked published in Supabase: {article_id}")

    site_domain = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")
    article_url = f"https://{site_domain}/blog/{slug}.html"

    # Read published HTML to upload to Supabase (non-fatal if it fails)
    content_html = None
    title = None
    try:
        import re
        article_path = Path(__file__).resolve().parent.parent / "blog" / f"{slug}.html"
        if article_path.exists():
            content_html = article_path.read_text()
            title_match = re.search(r"<title>(.*?)</title>", content_html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
    except Exception as e:
        log(f"[warn] could not read published HTML for upload: {e}")

    log_article(keyword=keyword, slug=slug, url=article_url, status="published",
                content_html=content_html, title=title)
    log_run(keyword=keyword, status="success")

    log(f"=== PIPELINE COMPLETE: {keyword} ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
