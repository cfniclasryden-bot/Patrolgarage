#!/usr/bin/env python3
"""Build /nissan-patrol-abu-dhabi.html — the Abu Dhabi service-area page.

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
SRC = ROOT / "services.html"
OUT = ROOT / "nissan-patrol-abu-dhabi.html"

# Root-level, hyphenated, .html — the site's convention exactly
# (y62-garage-dubai.html, services/y62-major-service-dubai.html). Unchanged.
URL = "https://patrolgarage.ae/nissan-patrol-abu-dhabi.html"
TITLE = "Nissan Patrol Abu Dhabi | Y62 Service &amp; Repair"
# Measured at 14px Arial: stays under ~920px or Google truncates the tail.
DESC = ("Nissan Patrol Y62 service and repair for Abu Dhabi owners. Engine, "
        "gearbox, suspension and diagnostics, with the work done in Mussafah.")
OG_DESC = ("Y62 engine, gearbox, suspension and diagnostic work for Abu Dhabi "
           "owners &mdash; booked on WhatsApp, done in Mussafah.")

HERO = '''<section class="hero">
    <div class="hero-bg">
      <picture>
        <source srcset="images/nissan-patrol-y62-dubai-desert.avif" type="image/avif">
        <img src="images/nissan-patrol-y62-dubai-desert.jpg" alt="Nissan Patrol Y62 in Dubai desert">
      </picture>
    </div>
    <div class="hero-inner">
      <div class="hero-meta">
        <span class="hero-meta-line"></span>
        <span>Y62 Only</span>
        <span>&middot;</span>
        <span>Mussafah</span>
      </div>
      <h1>Nissan Patrol,<br>Abu Dhabi.</h1>
      <p class="hero-lede">
        An Abu Dhabi Y62 no longer has to go to Dubai to be looked at properly. The work is done in Mussafah, on the same one-car basis the rest of this site is about.
      </p>
    </div>
  </section>'''

BODY = '''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 &mdash; How It Works</div>
        <h2>Booked here.<br>Done in<br>Mussafah.</h2>
        <p>Message the symptom, the year and the mileage, and you get a straight answer about what it is likely to be and whether it is worth doing anything about yet. If it is, the work is done in Mussafah, Abu Dhabi's industrial district. There is no walk-in counter and no queue to sit in &mdash; the booking is arranged first, which is also how the car gets looked at on the day it arrives instead of waiting behind three others.</p>
      </div>

      <div class="service-article">
        <h2>What gets looked at</h2>
        <p>The same four systems that bring every Y62 in, and the same order of checking. Engine work on the VK56VD, from a misfire that reads as one thing and is another through to oil consumption and cooling faults. Gearbox work on the JR710E, where fluid condition is the first thing checked every time. HBMC hydraulic suspension, which is unforgiving of conventional parts fitted to save money. And the heat-related faults that only show up here. The full list, with what each job actually involves, is on the <a href="/services.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 service and repair page</a>, and the systems themselves are covered on <a href="/services/nissan-patrol-v8-engine.html" style="text-decoration: underline; text-underline-offset: 3px;">VK56VD engine work</a>, <a href="/services/y62-gearbox-transmission-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 gearbox and transmission work</a> and <a href="/services/y62-major-service-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 major servicing</a>.</p>
      </div>

      <div class="service-article">
        <h2>What to send before you book</h2>
        <p>Four things, and they are worth more than a phone call: what the car is doing, when it started, the mileage, and a short video with the sound in it if there is a noise. A P0300 on a VK56VD can be coils, injectors or a vacuum leak, and those look nothing alike under load &mdash; which is why a code read on its own is not a diagnosis and nobody should quote you from one. Owners who send those four things get told what is likely, what it is not, and what the check involves, before anything is booked.</p>
      </div>

      <div class="service-article">
        <h2>Y62 only, and that is the point</h2>
        <p>This is a Nissan Patrol Y62 business and nothing else. Not a general 4x4 shop, not a garage that takes a Y62 when one turns up. A workshop that sees the same engine, the same gearbox and the same suspension all day recognises a fault before the owner has finished describing it, and that is the entire argument for coming here rather than somewhere closer that will see its first one this month. If you drive something else, this is not the right place and there is no point pretending otherwise. Worth reading first if you are weighing it up: <a href="/blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 specialist, Abu Dhabi vs Dubai</a>, and the <a href="/blog/nissan-patrol-y62-problems-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 problems guide</a> for the faults that actually recur.</p>
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Abu%20Dhabi%20Y62%20-%20my%20Patrol%20is" target="_blank" rel="noopener" class="btn btn-primary">Ask about your Y62</a>
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

# Anything here appearing in the built page is a bug, not a style choice.
BANNED = [
    ("AED", "price"), ("warranty", "warranty"), ("guarantee", "warranty"),
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
                  '<meta name="keywords" content="nissan patrol abu dhabi, nissan patrol y62 abu dhabi, '
                  'y62 service abu dhabi, patrol gearbox abu dhabi, y62 engine abu dhabi">', html, count=1)
    html = re.sub(r'<link rel="canonical" href=".*?">',
                  f'<link rel="canonical" href="{URL}">', html, count=1)
    html = re.sub(r'<meta property="og:title" content=".*?">',
                  '<meta property="og:title" content="Nissan Patrol Abu Dhabi | Y62 Service &amp; Repair">', html, count=1)
    html = re.sub(r'<meta property="og:description" content=".*?">',
                  f'<meta property="og:description" content="{OG_DESC}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content=".*?">',
                  f'<meta property="og:url" content="{URL}">', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content=".*?">',
                  '<meta name="twitter:title" content="Nissan Patrol Abu Dhabi | Y62 Service &amp; Repair">', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content=".*?">',
                  f'<meta name="twitter:description" content="{OG_DESC}">', html, count=1)
    html = re.sub(r'<script type="application/ld\+json">.*?</script>', SCHEMA, html, count=1, flags=re.S)
    html = re.sub(r'<section class="hero">.*?</section>', HERO, html, count=1, flags=re.S)
    start = html.index('<section class="dark">')
    end = html.index('<section class="cta-banner">')
    html = html[:start] + BODY + "\n\n  " + html[end:]
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
