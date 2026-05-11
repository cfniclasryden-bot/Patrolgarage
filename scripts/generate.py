#!/usr/bin/env python3
"""generate.py — turn research JSON into AIO-ready blog post draft"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
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

DUBAI CLIMATE:
- Summer temperatures 45-50°C ambient, 70°C+ tarmac
- Sand and dust ingress, salt humidity along coast
- Heavy stop-and-go on Sheikh Zayed Road, Sheikh Mohammed Bin Zayed Road
- Off-road usage common (Al Qudra, Big Red, Liwa)

TYPICAL UAE WORKSHOP PRICING (plausible ranges):
- Major service: AED 800-2,500
- Transmission fluid change: AED 600-1,200
- Transmission rebuild: AED 8,000-18,000
- Transmission replacement (used): AED 12,000-25,000
- Engine rebuild: AED 15,000-35,000
- AC compressor replacement: AED 2,500-5,000
- Suspension overhaul: AED 4,000-12,000
- Pre-purchase inspection: AED 400-800

WORKSHOP AREAS: Ras Al Khor, Al Quoz, Deira/Al Aweer, Sharjah Industrial

You can reference any facts naturally. Only flag [NEEDS_SOURCE] for very specific data 
(named workshop quote, specific recall number, exact dealer interval)."""


PROMPT_TEMPLATE = """You are writing an AIO-ready blog post for Patrol Garage, a Nissan Patrol specialist workshop in Dubai (Ras Al Khor). Target audience: Patrol owners in the UAE searching for help.

TARGET KEYWORD: {keyword}

{dubai_context}

SOURCE MATERIAL:
---
{sources}
---

THIS POST MUST BE STRUCTURED FOR AI OVERVIEW AND LLM CITATION. Structure exactly:

1. **H1** with target keyword

2. **Direct Answer block** (FIRST thing after H1): 
   <div class="direct-answer">
     <p><strong>Quick answer:</strong> 2-3 sentence direct answer to the keyword query with specific facts and numbers. This is what AI Overviews will cite.</p>
   </div>

3. **Evidence/Context paragraph** (200-250 words intro that hooks the reader)

4. **5-7 H2 sections** covering the full query cluster. Each H2 should:
   - Be phrased as a question when natural (e.g., "What Causes Y62 Transmission Failure in Dubai?")
   - Have a 1-sentence direct answer immediately after the H2
   - Then expand with details, specific AED costs, model years, Dubai context

5. **FAQ section** (H2: "Frequently Asked Questions") with exactly 4 Q&A pairs in this format:
   <div class="faq">
     <h3>Question phrased exactly as someone would type it?</h3>
     <p>2-4 sentence direct answer with specific facts.</p>
   </div>
   (Schema will be added separately)

6. **Final H2: "When to bring it to Patrol Garage"** with brief CTA

7. **Last updated stamp** at the very end before CTA:
   <p class="last-updated">Last updated: {current_month_year}</p>

8. **CTA block** (exactly this):
   <div class="cta">
     <p><strong>Need help with your Patrol?</strong> Call us on +971 58 221 1201 or <a href="/contact.html">request a quote</a>.</p>
   </div>

REQUIREMENTS:
- Length: 1500-2200 words
- Tone: conversational expert. First-person plural ("we see", "we recommend").
- Cite specific numbers: years, km, AED costs, part names. Use Dubai context facts above.
- Only flag [NEEDS_SOURCE] for very specific named workshop quotes or recall numbers.
- Use ° (not Â°), em-dash — (not â€").
- Output: HTML body only. Allowed tags: <h1>, <h2>, <h3>, <p>, <ul>, <li>, <strong>, <div>.
- Return ONLY the HTML body. No preamble, no markdown fences."""


def generate_post(keyword):
    slug = slugify(keyword)
    research_path = RESEARCH_DIR / f"{slug}.json"

    if not research_path.exists():
        print(f"[!] No research found at {research_path}")
        sys.exit(1)

    with open(research_path, encoding="utf-8") as f:
        research = json.load(f)

    if not research["sources"]:
        print("[i] No sources from research - generating from keyword + Dubai context only.")
        research["sources"] = []

    def source_priority(s):
        return {"forum": 0, "youtube": 1, "web": 2}.get(s.get("type", "web"), 3)
    sorted_sources = sorted(research["sources"], key=source_priority)

    source_blocks = []
    for i, src in enumerate(sorted_sources[:12], 1):
        content = src["content"][:2500]
        src_type = src.get("type", "web").upper()
        source_blocks.append(f"### SOURCE {i} [{src_type}]: {src['title']}\nURL: {src['url']}\n\n{content}\n")
    sources_text = "\n---\n".join(source_blocks)

    current_month_year = datetime.now().strftime("%B %Y")
    prompt = PROMPT_TEMPLATE.format(
        keyword=keyword,
        dubai_context=DUBAI_CONTEXT,
        sources=sources_text,
        current_month_year=current_month_year
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
    has_direct_answer = '<div class="direct-answer">' in html
    has_faq = '<div class="faq">' in html
    has_last_updated = '<p class="last-updated">' in html

    print(f"\n[i] Word count: {word_count}")
    print(f"[i] [NEEDS_SOURCE] flags: {needs_source_count}")
    print(f"[i] Direct answer block: {'✓' if has_direct_answer else '✗ MISSING'}")
    print(f"[i] FAQ block: {'✓' if has_faq else '✗ MISSING'}")
    print(f"[i] Last updated stamp: {'✓' if has_last_updated else '✗ MISSING'}")

    if word_count < 1200:
        print("[!] WARNING: word count below 1200")
    if needs_source_count > 2:
        print("[!] WARNING: too many unverified claims (>2)")

    out_path = DRAFTS_DIR / f"{slug}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[+] Draft saved to {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate.py \"your keyword here\"")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    generate_post(keyword)
