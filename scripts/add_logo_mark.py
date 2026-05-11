#!/usr/bin/env python3
"""add_logo_mark.py — add minimal SVG shield mark to logo across all pages"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Minimal shield SVG — geometric, single stroke, no fill
SHIELD_SVG = '<svg class="logo-mark" viewBox="0 0 24 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 1L2 5v9c0 7 4.5 11 10 13 5.5-2 10-6 10-13V5l-10-4z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>'

# CSS for the mark + hover effect
LOGO_CSS = """
    .logo { display: inline-flex; align-items: center; gap: 0.55rem; }
    .logo-mark { width: 18px; height: 21px; flex-shrink: 0; color: var(--white); transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
    .logo:hover .logo-mark { transform: rotate(360deg); }
    @media (max-width: 480px) { .logo-mark { width: 16px; height: 19px; } }"""

html_files = list(PROJECT_ROOT.glob("*.html")) + list(PROJECT_ROOT.glob("blog/*.html"))

updated = 0
for f in html_files:
    with open(f, encoding="utf-8") as fh:
        content = fh.read()
    original = content

    # Skip if mark already added
    if 'class="logo-mark"' in content:
        continue

    # Inject SVG mark inside .logo links, before the first <span>
    content = re.sub(
        r'(<a [^>]*class="logo"[^>]*>)\s*(<span>)',
        r'\1' + SHIELD_SVG + r'\2',
        content
    )

    # Inject CSS — add inside the existing <style> block, after .logo {} rules
    # Find the existing .logo rule and inject our enhanced version after it
    if "logo-mark" not in content and "<style>" in content:
        # Add our CSS just before </style>
        content = content.replace(
            "</style>",
            LOGO_CSS + "\n    </style>",
            1
        )

    if content != original:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"  ✓ Updated: {f.relative_to(PROJECT_ROOT)}")
        updated += 1

print(f"\n[+] Added logo mark to {updated} files")
