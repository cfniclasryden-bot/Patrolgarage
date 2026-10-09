#!/usr/bin/env python3
"""Build /nissan-patrol-abu-dhabi.html — the Abu Dhabi hub (service-area page).

Upgraded to the hub 2026-10-09: Y62-led title and H1, areas served, the
ownership questions (reliability, what drives upkeep, long-term ownership) in
copy and FAQPage schema, and Mussafah WhatsApp routing (ad_city.py).

Sibling of build_y62_garage_page.py and built the same way: from the
services.html shell, so header, nav, mobile menu, WhatsApp float, CTA banner,
footer, GA4 and Clarity are identical to the rest of the site and cannot drift.
Only the head metadata, hero and main content differ. Idempotent.

WHY THIS PAGE IS A SERVICE-AREA PAGE AND NOT A BRANCH PAGE
----------------------------------------------------------
This site has NO premises, in Abu Dhabi or anywhere. It books the work and a
partner workshop fulfils it. That is the same decision commit 89a64ee acted on
when it stripped address, geo and openingHoursSpecification from 39 schema
blocks; re-introducing any of them for a second emirate would rebuild the exact
claim that pass removed, somewhere harder to defend.

So this page carries, deliberately and permanently:
    NO street address        NO opening hours        NO map or directions
    NO geo coordinates       NO "our workshop"       NO walk-in invitation
Schema is the site's standard shape: AutoRepair + name + telephone + areaServed
+ makesOffer. Abu Dhabi is added to areaServed. Nothing else changes.

Mussafah is named ONLY as where the work is done, never as somewhere this
business is. The distinction is the whole point and the site already has the
correct construction on contact.html: "The work is done in Ras Al Khor, Dubai's
workshop district." That sentence names a district without claiming a building.
Copy it. Do NOT copy the homepage's "our Ras Al Khor workshop" or "we've built
our workshop in Ras Al Khor" — those are the residue 89a64ee did not reach and
they are the wrong model for this page.

THE PARTNER WORKSHOP IS NEVER NAMED OR LINKED. Not in copy, not in schema, not
in a meta tag. Owner instruction, 2026-08-21, not a preference to re-litigate.

KEYWORD BASIS, DataForSEO UAE (location 2784), pulled 2026-09-06:
    nissan patrol abu dhabi ............... 140/mo   <- what this page targets
    nissan service center abu dhabi ....... 320/mo   (dealer intent, adjacent)
    garage mussafah / car repair mussafah . 110/mo each, ALL-CAR, not targeted
    every Y62/Patrol + Abu Dhabi variant .. 0/mo
    nissan patrol mussafah ................ 0/mo
So the page targets the one term with demand and does not chase the Mussafah
all-car volume a Y62-only business cannot serve.

SEPARATION. There is a second site in this niche that has premises in Mussafah
and, since 2026-09-06, a branch page for it. It owns the address vocabulary the
way it owns Ras Al Khor's; see the SERP POSITIONING comment in index.html for
the history of the two reading as one business. This page therefore avoids its
structure and phrasing on purpose: different H1 shape, different section
headings, and no "workshop in Mussafah" construction anywhere.

No prices, no warranty language, no "approved" or "certified", no capability
this business has not confirmed. Same rules as every other page here.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ad_city  # noqa: E402

SRC = ROOT / "services.html"
OUT = ROOT / "nissan-patrol-abu-dhabi.html"

# Root-level, hyphenated, .html — the site's convention exactly
# (y62-garage-dubai.html, services/y62-major-service-dubai.html). Unchanged.
URL = "https://patrolgarage.ae/nissan-patrol-abu-dhabi.html"

# 2026-10-09: upgraded to the Abu Dhabi hub. Title and H1 are built around
# "Nissan Patrol Y62 Abu Dhabi"; the page now answers the ownership questions
# GSC shows this site getting Abu Dhabi impressions for (10 Sep - 7 Oct 2026):
#   how much does nissan patrol maintenance cost in abu dhabi?  pos 4.1
#   is the nissan patrol reliable for long-term ownership in abu dhabi?  pos 5.3
#   is the nissan patrol expensive to maintain in abu dhabi?  pos 2.0
# Those landed on Dubai posts; the hub now answers them directly, in copy and
# in FAQPage schema, with no price, figure, interval or premises claim.
TITLE = "Nissan Patrol Y62 Abu Dhabi | Reliability, Upkeep, Repair"
OG_TITLE = "Nissan Patrol Y62 Abu Dhabi"
DESC = ("Nissan Patrol Y62 in Abu Dhabi: how reliable it is, what drives the cost "
        "of keeping one, and how work is booked. The work is carried out in Mussafah.")
OG_DESC = ("Owning a Y62 in Abu Dhabi: reliability, what drives upkeep, and how "
           "work is booked. The work is carried out in Mussafah.")

AREAS = ("Abu Dhabi island, Al Reem Island, Al Raha, Yas Island, Khalifa City, "
         "Mohammed Bin Zayed City, Shakhbout City and Baniyas")

LINK = 'style="text-decoration: underline; text-underline-offset: 3px;"'

HERO = '''<section class="hero">
    <div class="hero-bg">
      <picture>
        <source srcset="images/nissan-patrol-y62-dubai-desert.avif" type="image/avif">
        <img src="images/nissan-patrol-y62-dubai-desert.jpg" alt="Nissan Patrol Y62 in the desert">
      </picture>
    </div>
    <div class="hero-inner">
      <div class="hero-meta">
        <span class="hero-meta-line"></span>
        <span>Y62 Only</span>
        <span>&middot;</span>
        <span>Abu Dhabi</span>
      </div>
      <h1>Nissan Patrol Y62,<br>Abu Dhabi.</h1>
      <p class="hero-lede">
        Owning a Y62 in Abu Dhabi: how reliable it is, what drives the cost of keeping one, and how work gets booked. The work is carried out in Mussafah.
      </p>
    </div>
  </section>'''

# (question, answer) pairs. Rendered visibly AND as FAQPage JSON-LD from this
# one list, so the two cannot drift. Plain text only: no quotes, no figures.
FAQS = [
    ("How much does Nissan Patrol maintenance cost in Abu Dhabi?",
     "It depends on the car more than the city. What moves the cost is the mileage, how the car "
     "has been used (long highway runs, short trips in summer heat, or desert driving), whether "
     "genuine or aftermarket parts go in, and whether a fault is caught early or left until it "
     "becomes a bigger job. Patrol Garage quotes per car once it has the symptom, the year and "
     "the mileage, so there is no price list here."),
    ("Is the Nissan Patrol reliable for long-term ownership in Abu Dhabi?",
     "Yes, when it is maintained for the conditions. The VK56VD V8 is a durable engine. The parts "
     "to watch on a Y62 kept in Abu Dhabi are the ones heat and sand work hardest: the condition "
     "of the JR710E gearbox fluid, the cooling system, the AC and, on trims that have it, the HBMC "
     "hydraulic suspension. A car with a clear service history is a better long-term prospect "
     "than one with lower mileage and no records."),
    ("Is the Nissan Patrol expensive to maintain in Abu Dhabi?",
     "Upkeep follows from how the car is kept more than from where it lives. A Y62 that has its "
     "fluids changed on time and small faults dealt with early costs less to keep than one that "
     "reaches a gearbox or cooling repair because a symptom was ignored. Large wheels and tyres, "
     "the HBMC suspension on higher trims and a large petrol V8 are what set it apart from a "
     "smaller SUV."),
    ("Where is the work carried out for Abu Dhabi owners?",
     "In Mussafah. The booking is arranged first, on WhatsApp or by phone. There is no walk-in "
     "counter."),
]

FAQ_HTML = "\n".join(
    f'''        <div class="faq">
          <h3>{q}</h3>
          <p>{a}</p>
        </div>''' for q, a in FAQS)

BODY = f'''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 · Booking</div>
        <h2>Booked here.<br>Done in<br>Mussafah.</h2>
        <p>Message the symptom, the year and the mileage, and you get a straight answer about what it is likely to be and whether it needs doing yet. If it does, the work is carried out in Mussafah, Abu Dhabi's industrial district. There is no walk-in counter: the booking is arranged first.</p>
      </div>

      <div class="service-article">
        <h2>Areas served</h2>
        <p>Y62 owners across Abu Dhabi: {AREAS}.</p>
      </div>

      <div class="service-article">
        <h2>How reliable is a Y62 in Abu Dhabi?</h2>
        <p>The Y62 is a durable car, and what decides how it holds up in Abu Dhabi is whether it is maintained for the conditions it actually lives in. Summer heat works the cooling system and the AC hardest. Long highway runs keep the JR710E gearbox at temperature for hours, which is why its fluid condition matters more than its mileage. Fine sand finds its way into filters and seals. On higher trims the HBMC hydraulic suspension needs parts made for it, not conventional substitutes. The faults that recur on the car are set out in the <a href="/blog/nissan-patrol-y62-problems-dubai.html" {LINK}>Y62 problems guide</a>, and the gearbox on its own in <a href="/services/y62-gearbox-transmission-dubai.html" {LINK}>Y62 gearbox and transmission work</a>.</p>
      </div>

      <div class="service-article">
        <h2>What drives the cost of keeping one</h2>
        <p>No price list, because the same job costs different amounts on different cars. What moves it: whether genuine or aftermarket parts go in, how much labour the job takes, whether a part can be repaired or has to be replaced, and above all whether a symptom was dealt with early. A fluid service caught in time is a small job; the gearbox rebuild that follows a neglected one is not. How the car is used matters too: highway miles, short trips in the heat and weekends in the sand each wear different parts. The <a href="/blog/nissan-patrol-service-cost-dubai.html" {LINK}>Patrol service cost guide</a> walks through what each service covers, and <a href="/blog/nissan-patrol-major-service.html" {LINK}>what a major service includes</a> explains the biggest routine job on the car.</p>
      </div>

      <div class="service-article">
        <h2>Owning one for the long term</h2>
        <p>A Y62 kept for years in Abu Dhabi is mostly a question of records and early attention. Keep the service history, deal with a new noise or a warning light when it appears, and have the gearbox fluid, cooling system and suspension checked rather than assumed. If you are buying, a car with a full history is a better prospect than a cleaner one without. The <a href="/blog/nissan-patrol-y62-dubai-complete-guide.html" {LINK}>Y62 owner's guide</a> covers trims and what to look for, and <a href="/blog/nissan-patrol-high-mileage.html" {LINK}>the high-mileage Patrol guide</a> covers what changes as the kilometres build up.</p>
      </div>

      <div class="service-article">
        <h2>What gets looked at</h2>
        <p>The same four systems, checked in the same order. The VK56VD, where a misfire reads as one thing and turns out to be another, and where oil consumption and cooling faults often arrive together. Gearbox work on the JR710E, where fluid condition is the first thing checked every time. HBMC hydraulic suspension, which is unforgiving of conventional parts fitted to save money. And the heat-related faults that only show up here. The full list, with what each job actually involves, is on the <a href="/services.html" {LINK}>Y62 service and repair page</a>, and the systems themselves are covered on <a href="/services/nissan-patrol-v8-engine.html" {LINK}>VK56VD engine work</a> and <a href="/services/y62-major-service-dubai.html" {LINK}>Y62 major servicing</a>.</p>
      </div>

      <div class="service-article">
        <h2>What to send before you book</h2>
        <p>Four things, and they are worth more than a phone call: the mileage, what the car started doing, roughly when you first noticed it, and a clip with the noise audible if there is one. A P0300 on a VK56VD can be coils, injectors or a vacuum leak, and those look nothing alike under load &mdash; which is why a code read on its own is not a diagnosis and nobody should quote you from one. Send those four things and you get told what is likely, what it is not, and what the check involves, before anything is booked.</p>
      </div>

      <div class="service-article">
        <h2>Y62 only, and that is the point</h2>
        <p>This is a Nissan Patrol Y62 business and nothing else. Not a general 4x4 shop, not a garage that takes a Y62 when one turns up. A bench that only ever opens one engine, one gearbox and one suspension layout reaches the likely cause faster than one working it out from a manual. If you drive something else, this is not the right place and there is no point pretending otherwise. Worth reading if you are weighing it up: <a href="/blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html" {LINK}>Y62 specialist, Abu Dhabi vs Dubai</a>.</p>
      </div>

      <div class="service-article">
        <h2>Abu Dhabi owners ask</h2>
{FAQ_HTML}
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Mussafah%3A%20Abu%20Dhabi%20Y62%20-%20my%20Patrol%20is%20" target="_blank" rel="noopener" class="btn btn-primary">Ask about your Y62</a>
      </div>
    </div>
  </section>'''

# Same shape as every other page on this site: AutoRepair, name, telephone,
# areaServed, makesOffer. NO address, NO geo, NO openingHoursSpecification —
# see the module docstring. Abu Dhabi joins areaServed; nothing else changes.
SCHEMA = '''<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "AutoRepair",
    "name": "Patrol Garage Dubai",
    "description": "Nissan Patrol Y62 service and repair for owners in Abu Dhabi.",
    "url": "https://patrolgarage.ae/nissan-patrol-abu-dhabi.html",
    "telephone": "+971585143634",
    "areaServed": [
      { "@type": "City", "name": "Abu Dhabi" },
      { "@type": "City", "name": "Dubai" },
      { "@type": "City", "name": "Sharjah" }
    ],
    "makesOffer": {
      "@type": "Offer",
      "itemOffered": {
        "@type": "Service",
        "name": "Nissan Patrol Y62 service and repair"
      }
    }
  }
  </script>'''


def faq_schema():
    import json
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}
    return ('<script type="application/ld+json">\n'
            + json.dumps(data, indent=2, ensure_ascii=False) + "\n  </script>")


# Anything here appearing in the built page is a bug, not a style choice.
BANNED = [
    ("AED", "price"), ("dirham", "price"), ("warranty", "warranty"), ("guarantee", "warranty"),
    ("approved", "approval claim"), ("certified", "approval claim"),
    ("opening hours", "hours"), ("Business Hours", "hours"),
    ("streetAddress", "address"), ("openingHoursSpecification", "hours"),
    ("Top Challenger", "partner workshop"), ("topchallenger", "partner workshop"),
    ("our Mussafah", "premises claim"), ("our workshop in Mussafah", "premises claim"),
    ("workshop in Mussafah", "premises claim"),
]


def build():
    html = SRC.read_text(encoding="utf-8")
    html = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", html, count=1)
    html = re.sub(r'<meta name="description" content=".*?">',
                  f'<meta name="description" content="{DESC}">', html, count=1)
    html = re.sub(r'<meta name="keywords" content=".*?">',
                  '<meta name="keywords" content="nissan patrol y62 abu dhabi, nissan patrol abu dhabi, '
                  'nissan patrol reliability abu dhabi, nissan patrol maintenance cost abu dhabi, '
                  'nissan patrol long term ownership abu dhabi">', html, count=1)
    html = re.sub(r'<link rel="canonical" href=".*?">',
                  f'<link rel="canonical" href="{URL}">', html, count=1)
    html = re.sub(r'<meta property="og:title" content=".*?">',
                  f'<meta property="og:title" content="{OG_TITLE}">', html, count=1)
    html = re.sub(r'<meta property="og:description" content=".*?">',
                  f'<meta property="og:description" content="{OG_DESC}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content=".*?">',
                  f'<meta property="og:url" content="{URL}">', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content=".*?">',
                  f'<meta name="twitter:title" content="{OG_TITLE}">', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content=".*?">',
                  f'<meta name="twitter:description" content="{OG_DESC}">', html, count=1)
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  lambda _m: SCHEMA + "\n  " + faq_schema(), html, count=1, flags=re.S)
    # services.html's own first-screen stylesheet; this page carries the Abu
    # Dhabi ask instead (ad_city.apply_routing, below).
    html = re.sub(r'<style id="pg-ask-css">.*?</style>\n?', "", html, flags=re.S)
    html = re.sub(r'<section class="hero">.*?</section>', HERO, html, count=1, flags=re.S)
    start = html.index('<section class="dark">')
    end = html.index('<section class="cta-banner">')
    html = html[:start] + BODY + "\n\n  " + html[end:]
    # Mussafah routing (2026-10-09): the Abu Dhabi ask under the H1 with labels
    # pg-ad-wa / pg-ad-wa-ar / pg-ad-call, and every WhatsApp pre-fill on the
    # page starting "Mussafah:".
    html = ad_city.apply_routing(html)
    # The FAQ questions need air above them; services.html has no FAQ styles.
    html = html.replace("</head>", '<style id="pg-ad-faq-css">.service-article .faq h3'
                        '{margin:1.75rem 0 .6rem}</style>\n</head>', 1)
    OUT.write_text(html, encoding="utf-8")
    return html


def main():
    html = build()
    import json
    ok = 0
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        json.loads(m.group(1)); ok += 1
    print(f"[OK] {OUT.name} written ({len(html):,} bytes), {ok} ld+json block(s) valid")
    fails = [(t, why) for t, why in BANNED if re.search(re.escape(t), html, re.I)]
    for t, why in fails:
        print(f"[!] BANNED ({why}): {t!r} appears in the built page")
    print(f"     banned-term check: {'FAIL' if fails else 'clean'} ({len(BANNED)} terms)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
