#!/usr/bin/env python3
"""assemble.py — wrap a draft HTML in the full Patrol Garage template"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

PROJECT_ROOT = Path(__file__).parent.parent
DRAFTS_DIR = PROJECT_ROOT / "drafts"
BLOG_DIR = PROJECT_ROOT / "blog"
TEMPLATE_FILE = BLOG_DIR / "nissan-patrol-y62-problems-dubai.html"

client = Anthropic()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def generate_meta(keyword, draft_html):
    """Use Claude to generate SEO meta from the keyword + draft."""
    body_text = re.sub(r"<[^>]+>", " ", draft_html)[:2000]
    prompt = f"""Generate SEO metadata for a Nissan Patrol blog post.

KEYWORD: {keyword}

ARTICLE EXCERPT:
{body_text}

Return ONLY valid JSON in this exact format (no markdown, no preamble):
{{
  "title": "60-char SEO title with keyword and year 2026, must end with '| Patrol Garage Dubai'",
  "description": "155-char meta description, action-oriented",
  "keywords": "5-8 comma-separated keywords",
  "og_title": "55-char OG title",
  "og_description": "120-char OG description",
  "tw_title": "55-char Twitter title",
  "tw_description": "100-char Twitter description",
  "schema_headline": "60-char article headline",
  "schema_description": "155-char article description",
  "hero_tag_1": "2-word hero tag (e.g. 'Y62 Issues')",
  "hero_tag_2": "1-word hero tag (e.g. 'Diagnosis')",
  "h1_short": "3-5 word headline for hero (e.g. 'Y62 Transmission Problems')",
  "wa_text": "URL-encoded WhatsApp message (e.g. 'My%20Y62%20has%20transmission%20issues')"
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_article_body(draft_html):
    """Get just the body content from the draft, excluding the CTA block."""
    html = draft_html.strip()
    # Remove the CTA div from the draft — template provides its own
    html = re.sub(r'<div class="cta">.*?</div>', "", html, flags=re.DOTALL)
    # Drop the H1 — template provides hero with H1
    html = re.sub(r"<h1>.*?</h1>", "", html, count=1, flags=re.DOTALL)
    return html.strip()


def assemble(keyword):
    slug = slugify(keyword)
    draft_path = DRAFTS_DIR / f"{slug}.html"

    if not draft_path.exists():
        print(f"[!] No draft at {draft_path}")
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print(f"[!] Template not found: {TEMPLATE_FILE}")
        sys.exit(1)

    print(f"[+] Assembling: {keyword}")
    print(f"    Generating SEO metadata...")

    with open(draft_path, encoding="utf-8") as f:
        draft_html = f.read()

    meta = generate_meta(keyword, draft_html)
    article_body = extract_article_body(draft_html)
    today = datetime.now().strftime("%Y-%m-%d")
    canonical_url = f"https://patrolgarage.ae/blog/{slug}.html"

    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        template = f.read()

    # --- Replace head metadata ---
    template = re.sub(r"<title>.*?</title>", f"<title>{meta['title']}</title>", template, count=1)
    template = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{meta["description"]}">', template, count=1)
    template = re.sub(r'<meta name="keywords" content=".*?">', f'<meta name="keywords" content="{meta["keywords"]}">', template, count=1)
    template = re.sub(r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{canonical_url}">', template, count=1)
    template = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{meta["og_title"]}">', template, count=1)
    template = re.sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{meta["og_description"]}">', template, count=1)
    template = re.sub(r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{canonical_url}">', template, count=1)
    template = re.sub(r'<meta name="twitter:title" content=".*?">', f'<meta name="twitter:title" content="{meta["tw_title"]}">', template, count=1)
    template = re.sub(r'<meta name="twitter:description" content=".*?">', f'<meta name="twitter:description" content="{meta["tw_description"]}">', template, count=1)

    # --- Replace JSON-LD schema ---
    new_schema = f'''<script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{meta["schema_headline"]}",
    "description": "{meta["schema_description"]}",
    "image": "https://patrolgarage.ae/images/og-blog-y62.jpg",
    "author": {{"@type": "Organization", "name": "Patrol Garage Dubai"}},
    "publisher": {{"@type": "Organization", "name": "Patrol Garage Dubai"}},
    "datePublished": "{today}",
    "dateModified": "{today}"
  }}
  </script>'''
    template = re.sub(r'<script type="application/ld\+json">.*?</script>', new_schema, template, count=1, flags=re.DOTALL)

    # --- Replace hero ---
    new_hero = f'''<div class="hero-meta"><span class="hero-meta-line"></span><span>{meta["hero_tag_1"]}</span><span>·</span><span>{meta["hero_tag_2"]}</span></div>
      <h1>{meta["h1_short"]}</h1>'''
    template = re.sub(r'<div class="hero-meta">.*?</h1>', new_hero, template, count=1, flags=re.DOTALL)

    # --- Replace article body ---
    new_article = f"<article>\n{article_body}\n    </article>"
    template = re.sub(r'<article>.*?</article>', new_article, template, count=1, flags=re.DOTALL)

    # --- Replace WhatsApp CTA text ---
    template = re.sub(
        r'href="https://wa\.me/971582211201\?text=[^"]*"',
        f'href="https://wa.me/971582211201?text={meta["wa_text"]}"',
        template,
        count=1,
    )

    out_path = BLOG_DIR / f"{slug}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"[+] Assembled blog post: {out_path}")
    print(f"    Title: {meta['title']}")
    print(f"    Open it: open {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 assemble.py \"your keyword here\"")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    assemble(keyword)
