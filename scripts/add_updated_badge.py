#!/usr/bin/env python3
"""add_updated_badge.py — inject 'UPDATED · MONTH YEAR' badge into all blog posts"""

import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"

# Current month/year
NOW = datetime.now()
UPDATED_TEXT = f"UPDATED · {NOW.strftime('%B %Y').upper()}"

# Badge HTML — sits just below hero, above article body
BADGE_HTML = f'''
  <section class="updated-badge-section">
    <div class="container">
      <span class="updated-badge">{UPDATED_TEXT}</span>
    </div>
  </section>
'''

# CSS for the badge — matches monochrome design
BADGE_CSS = """
    .updated-badge-section { background: var(--bg); padding: 1.5rem 0 0 0; }
    .updated-badge-section .container { max-width: 820px; margin: 0 auto; padding: 0 1.5rem; }
    .updated-badge { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-3); letter-spacing: 0.15em; padding: 0.4rem 0.8rem; border: 1px solid var(--line); border-radius: 4px; display: inline-block; }"""

blog_files = [f for f in BLOG_DIR.glob("*.html") if f.name != "index.html"]
updated = 0

for f in blog_files:
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    original = content

    # Skip if badge already exists
    if "updated-badge-section" in content:
        # Update the date inside existing badge
        content = re.sub(
            r'<span class="updated-badge">UPDATED · [A-Z]+ \d{4}</span>',
            f'<span class="updated-badge">{UPDATED_TEXT}</span>',
            content
        )
    else:
        # Inject badge section after </section> for hero (between hero and dark section with article)
        # Hero closes with </section>, then "<section class=\"dark\">" begins
        content = re.sub(
            r'(</section>)\s*(<section class="dark">)',
            r'\1' + BADGE_HTML + r'  \2',
            content,
            count=1
        )

        # Inject CSS before </style>
        if "updated-badge" not in content.split("</style>")[0]:
            content = content.replace("</style>", BADGE_CSS + "\n    </style>", 1)

    if content != original:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  ✓ Updated: {f.name}")
        updated += 1

print(f"\n[+] Added/refreshed badge in {updated} blog posts")
print(f"[+] Badge text: {UPDATED_TEXT}")
