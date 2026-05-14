#!/usr/bin/env python3
"""Auto-generate BOFU keywords for the queue."""

import csv
import sys
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
CSV_FILE = ROOT / "keywords.csv"

client = Anthropic()

def load_existing():
    if not CSV_FILE.exists():
        return [], []
    rows = list(csv.DictReader(open(CSV_FILE)))
    existing = [r["keyword"].lower() for r in rows]
    return rows, existing

def generate_keywords(existing_count, existing_sample):
    sample = "\n".join(existing_sample[-15:]) if existing_sample else "(none yet)"
    prompt = f"""Generate 10 new BOFU (bottom-of-funnel) SEO keywords for a Nissan Patrol specialist website in Dubai.

CONTEXT:
- Site: patrolgarage.ae (Nissan Patrol specialist - Y61, Y62, Y63)
- Location: Dubai, UAE
- Audience: Patrol owners searching for service, repair, comparisons, pricing
- Already published or queued: {existing_count} keywords. Recent examples:
{sample}

REQUIREMENTS for new keywords:
- BOFU intent: comparisons, costs, "best", "vs", "near me", brand pricing, alternatives
- Dubai/UAE specific where natural
- Mix of Y61, Y62, Y63 topics
- Include some "Al Futtaim alternative", workshop comparisons, parts pricing
- Avoid TOFU informational queries (no "what is", "how does")
- Each keyword 4-10 words, lowercase, no punctuation
- DO NOT repeat existing keywords

OUTPUT: Return ONLY the 10 keywords, one per line, no numbering, no explanations."""

    print(f"[*] Asking Claude for 10 new BOFU keywords (avoiding {existing_count} existing)...")
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip()
    keywords = [line.strip().lower() for line in raw.split("\n") if line.strip()]
    keywords = [k for k in keywords if 4 <= len(k.split()) <= 12]
    return keywords

def main():
    rows, existing = load_existing()
    new_keywords = generate_keywords(len(rows), existing)

    # Dedupe against existing
    unique_new = [k for k in new_keywords if k not in existing]
    duplicates = len(new_keywords) - len(unique_new)

    if not unique_new:
        print("[!] All generated keywords were duplicates. Try again.")
        return 1

    for k in unique_new:
        rows.append({"keyword": k, "status": "pending", "date_published": ""})

    with open(CSV_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "status", "date_published"])
        w.writeheader()
        w.writerows(rows)

    print(f"[+] Added {len(unique_new)} new keywords ({duplicates} duplicates filtered)")
    print(f"[i] Queue now has {sum(1 for r in rows if r['status']=='pending')} pending keywords")
    for k in unique_new:
        print(f"    - {k}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
