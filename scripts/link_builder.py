#!/usr/bin/env python3
"""link_builder.py — add Related Reading sections to all existing blog posts"""

import re
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"


def get_all_posts():
    posts = []
    for f in BLOG_DIR.glob("*.html"):
        if f.name == "index.html":
            continue
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        h1_match = re.search(r"<h1>(.*?)</h1>", content)
        title_match = re.search(r"<title>(.*?)</title>", content)
        if h1_match:
            posts.append({
                "slug": f.stem,
                "path": f,
                "h1": h1_match.group(1).strip(),
                "title": title_match.group(1).split("|")[0].strip() if title_match else "",
                "content": content
            })
    return posts


def inject_related_reading(post, all_posts, max_links=3):
    """Add Related Reading section before the CTA banner."""
    others = [p for p in all_posts if p["slug"] != post["slug"]]
    if len(others) <= max_links:
        related = others
    else:
        related = random.sample(others, max_links)

    if not related:
        return False

    links_html = '\n      <div class="related-reading">\n        <h3>Related reading</h3>\n        <ul>\n'
    for r in related:
        links_html += f'          <li><a href="/blog/{r["slug"]}.html">{r["h1"]}</a></li>\n'
    links_html += "        </ul>\n      </div>\n    "

    content = post["content"]

    # Remove existing related-reading if present (so we can re-run safely)
    content = re.sub(
        r'\s*<div class="related-reading">.*?</div>\s*',
        "\n    ",
        content,
        flags=re.DOTALL
    )

    # Inject before </article>
    if "</article>" in content:
        content = content.replace("</article>", links_html + "</article>", 1)
        with open(post["path"], "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    posts = get_all_posts()
    print(f"[+] Found {len(posts)} blog posts")

    updated = 0
    for post in posts:
        if inject_related_reading(post, posts, max_links=3):
            print(f"    ✓ Added internal links to: {post['slug']}")
            updated += 1
        else:
            print(f"    ✗ Skipped: {post['slug']}")

    print(f"\n[+] Updated {updated}/{len(posts)} posts with internal links")


if __name__ == "__main__":
    main()
