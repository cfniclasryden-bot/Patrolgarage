#!/usr/bin/env python3
"""Regenerate blog/index.html journal grid from all blog posts."""

import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
BLOG = ROOT / "blog"
INDEX = BLOG / "index.html"

def extract_post_meta(html_path):
    """Pull title, description, category, date from a post."""
    html = html_path.read_text()

    # Title from <title> tag, strip suffix
    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1) if title_match else html_path.stem
    title = re.sub(r'\s*[\|\-]\s*Patrol Garage.*$', '', title).strip()

    # Description from meta
    desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
    description = desc_match.group(1) if desc_match else ""
    # Trim to ~140 chars at word boundary
    if len(description) > 140:
        description = description[:137].rsplit(" ", 1)[0] + "..."

    # Category from first eyebrow span or fallback by slug keywords
    eyebrow_match = re.search(r'<div class="hero-meta">.*?<span>([^<]+)</span>', html, re.DOTALL)
    if eyebrow_match:
        category = eyebrow_match.group(1).strip().upper()
        # Skip the "—" prefix span if present
        if not re.match(r'^[A-Z0-9]', category):
            spans = re.findall(r'<span[^>]*>([^<]+)</span>', eyebrow_match.group(0))
            for s in spans:
                if re.match(r'^[A-Z0-9]', s.strip()):
                    category = s.strip().upper()
                    break
    else:
        slug_lower = html_path.stem.lower()
        if "problem" in slug_lower or "issue" in slug_lower:
            category = "PROBLEMS"
        elif "cost" in slug_lower or "price" in slug_lower:
            category = "COSTS"
        elif "ac" in slug_lower:
            category = "CLIMATE"
        elif "suspension" in slug_lower or "upgrade" in slug_lower:
            category = "UPGRADES"
        elif "service" in slug_lower or "maintenance" in slug_lower or "oil" in slug_lower:
            category = "MAINTENANCE"
        elif "vs" in slug_lower or "compari" in slug_lower:
            category = "COMPARISON"
        elif "guide" in slug_lower:
            category = "GUIDE"
        elif "mechanic" in slug_lower or "workshop" in slug_lower:
            category = "WORKSHOPS"
        elif "off-road" in slug_lower or "offroad" in slug_lower:
            category = "OFF-ROAD"
        elif "inspection" in slug_lower:
            category = "INSPECTION"
        else:
            category = "GUIDE"

    # Date from file mtime
    mtime = datetime.fromtimestamp(html_path.stat().st_mtime)
    date_str = mtime.strftime("%m/%Y")

    # Word count for read time
    text_only = re.sub(r'<[^>]+>', ' ', html)
    word_count = len(text_only.split())
    read_min = max(3, word_count // 250)

    return {
        "slug": html_path.stem,
        "title": title,
        "description": description,
        "category": category,
        "date": date_str,
        "mtime": mtime,
        "read_min": read_min,
    }

def build_card(meta):
    return f'''        <article class="journal-card">
          <div class="journal-meta">
            <span>{meta["category"]}</span>
            <span>{meta["date"]}</span>
          </div>
          <h3><a href="{meta["slug"]}.html">{meta["title"]}</a></h3>
          <p class="journal-excerpt">{meta["description"]}</p>
          <a href="{meta["slug"]}.html" class="journal-read">
            Read · {meta["read_min"]} min
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
          </a>
        </article>'''

def main():
    # Collect all posts (skip index.html itself)
    posts = []
    for f in BLOG.glob("*.html"):
        if f.name == "index.html":
            continue
        posts.append(extract_post_meta(f))

    # Sort newest first
    posts.sort(key=lambda p: p["mtime"], reverse=True)
    print(f"[i] Found {len(posts)} posts")

    # Build new grid HTML
    cards_html = "\n".join(build_card(p) for p in posts)
    new_grid = f'      <div class="journal-grid">\n{cards_html}\n      </div>'

    # Replace grid in index.html
    index_html = INDEX.read_text()
    new_html = re.sub(
        r'      <div class="journal-grid">.*?      </div>',
        new_grid,
        index_html,
        count=1,
        flags=re.DOTALL,
    )

    if new_html == index_html:
        print("[!] Failed to replace journal-grid block")
        return 1

    INDEX.write_text(new_html)
    print(f"[OK] blog/index.html rebuilt with {len(posts)} cards")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
