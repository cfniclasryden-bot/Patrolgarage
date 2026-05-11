import re
import shutil
from pathlib import Path
from anthropic import Anthropic

root = Path.home() / "Desktop/Projects/patrolgarage"
client = Anthropic()

source = root / "blog" / "nissan-patrol-y62-problems-dubai.html"
pillar = root / "blog" / "nissan-patrol-y62-dubai-complete-guide.html"

# Step 1: Duplicate source file as pillar
shutil.copy(source, pillar)
print(f"[+] Duplicated source -> pillar")

html = pillar.read_text()

# Step 2: Identify the article content boundaries
# Find first <h1> and the last paragraph before <footer>
h1_start = html.find('<h1')
if h1_start == -1:
    print("[!] No h1 found")
    exit(1)

footer_start = html.find('<footer')
if footer_start == -1:
    print("[!] No footer found")
    exit(1)

# Find where the main content section starts (parent of h1)
# Find the article/main/section opening tag that contains h1
# Look backwards from h1 for nearest opening tag
search_region = html[:h1_start]
container_match = None
for tag in ['main', 'article', 'section']:
    matches = list(re.finditer(rf'<{tag}[^>]*>', search_region))
    if matches:
        container_match = matches[-1]
        container_tag = tag
        break

if not container_match:
    print("[!] Could not find article container")
    exit(1)

# Find matching closing tag before footer
content_start = container_match.end()
# Find </tag> closest to but before footer
closing_pattern = f'</{container_tag}>'
closing_pos = html.rfind(closing_pattern, content_start, footer_start)
if closing_pos == -1:
    print(f"[!] Could not find closing {closing_pattern}")
    exit(1)

original_content = html[content_start:closing_pos]
print(f"[i] Found content section: {len(original_content)} chars")
print(f"[i] Container: <{container_tag}>")

# Step 3: Generate new pillar content via Claude
clusters = [
    ("nissan-patrol-y62-problems-dubai", "Common Y62 Problems in Dubai"),
    ("nissan-patrol-y62-transmission-problems-dubai", "Y62 Transmission Problems"),
    ("nissan-patrol-y61-vs-y62-dubai", "Y61 vs Y62 Comparison"),
    ("nissan-patrol-service-cost-dubai", "Nissan Patrol Service Costs Dubai"),
    ("nissan-patrol-suspension-dubai", "Patrol Suspension in Dubai"),
    ("nissan-patrol-ac-problems-dubai", "Patrol AC Problems in Dubai Heat"),
    ("nissan-patrol-gearbox-problems-uae", "Patrol Gearbox Problems UAE"),
    ("best-oil-nissan-patrol-uae-heat", "Best Oil for Patrol in UAE Heat"),
]

cluster_md = "\n".join([f"- /blog/{slug}.html → {title}" for slug, title in clusters])

prompt = f"""You are rewriting the article body of an existing blog post. Match the exact HTML structure and styling of the original — do NOT add new wrapper divs, hero sections, or change classes.

ORIGINAL CONTENT TO REPLACE (study its structure carefully):

{original_content}

NEW TOPIC: This becomes a pillar page titled "Nissan Patrol Y62 Dubai: The Complete Owner's Guide"

REQUIREMENTS:
- Keep the exact same HTML element types, class names, and structural pattern as the original
- Replace the H1 text with: Nissan Patrol Y62 Dubai: The Complete Owner's Guide
- Replace the eyebrow/category text (e.g. "Y62 Issues · Diagnosis") with: Y62 · Complete Guide · Dubai
- Replace the body content with 3500-4000 words covering Y62 ownership in Dubai
- Use 8 H2 sections, each phrased as a question
- Each H2 must internally link to one cluster post using contextual anchor text within a sentence:
{cluster_md}
- Include 5 FAQ items at the end (use same FAQ HTML pattern as original)
- Include "UPDATED · MAY 2026" badge using same pattern as original

FACTS YOU CAN USE:
- Y62 launched 2010 in UAE, refreshed 2016 and 2020
- VK56VD 5.6L V8, 400hp
- 7-speed automatic (Jatco JR710E / RE7R01A)
- Dubai: 45-50°C ambient, 70°C+ tarmac
- Major service AED 800-2500
- Transmission rebuild AED 8000-18000
- AC compressor AED 2500-5000
- Trims: SE, XE, LE, Platinum, Nismo
- Off-road: Al Qudra, Big Red, Liwa

OUTPUT: Return ONLY the new HTML content that should replace what's between <{container_tag}> and </{container_tag}>. Do not include the {container_tag} tags themselves. Match the original's nesting and class usage exactly."""

print("[*] Generating pillar content (60-90s)...")
resp = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,
    messages=[{"role": "user", "content": prompt}]
)

new_content = resp.content[0].text.strip()

# Strip code fences if present
new_content = re.sub(r'^```html\s*', '', new_content)
new_content = re.sub(r'^```\s*', '', new_content)
new_content = re.sub(r'\s*```$', '', new_content)

# Step 4: Replace content in pillar file
new_html = html[:content_start] + "\n" + new_content + "\n" + html[closing_pos:]

# Step 5: Update meta tags
new_html = re.sub(
    r'<title>[^<]+</title>',
    '<title>Nissan Patrol Y62 Dubai: The Complete Owner\'s Guide | Patrol Garage</title>',
    new_html
)
new_html = re.sub(
    r'<meta name="description" content="[^"]+"',
    '<meta name="description" content="Complete guide to owning a Nissan Patrol Y62 in Dubai. Problems, service costs, maintenance schedule, and Dubai-specific advice."',
    new_html
)
new_html = re.sub(
    r'<link rel="canonical" href="[^"]+"',
    '<link rel="canonical" href="https://patrolgarage.ae/blog/nissan-patrol-y62-dubai-complete-guide.html"',
    new_html
)
new_html = re.sub(
    r'<meta property="og:url" content="[^"]+"',
    '<meta property="og:url" content="https://patrolgarage.ae/blog/nissan-patrol-y62-dubai-complete-guide.html"',
    new_html
)
new_html = re.sub(
    r'<meta property="og:title" content="[^"]+"',
    '<meta property="og:title" content="Nissan Patrol Y62 Dubai: The Complete Owner\'s Guide"',
    new_html
)

pillar.write_text(new_html)
print(f"[✓] Pillar saved: {pillar.name} ({len(new_html)} chars)")

# Step 6: Inject pillar links into cluster posts
pillar_link = '''<div class="pillar-link" style="margin: 1.5rem 0; padding: 1rem 1.25rem; border-left: 2px solid var(--text-3); background: rgba(255,255,255,0.02); font-size: 0.9rem;">
  <span style="color: var(--text-3); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase;">Part of</span><br>
  <a href="/blog/nissan-patrol-y62-dubai-complete-guide.html" style="color: var(--text-1); text-decoration: none; font-weight: 500;">Nissan Patrol Y62 Dubai: The Complete Owner's Guide →</a>
</div>
'''

injected = 0
for slug, _ in clusters:
    f = root / "blog" / f"{slug}.html"
    if not f.exists():
        continue
    cluster_html = f.read_text()
    if "pillar-link" in cluster_html:
        continue
    cluster_html = re.sub(r'(</h1>)', r'\1\n' + pillar_link, cluster_html, count=1)
    f.write_text(cluster_html)
    injected += 1

print(f"[✓] Injected pillar link into {injected} cluster posts")

# Step 7: Update sitemap
sm = root / "sitemap.xml"
if sm.exists():
    smc = sm.read_text()
    if "y62-dubai-complete-guide" not in smc:
        new_url = '''  <url>
    <loc>https://patrolgarage.ae/blog/nissan-patrol-y62-dubai-complete-guide.html</loc>
    <lastmod>2026-05-11</lastmod>
    <priority>0.9</priority>
  </url>
</urlset>'''
        smc = smc.replace("</urlset>", new_url)
        sm.write_text(smc)
        print("[✓] Sitemap updated")
