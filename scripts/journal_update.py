#!/usr/bin/env python3
"""Regenerate the paginated blog journal from all blog posts.

Page 1 -> blog/index.html
Page N -> blog/page/{N}/index.html   (N >= 2)

Run on every publish from publish.py, so new posts flow into pagination and the
page count grows on its own. Card markup reproduces exactly what production
serves: single-quoted, root-absolute, extensionless /blog/{slug} links.

Env:
  POSTS_PER_PAGE   posts per listing page (default 24)
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
BLOG = ROOT / "blog"
INDEX = BLOG / "index.html"
PAGE_DIR = BLOG / "page"
SITE = "https://patrolgarage.ae"

PER_PAGE = int(os.environ.get("POSTS_PER_PAGE", 24))

# The grid block journal cards live in. 6-space indent, matches blog/index.html.
GRID_RE = r'      <div class="journal-grid">.*?\n      </div>'
# Pagination nav we inject after the grid (so re-runs replace, never stack).
NAV_RE = r'\n      <nav class="pagination".*?</nav>'

PAGINATION_CSS = """
    /* Pagination */
    .pagination {
      display: flex; flex-wrap: wrap; gap: 0.5rem;
      justify-content: center; align-items: center;
      padding: 2.5rem 1rem;
      border-top: 1px solid var(--line);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase;
    }
    .pagination a, .pagination span {
      display: inline-block; min-width: 2.4rem; text-align: center;
      padding: 0.65rem 0.9rem;
      border: 1px solid var(--line);
      color: var(--text-2); text-decoration: none;
      transition: background 0.25s, color 0.25s;
    }
    .pagination a:hover { background: var(--bg-1); color: var(--text-1); }
    .pagination [aria-current="page"] {
      color: var(--text-1); border-color: var(--text-1); font-weight: 600;
    }
"""


def page_url(n):
    """Canonical URL path for listing page n. Page 1 is /blog/, never /blog/page/1/."""
    return "/blog/" if n == 1 else f"/blog/page/{n}/"


def extract_post_meta(html_path):
    """Pull title, description, category, date from a post."""
    html = html_path.read_text()

    title_match = re.search(r"<title>([^<]+)</title>", html)
    title = title_match.group(1) if title_match else html_path.stem
    title = re.sub(r"\s*[\|\-]\s*Patrol Garage.*$", "", title).strip()

    desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
    description = desc_match.group(1) if desc_match else ""
    if len(description) > 140:
        description = description[:137].rsplit(" ", 1)[0] + "..."

    eyebrow_match = re.search(r'<div class="hero-meta">.*?<span>([^<]+)</span>', html, re.DOTALL)
    if eyebrow_match:
        category = eyebrow_match.group(1).strip().upper()
        if not re.match(r"^[A-Z0-9]", category):
            spans = re.findall(r"<span[^>]*>([^<]+)</span>", eyebrow_match.group(0))
            for s in spans:
                if re.match(r"^[A-Z0-9]", s.strip()):
                    category = s.strip().upper()
                    break
    else:
        sl = html_path.stem.lower()
        if "problem" in sl or "issue" in sl:
            category = "PROBLEMS"
        elif "cost" in sl or "price" in sl:
            category = "COSTS"
        # Word-boundary, not substring: bare `"ac" in sl` also matched the "ac"
        # inside "accumulator" and "replacement", so an hbmc-accumulator or any
        # replacement post with no "cost" in its slug was filed as CLIMATE.
        elif re.search(r"\bac\b", sl):
            category = "CLIMATE"
        # Suspension work here is REPAIR — shocks, HBMC accumulators, bushes.
        # The workshop does not do lift kits or height modification, so this
        # must not label a suspension post "UPGRADES" (owner decision
        # 2026-08-13). "upgrade" is deliberately NOT a trigger any more: the
        # slugs that carry it are informational cost posts (y62-turbo-upgrade-
        # dubai-cost, y62-intercooler-upgrade-cost-...), and they already match
        # the "cost" branch above, so routing them here only ever mislabelled
        # them as something the workshop sells.
        elif "suspension" in sl or "hbmc" in sl or "air-bag" in sl:
            category = "SUSPENSION"
        elif "service" in sl or "maintenance" in sl or "oil" in sl:
            category = "MAINTENANCE"
        elif "vs" in sl or "compari" in sl:
            category = "COMPARISON"
        elif "guide" in sl:
            category = "GUIDE"
        elif "mechanic" in sl or "workshop" in sl:
            category = "WORKSHOPS"
        elif "off-road" in sl or "offroad" in sl:
            category = "OFF-ROAD"
        elif "inspection" in sl:
            category = "INSPECTION"
        else:
            category = "GUIDE"

    mtime = datetime.fromtimestamp(html_path.stat().st_mtime)
    text_only = re.sub(r"<[^>]+>", " ", html)
    read_min = max(3, len(text_only.split()) // 250)

    return {
        "slug": html_path.stem,
        "title": title,
        "description": description,
        "category": category,
        "date": mtime.strftime("%B %d, %Y"),
        "mtime": mtime,
        "read_min": read_min,
    }


def build_card(meta):
    """Verbatim production card markup — single-quoted, root-absolute, .html.

    The .html form is deliberate. These cards used to emit extensionless
    /blog/<slug>, while canonical, og:url, schema, sitemap and every in-body
    link emitted /blog/<slug>.html. Netlify serves both with a 200, so Google
    indexed both and split impressions across 13 posts — the cards were the
    single source of the split. Everything now agrees on .html; the clean form
    301s to it (see _redirects).
    """
    return f'''        <article class="journal-card">
          <div class="journal-meta">
            <span>{meta["category"]}</span>
            <span>{meta["date"]}</span>
          </div>
          <h3><a href='/blog/{meta["slug"]}.html'>{meta["title"]}</a></h3>
          <p class="journal-excerpt">{meta["description"]}</p>
          <a class='journal-read' href='/blog/{meta["slug"]}.html'>
            Read · {meta["read_min"]} min
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
          </a>
        </article>'''


def build_nav(current, total):
    """Real crawlable <a href> pagination. Omits dead prev/next at the ends."""
    if total < 2:
        return ""
    parts = ['\n      <nav class="pagination" aria-label="Blog pages">']
    if current > 1:
        parts.append(f'        <a href="{page_url(current - 1)}" rel="prev">&larr; Prev</a>')
    for n in range(1, total + 1):
        if n == current:
            parts.append(f'        <span aria-current="page">{n}</span>')
        else:
            parts.append(f'        <a href="{page_url(n)}">{n}</a>')
    if current < total:
        parts.append(f'        <a href="{page_url(current + 1)}" rel="next">Next &rarr;</a>')
    parts.append("      </nav>")
    return "\n".join(parts)


def apply_head(html, current, total):
    """Self-referencing canonical + og:url + differentiated title + rel prev/next."""
    url = f"{SITE}{page_url(current)}"

    html = re.sub(r'(<link rel="canonical" href=")[^"]*(")', rf"\g<1>{url}\g<2>", html, count=1)
    html = re.sub(r'(<meta property="og:url" content=")[^"]*(")', rf"\g<1>{url}\g<2>", html, count=1)

    # Strip any prev/next from a previous run, then re-add for this page.
    html = re.sub(r'\n\s*<link rel="(?:prev|next)" href="[^"]*">', "", html)
    seq = ""
    if current > 1:
        seq += f'\n  <link rel="prev" href="{SITE}{page_url(current - 1)}">'
    if current < total:
        seq += f'\n  <link rel="next" href="{SITE}{page_url(current + 1)}">'
    if seq:
        html = re.sub(r'(<link rel="canonical" href="[^"]*">)', rf"\g<1>{seq}", html, count=1)

    if current > 1:
        html = re.sub(
            r"<title>([^<]*?)(?:\s*\|\s*Page \d+)?</title>",
            rf"<title>\g<1> | Page {current}</title>",
            html, count=1,
        )
    else:
        html = re.sub(r"<title>([^<]*?)\s*\|\s*Page \d+</title>", r"<title>\g<1></title>", html, count=1)
    return html


def fix_relative(html):
    """Sub-pages sit two levels deeper, so relative URLs must become root-absolute."""
    html = html.replace("../images/", "/images/")
    html = re.sub(r"(href=)(['\"])\./\2", r"\g<1>\g<2>/blog/\g<2>", html)
    return html


def ensure_css(html):
    if ".pagination {" in html:
        return html
    return html.replace("</style>", PAGINATION_CSS + "  </style>", 1)


def clean_stale_pages(keep_total):
    """Remove page dirs beyond the current count so an orphaned page can't linger.
    Scoped strictly to blog/page/<n>/ — never touches posts."""
    if not PAGE_DIR.exists():
        return
    for d in PAGE_DIR.iterdir():
        if d.is_dir() and d.name.isdigit() and int(d.name) > keep_total:
            shutil.rmtree(d)
            print(f"[-] removed stale {d.relative_to(ROOT)}")


def main():
    posts = [extract_post_meta(f) for f in BLOG.glob("*.html") if f.name != "index.html"]
    posts.sort(key=lambda p: p["mtime"], reverse=True)
    if not posts:
        print("[!] No posts found")
        return 1

    pages = [posts[i:i + PER_PAGE] for i in range(0, len(posts), PER_PAGE)]
    total = len(pages)
    print(f"[i] {len(posts)} posts -> {total} page(s) at {PER_PAGE}/page")

    template = INDEX.read_text()
    if not re.search(GRID_RE, template, re.DOTALL):
        print("[!] Could not find journal-grid block in index.html")
        return 1
    template = re.sub(NAV_RE, "", template, flags=re.DOTALL)  # drop old nav before reuse

    for i, chunk in enumerate(pages, start=1):
        grid = '      <div class="journal-grid">\n' + "\n".join(build_card(p) for p in chunk) + "\n      </div>"
        html = re.sub(GRID_RE, lambda _m: grid + build_nav(i, total), template, count=1, flags=re.DOTALL)
        html = apply_head(html, i, total)
        html = ensure_css(html)

        if i == 1:
            INDEX.write_text(html)
            out = INDEX
        else:
            html = fix_relative(html)
            d = PAGE_DIR / str(i)
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(html)
            out = d / "index.html"
        print(f"[OK] {out.relative_to(ROOT)} — {len(chunk)} cards, page {i}/{total}")

    clean_stale_pages(total)
    print(f"[OK] journal rebuilt: {len(posts)} posts across {total} page(s)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
