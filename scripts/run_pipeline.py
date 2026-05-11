#!/usr/bin/env python3
"""Daily autonomous pipeline runner."""

import csv
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
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

    # Read keywords
    rows = []
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Find next pending
    pending = next((r for r in rows if r["status"] == "pending"), None)
    if not pending:
        log("No pending keywords. Pipeline idle.")
        return 0

    keyword = pending["keyword"]
    slug = slugify(keyword)
    log(f"Target keyword: {keyword}")
    log(f"Slug: {slug}")

    # Run pipeline stages
    stages = [
        (["python3", "scripts/research.py", keyword], f"research: {keyword}"),
        (["python3", "scripts/generate.py", slug], f"generate draft"),
        (["python3", "scripts/assemble.py", slug], f"assemble final HTML"),
        (["python3", "scripts/publish.py", slug], f"publish + sitemap + deploy"),
    ]

    for cmd, desc in stages:
        if not run(cmd, desc):
            log(f"=== PIPELINE FAILED at: {desc} ===")
            return 1

    # Mark keyword as published
    pending["status"] = "published"
    pending["date_published"] = datetime.now().strftime("%Y-%m-%d")
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "status", "date_published"])
        writer.writeheader()
        writer.writerows(rows)

    log(f"=== PIPELINE COMPLETE: {keyword} ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
