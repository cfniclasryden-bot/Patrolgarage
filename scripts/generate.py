#!/usr/bin/env python3
"""generate.py — turn research JSON into a blog post draft"""

import sys
import os
import json
import re
from pathlib import Path
from anthropic import Anthropic

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
DRAFTS_DIR = PROJECT_ROOT / "drafts"
DRAFTS_DIR.mkdir(exist_ok=True)

client = Anthropic()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


DUBAI_CONTEXT = """KNOWN FACTS YOU CAN USE WITHOUT FLAGGING:

NISSAN PATROL MODELS IN UAE:
- Y61: produced 1997-2016 globally, still sold as Super Safari in GCC region today
- Y62: launched 2010 in UAE, refreshed in 2016 and 2020, sold with VK56VD 5.6L V8
- Y63: launched in UAE in 2024, replaces Y62 as the new flagship
- Y62 transmission: 7-speed automatic (Jatco JR710E / RE7R01A)
- Y62 engine: VK56VD 5.6L V8, 400hp
- Common trims in UAE: SE, XE, LE, Platinum, Nismo

DUBAI CLIMATE CONTEXT:
- Summer temperatures hit 45-50°C ambient, 70°C+ on tarmac
- Sand and dust ingress is constant
- Salt humidity along the coast accelerates corrosion
- Stop-and-go traffic in Sheikh Zayed Road, Sheikh Mohammed Bin Zayed Road
- Off-road usage common in desert (Al Qudra, Big Red, Liwa)

TYPICAL UAE WORKSHOP PRICING (use as plausible ranges, not exact quotes):
- Major service: AED 800-2,500
- Transmission fluid change: AED 600-1,200
- Transmission rebuild: AED 8,000-18,000
- Transmission replacement (used): AED 12,000-25,000
- Engine rebuild: AED 15,000-35,000
- AC compressor replacement: AED 2,500-5,000
- Suspension overhaul: AED 4,000-12,000
- Pre-purchase inspection: AED 400-800

DUBAI-RELEVANT AREAS:
- Ras Al Khor: industrial area with many workshops
- Al Quoz: another major workshop district
- Deira / Al Aweer: used car market
- Sharjah Industrial: cheaper alternative workshops

GCC-SPECIFIC PATROL QUIRKS:
- AC system works much harder than in temperate markets
- Fuel quality (95 RON) is good but premium fuel is rarely needed
- Cooling system stress is significantly higher
- Many imported used Patrols from Japan (RHD converted) or Canada

You can reference any of these facts naturally without flagging. Only flag with [NEEDS_SOURCE] for claims that would require specific data you genuinely don't have (e.g., a specific recall number, an exact dealer service interval, a named workshop's quote)."""


PROMPT_TEMPLATE = """You are writing a blog post for Patrol Garage, a Nissan Patrol specialist workshop in Dubai (Ras Al Khor). Target audience: Patrol owners in the UAE searching for help with their vehicle.

TARGET KEYWORD: {keyword}

{dubai_context}

SOURCE MATERIAL (additional context to draw from):
---
{sources}
---

REQUIREMENTS:
1. Length: 1500-2000 words
2. Tone: conversational expert. Like a mechanic talking to a customer, not corporate marketing. First-person plural ("we see", "we recommend") is fine.
3. Structure:
   - H1 with the target keyword
   - 200-300 word intro that hooks the reader with the actual problem
   - 5-7 H2 sections covering different angles
   - Specific numbers: model years, kilometers, AED costs (use the typical ranges above), part names
   - Reference Dubai-specific factors naturally
   - Final H2: "When to bring it to Patrol Garage" with brief CTA
4. Only flag [NEEDS_SOURCE] for very specific data not in the context above (e.g., specific recall numbers, named workshop quotes). Standard facts about Y62/Y61/Y63, Dubai climate, typical AED price ranges are fair game.
5. Use the degree symbol ° (not Â°). Use proper em-dashes — not â€".
6. Output: clean HTML using only <h1>, <h2>, <h3>, <p>, <ul>, <li>, <strong>. No <html>, <head>, <body>, no styling. Just the article body.
7. End with this exact CTA block:
   <div class="cta">
     <p><strong>Need help with your Patrol?</strong> Call us on +971 58 221 1201 or <a href="/contact.html">request a quote</a>.</p>
   </div>

Return ONLY the HTML body. No preamble, no markdown fences, no explanation."""


def generate_post(keyword):
    slug = slugify(keyword)
    research_path = RESEARCH_DIR / f"{slug}.json"

    if not research_path.exists():
        print(f"[!] No research found at {research_path}")
        sys.exit(1)

    with open(research_path, encoding="utf-8") as f:
        research = json.load(f)

    if not research["sources"]:
        print("[!] Research file has zero sources.")
        sys.exit(1)

    # Prioritize forum + youtube sources over web (less marketing fluff)
    def source_priority(s):
        return {"forum": 0, "youtube": 1, "web": 2}.get(s.get("type", "web"), 3)
    sorted_sources = sorted(research["sources"], key=source_priority)

    source_blocks = []
    for i, src in enumerate(sorted_sources[:12], 1):
        content = src["content"][:2500]
        src_type = src.get("type", "web").upper()
        source_blocks.append(f"### SOURCE {i} [{src_type}]: {src['title']}\nURL: {src['url']}\n\n{content}\n")
    sources_text = "\n---\n".join(source_blocks)

    prompt = PROMPT_TEMPLATE.format(
        keyword=keyword,
        dubai_context=DUBAI_CONTEXT,
        sources=sources_text
    )

    print(f"[+] Generating post for: {keyword}")
    print(f"    Using {len(sorted_sources[:12])} sources")
    print(f"    Sending to Claude Sonnet 4...")

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    html = msg.content[0].text

    word_count = len(re.sub(r"<[^>]+>", " ", html).split())
    needs_source_count = html.count("[NEEDS_SOURCE]")

    print(f"\n[i] Word count: {word_count}")
    print(f"[i] [NEEDS_SOURCE] flags: {needs_source_count}")

    if word_count < 1200:
        print("[!] WARNING: word count below 1200")
    if needs_source_count > 2:
        print("[!] WARNING: too many unverified claims (>2)")

    out_path = DRAFTS_DIR / f"{slug}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[+] Draft saved to {out_path}")
    print(f"    Open it: open {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate.py \"your keyword here\"")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    generate_post(keyword)
