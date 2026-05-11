import os
import re
from pathlib import Path
from anthropic import Anthropic

root = Path.home() / "Desktop/Projects/patrolgarage"
client = Anthropic()

# Y62 cluster posts (slug, title, anchor)
clusters = [
    ("nissan-patrol-y62-problems-dubai", "Common Y62 Problems in Dubai", "Y62 problems overview"),
    ("nissan-patrol-y62-transmission-problems-dubai", "Y62 Transmission Problems", "Y62 transmission issues"),
    ("nissan-patrol-y61-vs-y62-dubai", "Y61 vs Y62 Comparison", "Y61 vs Y62 comparison"),
    ("nissan-patrol-service-cost-dubai", "Nissan Patrol Service Costs Dubai", "service costs in Dubai"),
    ("nissan-patrol-suspension-dubai", "Patrol Suspension in Dubai", "suspension issues"),
    ("nissan-patrol-ac-problems-dubai", "Patrol AC Problems in Dubai Heat", "AC problems"),
    ("nissan-patrol-gearbox-problems-uae", "Patrol Gearbox Problems UAE", "gearbox issues"),
    ("best-oil-nissan-patrol-uae-heat", "Best Oil for Patrol in UAE Heat", "oil recommendations"),
]

cluster_list_md = "\n".join([f"- {title} → /blog/{slug}.html" for slug, title, _ in clusters])

prompt = f"""Write a comprehensive pillar page for "Nissan Patrol Y62 Dubai: The Complete Owner's Guide."

Target: 3500-4000 words. Audience: Y62 owners in Dubai/UAE. Tone: first-person plural ("we see", "we recommend"), conversational expert, mechanic voice.

STRUCTURE (mandatory):
1. H1: Nissan Patrol Y62 Dubai: The Complete Owner's Guide
2. Direct Answer block (2-3 sentences with specific facts)
3. Evidence/Context paragraph (200-250 words)
4. 8 H2 sections, each as a question, each followed by 1-sentence direct answer, then 250-350 words. Each H2 must internally link to ONE of these cluster posts using a contextual sentence with descriptive anchor text:

{cluster_list_md}

5. FAQ section: 5 Q&A pairs (each Q in <h3>, each A in <p>)
6. Final CTA paragraph

FACTS YOU CAN USE (no [NEEDS_SOURCE] tags):
- Y62 launched 2010 in UAE, refreshed 2016 and 2020
- VK56VD 5.6L V8, 400hp
- 7-speed automatic (Jatco JR710E / RE7R01A)
- Dubai climate: 45-50°C ambient, 70°C+ tarmac
- Major service AED 800-2500
- Transmission rebuild AED 8000-18000
- AC compressor AED 2500-5000
- Common trims: SE, XE, LE, Platinum, Nismo
- Off-road areas: Al Qudra, Big Red, Liwa

OUTPUT ONLY THE HTML BODY CONTENT (no <html>, no <head>, no <body> tags). Start with <h1>. Use <h2>, <h3>, <p>, <ul>, <li>, <a href="..."> tags. For internal links use full path like /blog/slug.html.
Wrap FAQ items in <div class="faq"><h3>Q</h3><p>A</p></div>
End with <div class="last-updated">UPDATED · MAY 2026</div>"""

print("[*] Generating pillar content (this takes 30-60s)...")
resp = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,
    messages=[{"role": "user", "content": prompt}]
)

content = resp.content[0].text

# Load template from existing Y62 post
template_file = root / "blog" / "nissan-patrol-y62-problems-dubai.html"
template = template_file.read_text()

# Extract everything before <h1> and everything after the article body
# Find the article container
h1_match = re.search(r'<h1[^>]*>', template)
if not h1_match:
    print("[!] Could not find <h1> in template")
    exit(1)

pre_h1 = template[:h1_match.start()]

# Find end of article body (before related reading or footer)
related_match = re.search(r'<section[^>]*class="[^"]*related', template) or re.search(r'<footer', template)
if not related_match:
    print("[!] Could not find article end marker")
    exit(1)

post_body = template[related_match.start():]

# Build new pillar HTML
new_html = pre_h1 + content + "\n\n" + post_body

# Replace title and meta in pre_h1
new_html = re.sub(
    r'<title>[^<]+</title>',
    '<title>Nissan Patrol Y62 Dubai: The Complete Owner\'s Guide | Patrol Garage</title>',
    new_html
)
new_html = re.sub(
    r'<meta name="description" content="[^"]+"',
    '<meta name="description" content="Complete guide to owning a Nissan Patrol Y62 in Dubai. Problems, service costs, maintenance schedule, and Dubai-specific advice from Patrol specialists."',
    new_html
)

# Save pillar
pillar_path = root / "blog" / "nissan-patrol-y62-dubai-complete-guide.html"
pillar_path.write_text(new_html)
print(f"[✓] Pillar saved: {pillar_path.name}")

# Now inject pillar link into each cluster post
pillar_link_html = '''<div class="pillar-link" style="margin: 1.5rem 0; padding: 1rem 1.25rem; border-left: 2px solid var(--text-3); background: rgba(255,255,255,0.02); font-size: 0.9rem;">
  <span style="color: var(--text-3); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;">Part of</span><br>
  <a href="/blog/nissan-patrol-y62-dubai-complete-guide.html" style="color: var(--text-1); text-decoration: none; font-weight: 500;">Nissan Patrol Y62 Dubai: The Complete Owner's Guide →</a>
</div>
'''

injected = 0
for slug, _, _ in clusters:
    cluster_file = root / "blog" / f"{slug}.html"
    if not cluster_file.exists():
        print(f"[!] Missing: {slug}")
        continue
    cluster_html = cluster_file.read_text()
    if "pillar-link" in cluster_html:
        print(f"[-] Already has pillar link: {slug}")
        continue
    # Inject right after the <h1>
    cluster_html = re.sub(
        r'(</h1>)',
        r'\1\n' + pillar_link_html,
        cluster_html,
        count=1
    )
    cluster_file.write_text(cluster_html)
    injected += 1
    print(f"[+] Injected pillar link: {slug}")

print(f"\n[✓] Pillar built and {injected} cluster posts linked")

# Update sitemap
sitemap = root / "sitemap.xml"
if sitemap.exists():
    sm = sitemap.read_text()
    if "y62-dubai-complete-guide" not in sm:
        new_url = f'''  <url>
    <loc>https://patrolgarage.ae/blog/nissan-patrol-y62-dubai-complete-guide.html</loc>
    <lastmod>2026-05-11</lastmod>
    <priority>0.9</priority>
  </url>
</urlset>'''
        sm = sm.replace("</urlset>", new_url)
        sitemap.write_text(sm)
        print("[✓] Sitemap updated")
