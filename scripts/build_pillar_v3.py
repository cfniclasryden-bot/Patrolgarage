#!/usr/bin/env python3
"""Build any pillar page from a config."""
import sys, re, shutil
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
client = Anthropic()

PILLARS = {
    "y61": {
        "slug": "nissan-patrol-y61-dubai-complete-guide",
        "title": "Nissan Patrol Y61 Dubai: The Complete Owner's Guide",
        "eyebrow": "Y61 · Complete Guide · Dubai",
        "description": "Complete guide to owning a Nissan Patrol Y61 / Super Safari in Dubai. Common issues, maintenance, costs, and Dubai-specific advice.",
        "meta_keywords": "Y61 problems, Nissan Patrol Y61, Super Safari, Dubai repair",
        "source_template": "nissan-patrol-y61-vs-y62-dubai",
        "clusters": [
            ("nissan-patrol-y61-vs-y62-dubai", "Y61 vs Y62 Comparison"),
            ("nissan-patrol-off-road-uae", "Patrol Off-Road in UAE"),
            ("nissan-patrol-pre-purchase-inspection", "Patrol Pre-Purchase Inspection"),
            ("nissan-patrol-mechanic-al-quoz", "Patrol Mechanic Al Quoz"),
            ("nissan-patrol-service-cost-dubai", "Patrol Service Costs Dubai"),
        ],
        "facts": """
- Y61 produced 1997-2016 globally, still sold as Super Safari in GCC region today
- TB48DE 4.8L inline-6 petrol, RD28 / ZD30 diesel options in older models
- 5-speed manual or 4-speed automatic transmissions
- Body-on-frame construction, solid axles front and rear
- Beloved by serious off-roaders in UAE
- Common trims: GL, GLX, Safari, Super Safari
- Dubai: 45-50°C ambient, 70°C+ tarmac
- Off-road areas: Al Qudra, Big Red, Liwa
- Major service AED 800-2500
- Engine rebuild AED 15,000-35,000
- Suspension overhaul AED 4,000-12,000
- Pre-purchase inspection AED 400-800
""",
    },
    "service": {
        "slug": "nissan-patrol-service-dubai-complete-guide",
        "title": "Nissan Patrol Service in Dubai: The Complete Guide",
        "eyebrow": "Service · Workshops · Dubai",
        "description": "Complete guide to servicing a Nissan Patrol in Dubai. Workshop selection, costs, intervals, dealer vs independent comparison.",
        "meta_keywords": "Patrol service Dubai, Nissan Patrol workshop, Al Futtaim alternative, Patrol mechanic",
        "source_template": "nissan-patrol-service-cost-dubai",
        "clusters": [
            ("nissan-patrol-service-cost-dubai", "Patrol Service Costs Dubai"),
            ("nissan-patrol-mechanic-al-quoz", "Patrol Mechanic Al Quoz"),
            ("nissan-patrol-pre-purchase-inspection", "Patrol Pre-Purchase Inspection"),
            ("nissan-patrol-gearbox-problems-uae", "Patrol Gearbox Problems"),
            ("nissan-patrol-ac-problems-dubai", "Patrol AC Problems"),
        ],
        "facts": """
- Dubai workshop areas: Ras Al Khor, Al Quoz, Deira/Al Aweer, Sharjah Industrial
- Major service AED 800-2,500
- Transmission fluid change AED 600-1,200
- Transmission rebuild AED 8,000-18,000
- Engine rebuild AED 15,000-35,000
- AC compressor replacement AED 2,500-5,000
- Suspension overhaul AED 4,000-12,000
- Pre-purchase inspection AED 400-800
- Al Futtaim Nissan = official dealer (premium pricing, genuine parts)
- Independent workshops 30-50% cheaper, varying quality
- Service intervals: every 5,000-7,500 km in Dubai (vs factory 10,000 km) due to heat
""",
    },
}


def build(pillar_key):
    config = PILLARS[pillar_key]
    source = ROOT / "blog" / f"{config['source_template']}.html"
    pillar = ROOT / "blog" / f"{config['slug']}.html"

    if not source.exists():
        print(f"[!] Source template not found: {source}")
        return False

    shutil.copy(source, pillar)
    print(f"[+] Duplicated {source.name} -> {pillar.name}")

    html = pillar.read_text()

    # Find content boundaries
    h1_start = html.find('<h1')
    footer_start = html.find('<footer')
    container_match = None
    container_tag = None
    for tag in ['main', 'article', 'section']:
        matches = list(re.finditer(rf'<{tag}[^>]*>', html[:h1_start]))
        if matches:
            container_match = matches[-1]
            container_tag = tag
            break
    if not container_match:
        print("[!] No content container found")
        return False

    content_start = container_match.end()
    closing_pos = html.rfind(f'</{container_tag}>', content_start, footer_start)
    original_content = html[content_start:closing_pos]

    cluster_md = "\n".join([f"- /blog/{slug}.html → {title}" for slug, title in config["clusters"]])

    prompt = f"""You are rewriting the article body of an existing blog post template. Match the exact HTML structure, classes, and styling. Do NOT add new wrapper divs.

ORIGINAL TEMPLATE CONTENT:
{original_content}

NEW TOPIC: "{config['title']}"

REQUIREMENTS:
- Match the exact HTML element types and class names as the original
- Replace H1 text with: {config['title']}
- Replace the eyebrow text with: {config['eyebrow']}
- 3500-4000 word pillar page
- Use {len(config['clusters'])} H2 sections, each phrased as a question
- Each H2 must internally link to one cluster post via contextual anchor text:
{cluster_md}
- Include 5 FAQ items at the end using the same FAQ HTML pattern
- Include "UPDATED · MAY 2026" badge using same pattern as original

FACTS YOU CAN USE:
{config['facts']}

Dubai context: 45-50°C summers, 70°C+ tarmac, sand/dust ingress, off-road areas (Al Qudra, Big Red, Liwa).

OUTPUT: Return ONLY the new HTML content that replaces what's between <{container_tag}> and </{container_tag}>. Match the original's nesting and class usage exactly."""

    print(f"[*] Generating pillar content (60-90s)...")
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    new_content = resp.content[0].text.strip()
    new_content = re.sub(r'^```html\s*', '', new_content)
    new_content = re.sub(r'^```\s*', '', new_content)
    new_content = re.sub(r'\s*```$', '', new_content)

    new_html = html[:content_start] + "\n" + new_content + "\n" + html[closing_pos:]

    # Update metadata
    new_html = re.sub(r'<title>[^<]+</title>', f"<title>{config['title']} | Patrol Garage</title>", new_html)
    new_html = re.sub(r'<meta name="description" content="[^"]+"', f'<meta name="description" content="{config["description"]}"', new_html)
    new_html = re.sub(r'<meta name="keywords" content="[^"]+"', f'<meta name="keywords" content="{config["meta_keywords"]}"', new_html)
    new_html = re.sub(r'<link rel="canonical" href="[^"]+"', f'<link rel="canonical" href="https://patrolgarage.ae/blog/{config["slug"]}.html"', new_html)
    new_html = re.sub(r'<meta property="og:url" content="[^"]+"', f'<meta property="og:url" content="https://patrolgarage.ae/blog/{config["slug"]}.html"', new_html)
    new_html = re.sub(r'<meta property="og:title" content="[^"]+"', f'<meta property="og:title" content="{config["title"]}"', new_html)

    pillar.write_text(new_html)
    print(f"[+] Pillar saved: {pillar.name} ({len(new_html)} chars)")

    # Inject pillar link into cluster posts
    pillar_link = f'''<div class="pillar-link" style="margin: 1.5rem 0; padding: 1rem 1.25rem; border-left: 2px solid var(--text-3); background: rgba(255,255,255,0.02); font-size: 0.9rem;">
  <span style="color: var(--text-3); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;">Part of</span><br>
  <a href="/blog/{config['slug']}.html" style="color: var(--text-1); text-decoration: none; font-weight: 500;">{config['title']} →</a>
</div>
'''

    injected = 0
    for slug, _ in config["clusters"]:
        f = ROOT / "blog" / f"{slug}.html"
        if not f.exists():
            continue
        ch = f.read_text()
        # Allow multiple pillar links per post (a post can belong to multiple pillars)
        if config['slug'] in ch:
            continue
        ch = re.sub(r'(</h1>)', r'\1\n' + pillar_link, ch, count=1)
        f.write_text(ch)
        injected += 1
    print(f"[+] Injected pillar link into {injected} cluster posts")

    # Update sitemap
    sm = ROOT / "sitemap.xml"
    if sm.exists():
        smc = sm.read_text()
        if config['slug'] not in smc:
            new_url = f'''  <url>
    <loc>https://patrolgarage.ae/blog/{config['slug']}.html</loc>
    <lastmod>2026-05-11</lastmod>
    <priority>0.9</priority>
  </url>
</urlset>'''
            smc = smc.replace("</urlset>", new_url)
            sm.write_text(smc)
            print("[+] Sitemap updated")

    return True


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PILLARS:
        print(f"Usage: python3 build_pillar_v3.py <{'/'.join(PILLARS.keys())}>")
        sys.exit(1)
    build(sys.argv[1])
