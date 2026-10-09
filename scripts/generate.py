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
- Y61: still sold as the Super Safari in the GCC. Comparison and owner
  information only: Patrol Garage does not work on it
- Y62: launched 2010 in UAE, sold with VK56VD 5.6L V8. See MODEL YEARS below:
  there was NO 2016 facelift
- Y63: the current model, a twin-turbo V6. Owner information only
- Y62 transmission: 7-speed automatic (Jatco JR710E / RE7R01A)
- Y62 engine: VK56VD 5.6L V8 (state no horsepower or torque figure)
- Common trims in UAE: SE, XE, LE, Platinum, Nismo

DUBAI CLIMATE:
- Summer temperatures 45-50°C ambient, 70°C+ tarmac
- Sand and dust ingress, salt humidity along coast
- Heavy stop-and-go on Sheikh Zayed Road, Sheikh Mohammed Bin Zayed Road
- Off-road usage common (Al Qudra, Big Red, Liwa)

PRICING — HARD RULE, NO EXCEPTIONS (2026-10-05; the same rule as the sister site):
- Do NOT state, estimate, imply or hint at any price. Not ours, not a dealer's,
  not "the market's".
- This bans: any AED or dirham amount; any range ("AED 3,000 to 6,000", "between
  2k and 5k"); any "from" / "starting at" / "as low as"; any hourly labour rate,
  labour total, parts price or job total; any percentage saving or numeric price
  comparison ("20 to 35 percent lower", "half the dealer price"); any figure in
  another currency. A pre-publish check blocks the post if one appears.
- Where a price would normally go, describe what DRIVES the cost instead (parts
  vs labour, repair vs replace, how long the job takes, what the diagnosis finds)
  and point the reader to WhatsApp for a quote on their car.
- A keyword may well contain "cost" or "price". Answer the intent by explaining
  what the job involves and what moves the cost, never with a number.

INDEPENDENT WORKSHOP AREAS (market context only, NOT where Patrol Garage is):
Ras Al Khor, Al Quoz, Deira/Al Aweer, Sharjah Industrial

WHAT PATROL GARAGE DOES AND DOES NOT SELL — this overrides the keyword, the
research notes, and anything the topic seems to invite.

OFFERED (you may write "we", "our", "at the workshop", "bring it to us"):
- engine diagnostics and repair
- gearbox and transmission work
- suspension and HBMC repair (worn shocks, accumulators, bushes)
- AC service and repair
- electrical and diagnostic work
- brakes, tyres and batteries
- periodic servicing and maintenance
The workshop services the Y62. Y61 and Y63 are owner information only.

NOT OFFERED. Never attach "we", "our", "at the workshop", "book", "bring it to
us", or a quote invitation to any of these:
- pre-purchase inspections (PPI). Buyers should get one INDEPENDENTLY.
- lift kits, suspension lifts, ride-height or body-height changes
- performance modifications, turbo kits, ECU tuning, engine or exhaust
  modification
- paint protection film, wraps, tinting, accessory fitting

Write all of the above in the THIRD PERSON, as owner information. This is the
single most common failure in this pipeline, so be literal about it:

  GOOD: "A thorough pre-purchase inspection covers 30+ points."
  GOOD: "Ask any independent specialist for an itemised quote before work starts."
  BAD:  "At the workshop we run through the following on every inspection."
  BAD:  "Book a full inspection and we will go through it systematically."
  BAD:  "Lift kit installation adds 4 to 8 hours of labour."

An ownership or buying keyword does NOT license an offer. Write the buyer's
guide, then point them to an independent inspection, then offer only the repair
work above.

Never state a price of any kind. See PRICING above: we quote per job.

MODEL YEARS AND GENERATIONS — HARD RULE (added 2026-10-05):
There was NO 2016 facelift of the Y62, and an earlier version of this list said
there was. On the sister site the same invention grew into a whole taxonomy of
"pre-2016" and "post-2016" cars across five posts. A pre-publish check now
BLOCKS the post if it finds any of these, so do not write them:
  - "facelift", "pre-facelift", "post-facelift", or any named facelift year
  - "pre-" or "post-" followed by a year, except 2010 and 2020
  - "earlier cars", "later cars", "newer cars", "older cars"
  - "from", "since", "until", "before" or "after" followed by a year, except
    2010 and 2020
Describe a car by its mileage and service history instead of its build year.

FLUID GRADES, CAPACITIES, SERVICE INTERVALS AND THE OWNER'S MANUAL — HARD RULE,
NO EXCEPTIONS (added 2026-10-05):
Do not state any fluid grade or viscosity (0W-20, 5W-30, any ATF, gear oil or
coolant grade), any fill capacity, or any service or change interval in
kilometres, miles or months. Do not attribute anything to an owner's manual and
do not mention an owner's manual at all. Do not attribute any figure to Nissan,
the manufacturer, the factory, a dealer schedule, a specification or an "OEM"
figure. This covers the workshop's own figures too.
The ONLY exception is one of these sentences, copied WORD FOR WORD as a sentence
on its own, with nothing paraphrased, shortened, extended or changed:
<<ACCEPTED_SENTENCES>>
If none of them says what you need, leave the figure out and explain what the
job protects and what to watch for instead. A pre-publish check blocks any
figure credited to an authority this site cannot produce.

NO EDITORIAL MARKERS: never write [NEEDS_SOURCE], TODO, TK or any other
placeholder. This post is published unattended and a marker in the copy blocks
it. If a claim needs a source you do not have, leave the claim out."""


# The approved sentences live in check_claims.ACCEPTED_SENTENCES, beside the
# fragments the guard matches, so the prompt and the guard cannot drift apart.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_claims  # noqa: E402
import ad_city  # noqa: E402
DUBAI_CONTEXT = DUBAI_CONTEXT.replace(
    "<<ACCEPTED_SENTENCES>>",
    "\n".join(f'  - "{s}"' for s in check_claims.ACCEPTED_SENTENCES))


AUTHORITATIVE_LINKS = [
    "https://rta.ae",
    "https://www.dubai.ae",
    "https://u.ae",
    "https://moccae.gov.ae",
    "https://www.dubaipolice.gov.ae",
    "https://www.ead.gov.ae",
    # consumer.gov.ae stopped resolving (NXDOMAIN, checked 2026-08-12). The UAE
    # consumer-protection material now lives on the government portal.
    "https://u.ae/en/information-and-services/justice-safety-and-the-law/consumer-protection",
]

PROMPT_TEMPLATE = """You are writing an AIO-ready blog post for Patrol Garage, a Nissan Patrol specialist service for owners in Dubai. Target audience: Patrol owners in the UAE searching for help.

NO PREMISES — HARD RULE: Patrol Garage books the work and has no premises of its own: never write that it has a workshop, garage, facility or location anywhere, never give an address, district, opening hours or directions for it, and never say where it is based. "Bring it to us" and "message us" are fine.

NO CROWD COUNTS OR FIRST-HAND OBSERVATIONS — HARD RULE:
The claims check blocks both (copy_rules CROWD / FIRST_HAND, 2026-10-09). Never "hundreds of Patrols ...",
"thousands of owners ...", "most owners ...", "many Patrols ...", "the ones we
see", "we often see", "we often find", "we regularly see", "in our experience",
"most cars we get". Nobody counted, and the site cannot vouch for a caseload.
  BAD:  "Cars with late fluid changes are the ones we see with valve body wear."
  GOOD: "Fluid left too long between changes can contribute to valve body wear."

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
   - Then expand with details, what drives the cost (never a figure), mileage, Dubai context

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
     <p><strong>Need help with your Patrol?</strong> Call us on +971 58 514 3634 or <a href="/contact.html">request a quote</a>.</p>
   </div>

REQUIREMENTS:
- Length: 1500-2200 words
- Tone: conversational expert. First-person plural ("we see", "we recommend").
- Cite specific details: mileage, part names, what drives the cost. NO prices (see PRICING). Use Dubai context facts above. NOT model years beyond the MODEL YEARS rule, and NOT fluid grades, capacities or service intervals (see the HARD RULE).
- AUTHORITATIVE SOURCES REQUIREMENT: You MUST include at least 2 outbound links to government or research authorities in the article body. Naturally integrate them where a fact is stated that benefits from a citation.

  Approved authoritative sources for this site:
{authoritative_links}

  Use the exact URLs. Embed as inline links naturally in prose — e.g. 'Per <a href="https://rta.ae">the RTA</a>, all vehicles in Dubai require annual inspection...' Do NOT include them as a footnote list. Minimum 2 distinct sources per article.
- Never write [NEEDS_SOURCE] or any other marker. See NO EDITORIAL MARKERS above.
- Use the ° symbol (not Â°). Do NOT use em dashes (—) or en dashes (–) anywhere. Use a period, comma, colon, or parentheses instead.

HUMAN-VOICE RULES (write clean on the first pass so the copy reads like a real Dubai Patrol mechanic wrote it, not a chatbot):
- No em or en dashes anywhere (restated for emphasis). Scan the output and replace every — or – with a period, comma, colon, or parentheses before returning.
- No promotional filler. Do not use: renowned, nestled, stunning, vibrant, seamless, robust, world-class, cutting-edge, must-visit, commitment to, in the heart of. Describe the car and the work plainly.
- Ban these AI-tell words: crucial, vital, pivotal, testament, landscape (figurative), delve, underscore, foster, elevate, enhance, unlock, realm, ever-evolving. Use the plain equivalent.
- Use "is / are / has". Do not write "serves as / boasts / features / offers a" in place of a simple verb.
- No forced groups of three. List as many real symptoms, causes, or costs as actually exist, not a tidy trio for rhythm.
- No "-ing" filler tails ("...ensuring optimal performance", "...highlighting the importance of regular servicing"). End the sentence on the concrete fact.
- No signposting ("Let's dive in", "Here's what you need to know") and no generic upbeat closer ("keep your Patrol running smoothly for years to come"). End on a specific next step or fact.
- Vary sentence length. Mix short sentences with longer ones. Avoid an even, mid-length cadence.
- When a claim needs authority, link one of the approved sources inline. Never write "experts recommend" or "studies show" without a real link.
- Headings in sentence case, not Title Case (the question-phrased H2s already fit this).

PROTECT THE AIO STRUCTURE (these override the voice rules — never strip them):
- Keep the direct-answer <div> and its <strong>, the FAQ <h3> question blocks, and the CTA <strong> exactly as specified above.
- Keep every specific identifier (mileage, engine/part names like VK56VD, JR710E). Never a price. Specific detail is the goal, not filler. This never licenses a model year, fluid grade, capacity or interval that the hard rules above forbid.
- Only remove DECORATIVE mid-paragraph bold. Do not bold phrases inside body paragraphs for emphasis.
- Output: HTML body only. Allowed tags: <h1>, <h2>, <h3>, <p>, <ul>, <li>, <strong>, <div>, <a>.
- DO NOT include image placeholders, image markdown, [HERO IMAGE], [IMAGE], <img>, or any image references. Images are added separately by the pipeline. Just write the text body.
- Return ONLY the HTML body. No preamble, no markdown fences."""


def retry_block():
    """The prompt addition for a regenerate after check_claims blocked a draft.

    run_pipeline.py sets GATE_FEEDBACK to the flagged sentences, one per line,
    and re-runs this script once. An environment variable rather than a flag
    because every argument here is joined into the keyword. Unset, this
    returns "" and the prompt is unchanged. Same as topchallenger-site.
    """
    flagged = [s.strip() for s in os.environ.get("GATE_FEEDBACK", "").splitlines()
               if s.strip()]
    if not flagged:
        return ""
    lines = "\n".join(f'  - "{s}"' for s in flagged)
    return (
        "\n\nRETRY. A DRAFT OF THIS POST WAS BLOCKED BEFORE PUBLISHING.\n"
        "The claims check stopped the previous draft on the sentence(s) below. "
        "Each one either credited a figure to an authority this site cannot produce, "
        "or claimed something nobody can verify: a crowd or volume count "
        "(\"hundreds of Patrols ...\", \"most owners ...\", \"many Patrols ...\") or a "
        "first-hand workshop observation (\"the ones we see\", \"we often find\", "
        "\"in our experience\"). For those, state the mechanism in general terms, "
        "with no count and no observation. "
        "REMOVE these claims. Do not write these sentences, any rewording of "
        "them, or any other sentence making the same claim, anywhere: not in "
        "the body, the FAQ, the quick answer or the meta description. Do not "
        "restate the figure as the workshop's own instead. The only permitted "
        "form of a grade, capacity, interval or owner's manual mention is an "
        "approved sentence copied word for word, as the hard rule above says. "
        "Every other rule in this prompt still applies.\n" + lines + "\n"
    )


def city_block(slug):
    """Abu Dhabi rules for an Abu Dhabi slug (2026-10-09), "" for every other.

    The reader's car is in Abu Dhabi, so the city goes in the H1 and the quick
    answer, and the one location line is "the work is carried out in Mussafah".
    check_city.py blocks the publish if the output ignores this. Every other
    slug gets "", so its prompt is unchanged.
    """
    rules = ad_city.ad_city_rules_for(slug)
    return ("\n\nCITY FOR THIS POST: sits alongside the rules above, does not replace them.\n"
            + rules + "\n") if rules else ""


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
        current_month_year=current_month_year,
        authoritative_links="\n".join(f"  - {u}" for u in AUTHORITATIVE_LINKS),
    ) + city_block(slug) + retry_block()

    print(f"[+] Generating post for: {keyword}")
    print(f"    Using {len(sorted_sources[:12])} sources")
    print(f"    Sending to Claude Sonnet 4...")

    msg = client.messages.create(
        model="claude-sonnet-4-6",
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

    # Strip any image placeholder text the AI may have written
    import re as _re
    placeholder_patterns = [
        r"\[\s*HERO\s*IMAGE\s*\]",
        r"\[\s*IMAGE[^\]]*\]",
        r"<!--\s*IMAGE[^>]*-->",
        r"<img[^>]*>",
        r"!\[[^\]]*\]\([^)]*\)",
    ]
    for pat in placeholder_patterns:
        before = len(html)
        html = _re.sub(pat, "", html, flags=_re.IGNORECASE)
        if len(html) < before:
            print(f"[+] Stripped image placeholder matching: {pat}")
    html = _re.sub(r"<p>\s*</p>", "", html)
    html = _re.sub(r"\n\s*\n\s*\n", "\n\n", html)

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
