#!/usr/bin/env python3
"""Auto-generate BOFU keywords for the queue and insert them into Supabase."""

import csv
import os
import re
import sys
from pathlib import Path

import requests
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
CSV_FILE = ROOT / "keywords.csv"

client = Anthropic()


# Verbatim from run_pipeline.py — do not change
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def load_existing():
    if not CSV_FILE.exists():
        return [], []
    rows = list(csv.DictReader(open(CSV_FILE)))
    existing = [r["keyword"].lower() for r in rows]
    return rows, existing


def fetch_site_data():
    """Fetch site_id and ALL existing articles before generation.
    Returns (supabase_url, headers, site_id, existing_articles, existing_keywords, existing_slugs).
    Raises RuntimeError on any failure."""
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    site_domain = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")

    if not supabase_url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    r = requests.get(
        f"{supabase_url}/rest/v1/sites",
        headers=headers,
        params={"domain": f"eq.{site_domain}", "select": "id"},
    )
    if not r.ok:
        raise RuntimeError(f"Site lookup failed ({r.status_code}): {r.text[:300]}")
    site_rows = r.json()
    if not site_rows:
        raise RuntimeError(f"Site '{site_domain}' not found in Supabase")
    site_id = site_rows[0]["id"]

    r = requests.get(
        f"{supabase_url}/rest/v1/articles",
        headers=headers,
        params={"site_id": f"eq.{site_id}", "select": "keyword,title,slug"},
    )
    if not r.ok:
        raise RuntimeError(f"Existing-articles fetch failed ({r.status_code}): {r.text[:300]}")
    existing_articles = r.json()

    existing_keywords = {a["keyword"].lower().strip() for a in existing_articles}
    existing_slugs = {a["slug"].lower().strip() for a in existing_articles if a.get("slug")}

    return supabase_url, headers, site_id, existing_articles, existing_keywords, existing_slugs


def generate_keywords(existing_articles):
    """Generate new BOFU keywords, fed the full list of existing article titles."""
    # Use title if present (richer signal), fall back to keyword for pending rows
    titles_list = []
    for a in existing_articles:
        label = (a.get("title") or a.get("keyword") or "").strip()
        if label:
            titles_list.append(label)

    titles_block = "\n".join(f"- {t}" for t in titles_list) if titles_list else "(none yet)"

    prompt = f"""Generate 10 new BOFU (bottom-of-funnel) SEO keywords for a Nissan Patrol specialist website in Dubai.

CONTEXT:
- Site: patrolgarage.ae (Nissan Patrol specialist - Y62)
- Location: Dubai, UAE
- Audience: Patrol owners searching for service, repair, comparisons, pricing

EXISTING ARTICLES (do not duplicate these topics):
{titles_block}

CRITICAL: Avoid any keyword that covers a topic ALREADY in the list above. Treat these as the SAME topic (synonyms):
- gearbox = transmission
- service = maintenance = servicing
- cost = price = pricing
- problems = issues = faults
- repair = fix
So if an article about 'transmission rebuild cost' exists, do NOT generate 'gearbox repair cost' — it's the same topic. Only propose keywords on genuinely NEW topics or angles not covered above.

REQUIREMENTS for new keywords:
- BOFU intent: comparisons, costs, "best", "vs", "near me", brand pricing, alternatives
- Dubai/UAE specific where natural
- Focus on Y62 topics
- Include some "Al Futtaim alternative", workshop comparisons, parts pricing
- Avoid TOFU informational queries (no "what is", "how does")
- Each keyword 4-10 words, lowercase, no punctuation

OUTPUT: Return ONLY the 10 keywords, one per line, no numbering, no explanations."""

    print(f"[*] Asking Claude for 10 new BOFU keywords (avoiding {len(titles_list)} existing topics)...")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip()
    keywords = [line.strip().lower() for line in raw.split("\n") if line.strip()]
    keywords = [k for k in keywords if 4 <= len(k.split()) <= 12]
    return keywords


def sync_to_supabase(unique_new, supabase_url, headers, site_id, existing_keywords, existing_slugs):
    """Insert new keywords using pre-fetched Supabase data — no re-queries.
    Returns count of rows actually inserted."""
    inserted = 0
    for kw in unique_new:
        kw_lower = kw.lower().strip()
        if kw_lower in existing_keywords:
            print(f"    [skip] already in DB: {kw}")
            continue

        slug = slugify(kw)
        if slug in existing_slugs:
            print(f"    [skip] slug collision ({slug}): {kw}")
            continue

        r = requests.post(
            f"{supabase_url}/rest/v1/articles",
            headers=headers,
            json={
                "site_id": site_id,
                "keyword": kw,
                "slug": slug,
                "status": "pending",
                "created_by_luni": True,
            },
        )
        if not r.ok:
            print(f"    [!] Insert failed for '{kw}' ({r.status_code}): {r.text[:200]}")
        else:
            existing_slugs.add(slug)
            inserted += 1

    return inserted


def main():
    rows, csv_existing = load_existing()

    # Fetch Supabase state BEFORE generating so the prompt has full topic context
    try:
        supabase_url, headers, site_id, existing_articles, existing_keywords, existing_slugs = fetch_site_data()
    except RuntimeError as e:
        print(f"[!] Supabase fetch failed: {e}")
        return 1

    new_keywords = generate_keywords(existing_articles)

    # Dedup against DB (authoritative) union CSV — reject exact-string matches
    all_existing_lower = existing_keywords | {k.lower() for k in csv_existing}
    unique_new = [k for k in new_keywords if k.lower().strip() not in all_existing_lower]
    duplicates = len(new_keywords) - len(unique_new)

    if not unique_new:
        print("All generated keywords were topic-duplicates — queue not grown. "
              "Site topic coverage may be saturated; consider adding keywords manually.")
        return 0

    # Write survivors to CSV
    for k in unique_new:
        rows.append({"keyword": k, "status": "pending", "date_published": ""})

    with open(CSV_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["keyword", "status", "date_published"])
        w.writeheader()
        w.writerows(rows)

    print(f"[+] CSV: added {len(unique_new)} keywords ({duplicates} exact-string duplicates filtered)")
    for k in unique_new:
        print(f"    - {k}")

    # Sync to Supabase using pre-fetched data
    inserted = sync_to_supabase(
        unique_new, supabase_url, headers, site_id, existing_keywords, existing_slugs
    )

    if inserted == 0:
        print("⚠  Replenishment generated keywords but inserted 0 new pending rows "
              "(all duplicates or slug collisions)")
    else:
        print(f"✓  Keyword queue replenished ({inserted} new pending articles inserted into Supabase)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
