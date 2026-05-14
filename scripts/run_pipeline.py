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

def main():
    log(f"=== PIPELINE RUN START ===")

    rows = []
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Auto-replenish queue if running low
    pending_count = sum(1 for r in rows if r["status"] == "pending")
    if pending_count < 5:
        log(f"Queue low ({pending_count} pending). Auto-generating more keywords...")
        kw_result = subprocess.run(
            ["python3", "scripts/keyword_generator.py"],
            capture_output=True, text=True, cwd=ROOT
        )
        if kw_result.returncode == 0:
            log("  ✓ Keyword queue replenished")
            with open(CSV_FILE) as f:
                rows = list(csv.DictReader(f))
        else:
            log(f"  [!] Keyword generation failed: {kw_result.stderr[:300]}")

    # Sync current queue state to Supabase (before running, captures pending state)
    sync_queue(rows)

    pending = next((r for r in rows if r["status"] == "pending"), None)
    if not pending:
        log("No pending keywords. Pipeline idle.")
        return 0

    keyword = pending["keyword"]
    slug = slugify(keyword)
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

    pending["status"] = "published"
    pending["date_published"] = datetime.now().strftime("%Y-%m-%d")
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "status", "date_published"])
        writer.writeheader()
        writer.writerows(rows)

    # Sync the updated queue (now reflecting the just-published article)
    sync_queue(rows)

    site_domain = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")
    article_url = f"https://{site_domain}/blog/{slug}.html"
    log_article(keyword=keyword, slug=slug, url=article_url, status="published")
    log_run(keyword=keyword, status="success")

    log(f"=== PIPELINE COMPLETE: {keyword} ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
