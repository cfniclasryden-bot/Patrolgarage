#!/usr/bin/env python3
"""assemble.py — wrap draft in template with schema, internal links, AIO optimizations"""

import sys
import re
import json
import random
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
    body_text = re.sub(r"<[^>]+>", " ", draft_html)[:2000]
    prompt = f"""Generate SEO metadata for a Nissan Patrol blog post.

KEYWORD: {keyword}
ARTICLE EXCERPT:
{body_text}

Return ONLY valid JSON (no markdown, no preamble):
{{
  "title": "60-char SEO title with keyword and year 2026, ending with '| Patrol Garage Dubai'",
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
  "h1_short": "3-5 word hero headline",
  "wa_text": "URL-encoded WhatsApp message"
}}"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_faqs(draft_html):
    """Pull FAQ Q&A pairs for FAQPage schema.
    Handles two layouts:
      A) Each Q&A in its own <div class="faq"><h3>...</h3><p>...</p></div>
      B) One <div class="faq"> wrapping H2 + multiple H3/p pairs
      C) FAQ H2 followed by H3/p pairs (no wrapper div)
    """
    faqs = []

    # Layout A — per-Q&A divs
    pattern_a = r'<div class="faq">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>'
    for match in re.finditer(pattern_a, draft_html, re.DOTALL):
        q = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        a = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if q and a:
            faqs.append({"q": q, "a": a})
    if faqs:
        return faqs

    # Layout B/C — scope to FAQ section (between FAQ H2 and next H2 or end)
    faq_section = re.search(
        r'<h2[^>]*>\s*(?:frequently asked questions|faq|faqs|q\s*&\s*a)\s*</h2>(.*?)(?=<h2|$)',
        draft_html, re.I | re.S
    )
    scope = faq_section.group(1) if faq_section else draft_html

    # Find each <h3>...</h3> followed by <p>...</p> pair within scope
    pair_pattern = r'<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>'
    for match in re.finditer(pair_pattern, scope, re.DOTALL):
        q = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        a = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if q and a and q.endswith("?"):
            faqs.append({"q": q, "a": a})

    return faqs


def get_related_posts(current_slug, max_links=3):
    """Find related blog posts for internal linking."""
    all_posts = []
    for f in BLOG_DIR.glob("*.html"):
        if f.name in ["index.html", f"{current_slug}.html"]:
            continue
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        title_match = re.search(r"<title>(.*?)</title>", content)
        h1_match = re.search(r"<h1>(.*?)</h1>", content)
        if title_match and h1_match:
            title = title_match.group(1).split("|")[0].strip()
            h1 = h1_match.group(1).strip()
            all_posts.append({"slug": f.stem, "title": title, "h1": h1})

    if len(all_posts) <= max_links:
        return all_posts
    return random.sample(all_posts, max_links)


def inject_internal_links(article_body, related_posts):
    """Add a Related Reading box at end of article body."""
    if not related_posts:
        return article_body
    links_html = '<div class="related-reading"><h3>Related reading</h3><ul>'
    for post in related_posts:
        links_html += f'<li><a href="/blog/{post["slug"]}.html">{post["h1"]}</a></li>'
    links_html += "</ul></div>"
    if '<div class="cta">' in article_body:
        article_body = article_body.replace('<div class="cta">', links_html + '<div class="cta">')
    else:
        article_body = article_body + "\n" + links_html
    return article_body


def build_schemas(meta, keyword, today, faqs, canonical_url):
    """Build Article + FAQPage + LocalBusiness schemas."""
    schemas = []

    schemas.append({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta["schema_headline"],
        "description": meta["schema_description"],
        "image": "https://patrolgarage.ae/images/og-blog-y62.jpg",
        "author": {"@type": "Organization", "name": "Patrol Garage Dubai"},
        "publisher": {"@type": "Organization", "name": "Patrol Garage Dubai"},
        "datePublished": today,
        "dateModified": today,
        "mainEntityOfPage": canonical_url
    })

    if faqs:
        schemas.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
                } for faq in faqs
            ]
        })

    schemas.append({
        "@context": "https://schema.org",
        "@type": "AutoRepair",
        "name": "Patrol Garage Dubai",
        "image": "https://patrolgarage.ae/images/og-blog-y62.jpg",
        "telephone": "+971582211201",
        "url": "https://patrolgarage.ae",
        "areaServed": {"@type": "City", "name": "Dubai"},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Ras Al Khor",
            "addressRegion": "Dubai",
            "addressCountry": "AE"
        },
        "geo": {"@type": "GeoCoordinates", "latitude": 25.1768, "longitude": 55.3537},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Sunday","Monday","Tuesday","Wednesday","Thursday"], "opens": "09:00", "closes": "19:00"},
            {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday", "opens": "09:00", "closes": "14:00"}
        ],
        "priceRange": "AED 400-25000"
    })

    blocks = []
    for s in schemas:
        blocks.append(f'<script type="application/ld+json">\n{json.dumps(s, indent=2, ensure_ascii=False)}\n</script>')
    return "\n  ".join(blocks)


def extract_article_body(draft_html):
    html = draft_html.strip()
    html = re.sub(r'<div class="cta">.*?</div>', "", html, flags=re.DOTALL)
    html = re.sub(r"<h1>.*?</h1>", "", html, count=1, flags=re.DOTALL)
    return html.strip()


def assemble(keyword):
    slug = slugify(keyword)
    draft_path = DRAFTS_DIR / f"{slug}.html"

    if not draft_path.exists():
        print(f"[!] No draft at {draft_path}")
        sys.exit(1)

    print(f"[+] Assembling: {keyword}")

    with open(draft_path, encoding="utf-8") as f:
        draft_html = f.read()

    print("    Generating SEO metadata...")
    meta = generate_meta(keyword, draft_html)

    faqs = extract_faqs(draft_html)
    print(f"    Found {len(faqs)} FAQ pairs for schema")

    related = get_related_posts(slug, max_links=3)
    print(f"    Adding {len(related)} internal links")

    article_body = extract_article_body(draft_html)
    article_body = inject_internal_links(article_body, related)

    today = datetime.now().strftime("%Y-%m-%d")
    canonical_url = f"https://patrolgarage.ae/blog/{slug}.html"

    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        template = f.read()

    template = re.sub(r"<title>.*?</title>", f"<title>{meta['title']}</title>", template, count=1)
    template = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{meta["description"]}">', template, count=1)
    template = re.sub(r'<meta name="keywords" content=".*?">', f'<meta name="keywords" content="{meta["keywords"]}">', template, count=1)
    template = re.sub(r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{canonical_url}">', template, count=1)
    template = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{meta["og_title"]}">', template, count=1)
    template = re.sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{meta["og_description"]}">', template, count=1)
    template = re.sub(r'<meta property="og:url" content=".*?">', f'<meta property="og:url" content="{canonical_url}">', template, count=1)
    template = re.sub(r'<meta name="twitter:title" content=".*?">', f'<meta name="twitter:title" content="{meta["tw_title"]}">', template, count=1)
    template = re.sub(r'<meta name="twitter:description" content=".*?">', f'<meta name="twitter:description" content="{meta["tw_description"]}">', template, count=1)

    new_schemas = build_schemas(meta, keyword, today, faqs, canonical_url)
    template = re.sub(r'<script type="application/ld\+json">.*?</script>', new_schemas, template, count=1, flags=re.DOTALL)

    new_hero = f'''<div class="hero-meta"><span class="hero-meta-line"></span><span>{meta["hero_tag_1"]}</span><span>·</span><span>{meta["hero_tag_2"]}</span></div>
      <h1>{meta["h1_short"]}</h1>'''
    template = re.sub(r'<div class="hero-meta">.*?</h1>', new_hero, template, count=1, flags=re.DOTALL)

    # Swap hero background to AI-generated image for this slug
    new_hero_bg = (
        f'<div class="hero-bg"><picture>'
        f'<source srcset="../images/blog/{slug}.avif" type="image/avif">'
        f'<img src="../images/blog/{slug}.jpg" alt="{meta["h1_short"]}">'
        f'</picture></div>'
    )
    template = re.sub(r'<div class="hero-bg">.*?</div>', new_hero_bg, template, count=1, flags=re.DOTALL)

    new_article = f"<article>\n{article_body}\n    </article>"
    template = re.sub(r'<article>.*?</article>', new_article, template, count=1, flags=re.DOTALL)

    template = re.sub(
        r'href="https://wa\.me/971582211201\?text=[^"]*"',
        f'href="https://wa.me/971582211201?text={meta["wa_text"]}"',
        template,
        count=1,
    )

    out_path = BLOG_DIR / f"{slug}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"\n[+] Assembled: {out_path}")
    print(f"    Title: {meta['title']}")
    print(f"    Schemas: Article + {'FAQPage + ' if faqs else ''}AutoRepair")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 assemble.py \"your keyword here\"")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    assemble(keyword)
