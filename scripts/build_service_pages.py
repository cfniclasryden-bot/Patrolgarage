#!/usr/bin/env python3
"""Build the three service pages under /services/.

Only three, chosen on measured Patrol-qualified demand (DataForSEO, UAE, 2026-08-13).
Suspension and engine-rebuild pages were considered and REJECTED — see below.

  /services/y62-major-service-dubai.html          cluster 160/mo
      nissan patrol service          50/mo HIGH  $ 7.95
      nissan patrol service center   40/mo MED   $ 2.63
      nissan patrol service dubai    20/mo HIGH  $20.43   <- highest CPC on the site
      nissan patrol oil change       10/mo MED   $17.71
      + service cost / major service / maintenance / schedule at 10/mo
    The only cluster where Patrol-qualified demand and commercial value coincide.

  /services/y62-gearbox-transmission-dubai.html   cluster 130/mo
      nissan patrol gearbox          40/mo LOW
      nissan patrol transmission     20/mo LOW
      + 7 terms at 10/mo, nearly all LOW competition
    The site already sits at position 4.0 on "nissan patrol gearbox". Small terms,
    but winnable — LOW competition is the point.
    NOTE: "nissan patrol gearbox repair" is 0/mo. The service phrasing has no
    demand; the demand is on the component noun. The page is titled accordingly.

  /services/nissan-patrol-v8-engine.html          cluster 560/mo
      nissan patrol v8 engine       390/mo LOW  $2.00
      nissan patrol engine          140/mo LOW  $4.21
      y62 engine                     30/mo LOW
    THIS IS NOT A REPAIR PAGE. Every repair phrasing is zero:
      nissan patrol engine repair 0, y62 engine repair 0, vk56vd engine repair 0,
      engine rebuild dubai 0, nissan patrol engine rebuild 10.
    So this targets people RESEARCHING the car, not people shopping for a rebuild.
    It explains the VK56VD honestly and routes readers onward. It does not sell.
    Selling to a research query is what produces 0% CTR, which is exactly what the
    model-name pages already do.

REJECTED: suspension (80/mo, thin, mostly $0 CPC) and engine rebuild/replacement
(30/mo total, with the head term at 0). Building those would be vanity.

MECHANICS. Pages are built from the services.html shell so header, nav, mobile
menu, WhatsApp float, CTA banner, footer, GA4 and Clarity cannot drift. Because
they live one directory down, every RELATIVE url in that shell is rewritten to
root-absolute — otherwise /services/foo.html would request
/services/images/... and /services/blog/... and quietly 404.

No prices anywhere.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "services.html"
OUT_DIR = ROOT / "services"

# Relative paths in the shell -> root-absolute. Order matters: longest first.
REWRITES = [
    ('href="blog/nissan-patrol-y62-dubai-complete-guide.html"', 'href="/blog/nissan-patrol-y62-dubai-complete-guide.html"'),
    ('href="services.html"', 'href="/services.html"'),
    ('href="contact.html"', 'href="/contact.html"'),
    ('href="about.html"', 'href="/about.html"'),
    ('href="blog/"', 'href="/blog/"'),
    ('src="images/', 'src="/images/'),
    ('srcset="images/', 'srcset="/images/'),
]


def hero(tag1, tag2, h1, lede):
    return f'''<section class="hero">
    <div class="hero-bg">
      <picture>
        <source srcset="/images/nissan-patrol-y62-dubai-desert.avif" type="image/avif">
        <img src="/images/nissan-patrol-y62-dubai-desert.jpg" alt="Nissan Patrol Y62 in Dubai">
      </picture>
    </div>
    <div class="hero-inner">
      <div class="hero-meta">
        <span class="hero-meta-line"></span>
        <span>{tag1}</span>
        <span>&middot;</span>
        <span>{tag2}</span>
      </div>
      <h1>{h1}</h1>
      <p class="hero-lede">{lede}</p>
    </div>
  </section>'''


PAGES = [
    {
        "file": "y62-major-service-dubai.html",
        "title": "Nissan Patrol Service in Dubai | Major Service &amp; Maintenance",
        "desc": ("Nissan Patrol service in Dubai: what a major service actually covers on a "
                 "Y62, how often it is due in UAE heat, and what we check every time."),
        "hero": hero("Periodic Service", "Ras Al Khor", "Nissan Patrol<br>Service.",
                     "What a proper Patrol service covers, why the intervals are shorter here than the book says, and what we check every time one comes in."),
        "body": '''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 &mdash; The Service</div>
        <h2>What a Patrol<br>service covers.</h2>
        <p>A Nissan Patrol service is not a generic oil change with the model name on the invoice. The Y62 runs a 5.6-litre VK56VD V8 with its own filter and fluid requirements, a seven-speed Jatco JR710E automatic that is sensitive to fluid condition, and on higher trims a hydraulic body motion control system that has to be checked rather than ignored. A service that skips those is a service in name only.</p>
      </div>

      <div class="service-article">
        <h2>Minor service</h2>
        <p>Engine oil and filter on the correct grade for UAE ambient temperatures, air filter inspection or replacement, cabin filter, brake and coolant level check, tyre condition and pressures, battery health test, and a scan for stored codes. This is the interval most owners in Dubai should be treating as routine, because heat shortens oil life well before the distance figure is reached.</p>
      </div>

      <div class="service-article">
        <h2>Major service</h2>
        <p>Everything in the minor service plus the items that only come round occasionally: spark plugs on the VK56VD, transmission fluid condition assessment and change where due, differential and transfer case oils, brake fluid, coolant condition and a pressure test of the cooling system, drive belt inspection, and a full underbody look for off-road damage. On a Patrol that sees dune work, the underbody check is not optional.</p>
      </div>

      <div class="service-article">
        <h2>Why the interval is shorter in the UAE</h2>
        <p>Ambient temperatures of 45 to 50&deg;C and 70&deg;C tarmac degrade engine oil faster than the schedule in the handbook assumes, and stop-and-go traffic on Sheikh Zayed Road keeps the engine at operating temperature with very little airflow. Sand is the other factor: it packs radiator and condenser cores and shortens air filter life considerably. Most Patrols in Dubai are better served on a shorter rhythm than the book interval, and we will tell you what yours actually needs based on how you drive it.</p>
      </div>

      <div class="section-head" style="margin-top:4rem;">
        <div class="section-num">02 &mdash; Booking</div>
        <h2>Getting it<br>booked in.</h2>
        <p>Send us the year, the mileage and roughly how the car is used, and we will tell you which service it is due for before you come in rather than after. We are in Ras Al Khor and we work on Nissan Patrols only, so the parts are on the shelf and the job does not wait on a dealer order. Full job list on the <a href="/services.html" style="text-decoration: underline; text-underline-offset: 3px;">service menu</a>.</p>
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Patrol%20service%20-%20year%20and%20mileage%3A" target="_blank" rel="noopener" class="btn btn-primary">Ask what yours is due for</a>
      </div>
    </div>
  </section>''',
        "schema_name": "Nissan Patrol service and maintenance",
    },
    {
        "file": "y62-gearbox-transmission-dubai.html",
        "title": "Nissan Patrol Gearbox &amp; Transmission | Y62 JR710E, Dubai",
        "desc": ("Nissan Patrol gearbox and transmission work in Dubai. The Y62's JR710E "
                 "seven-speed: shudder, flare, delayed engagement and fluid condition."),
        "hero": hero("Gearbox", "JR710E", "Patrol Gearbox<br>&amp; Transmission.",
                     "The Y62's seven-speed automatic is the most expensive thing on the car to get wrong. Most of what we see was cheap to fix a year earlier."),
        "body": '''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 &mdash; The Unit</div>
        <h2>The JR710E,<br>and how it fails.</h2>
        <p>The Nissan Patrol Y62 uses a Jatco JR710E seven-speed automatic, also badged RE7R01A. It is a durable unit behind a 5.6-litre V8, and it is unforgiving of neglected fluid. Almost every expensive gearbox job we see started as a symptom the owner noticed months earlier and reasonably assumed would settle down.</p>
      </div>

      <div class="service-article">
        <h2>Shudder under light throttle</h2>
        <p>A vibration that feels like driving over rumble strips, usually at light throttle and steady speed, most often between 60 and 100 km/h. It is typically torque converter lock-up shudder, and at the early stage it is frequently a fluid condition problem rather than a mechanical one. Left alone, the converter contaminates the rest of the unit and a fluid service stops being the answer.</p>
      </div>

      <div class="service-article">
        <h2>Flare between gears</h2>
        <p>Engine revs rise between shifts as if the clutch pack slipped before engaging. On a Patrol this points at line pressure, solenoid response or clutch wear, and the order in which those are checked matters. We read live data and drive the car rather than replacing parts in sequence.</p>
      </div>

      <div class="service-article">
        <h2>Delayed engagement from cold</h2>
        <p>A pause of a second or more between selecting drive and the car actually moving, worst on the first start of the day. It is a classic early warning and one of the cheapest points at which to intervene.</p>
      </div>

      <div class="service-article">
        <h2>Fluid condition first, always</h2>
        <p>Clean red ATF means a healthy unit. Dark, burnt-smelling fluid means it has been running hot and internal wear has already started. Metallic particles mean damage has happened. That single check tells us more about a Y62 gearbox than any code will, and it is the first thing we do. Heat is why this matters more here: Dubai traffic keeps the transmission working hard with little airflow, and a gearbox cooler that is packed with sand is a gearbox running hotter than its designer intended.</p>
      </div>

      <div class="section-head" style="margin-top:4rem;">
        <div class="section-num">02 &mdash; Bring It In</div>
        <h2>Before it gets<br>expensive.</h2>
        <p>If your Patrol is doing any of the above, the useful thing to send us is the symptom, the year and roughly when it started. We will tell you whether it sounds like fluid, solenoid or something that needs the unit out, before the car comes in. Further reading: <a href="/blog/nissan-patrol-y62-transmission-problems-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 transmission problems in Dubai</a>.</p>
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Patrol%20gearbox%20-%20symptom%20and%20year%3A" target="_blank" rel="noopener" class="btn btn-primary">Describe the symptom</a>
      </div>
    </div>
  </section>''',
        "schema_name": "Nissan Patrol gearbox and transmission service",
    },
    {
        "file": "nissan-patrol-v8-engine.html",
        "title": "Nissan Patrol V8 Engine | The VK56VD Explained",
        "desc": ("The Nissan Patrol V8: what the VK56VD is, what it is like to own in the "
                 "UAE, what tends to go wrong and at what age. Owner's reference."),
        "hero": hero("VK56VD", "Owner Reference", "The Nissan<br>Patrol V8.",
                     "What the 5.6-litre VK56VD actually is, how it behaves in UAE heat, and what tends to need attention as it ages."),
        "body": '''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 &mdash; The Engine</div>
        <h2>What the<br>VK56VD is.</h2>
        <p>The Nissan Patrol Y62 is powered by the VK56VD, a 5.6-litre naturally aspirated V8 producing around 400hp. It uses both direct and port injection, variable valve event and lift on the intake side, and a timing chain rather than a belt. It replaced the VK56DE used in earlier applications, and it is the engine in every Y62 sold in the UAE from 2010 until the Y63 arrived in 2024 with a twin-turbo 3.5-litre V6.</p>
        <p>If you are reading this while deciding whether to buy one, the short version is that it is a robust engine with a small number of well-understood habits, and it is not remotely fussy compared with the European V8s in its price range. The rest of this page is what those habits are.</p>
      </div>

      <div class="service-article">
        <h2>Timing chain noise on cold start</h2>
        <p>A brief rattle in the first second or two after a cold start is the thing owners ask about most. On a high-mileage VK56VD it points at chain guide and tensioner wear. It is worth investigating rather than ignoring, because the chain is not a consumable you plan around.</p>
      </div>

      <div class="service-article">
        <h2>Valve cover gaskets</h2>
        <p>They weep with age and heat, and on this engine the oil lands on hot exhaust components, which is where the burning smell after a drive usually comes from. Straightforward to deal with, unpleasant to leave.</p>
      </div>

      <div class="service-article">
        <h2>Coils, injectors and the generic misfire</h2>
        <p>A stored P0300 on this engine means "something is misfiring", not "here is the fault". It can be coils, injectors or a vacuum leak, and those look nothing alike under load. Diagnosis needs live data and a road test rather than a code read, which is why parts-swapping on a VK56VD gets expensive quickly.</p>
      </div>

      <div class="service-article">
        <h2>Oil consumption and heat</h2>
        <p>Owners often notice consumption before any warning light appears. Ambient temperatures of 45 to 50&deg;C degrade oil faster than the handbook interval assumes, and a V8 sitting in Sheikh Zayed Road traffic is at operating temperature with almost no airflow. Checking the level between services is worth the thirty seconds.</p>
      </div>

      <div class="section-head" style="margin-top:4rem;">
        <div class="section-num">02 &mdash; Where To Next</div>
        <h2>Reading on,<br>by topic.</h2>
        <p>If you are researching the car generally, the <a href="/blog/nissan-patrol-y62-dubai-complete-guide.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 owner's guide</a> covers generations, trims and what to check before buying. If something specific is happening to yours, the <a href="/blog/nissan-patrol-y62-problems-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">common Y62 problems</a> page is organised by symptom, and <a href="/blog/nissan-patrol-overheating-dubai-summer-fix.html" style="text-decoration: underline; text-underline-offset: 3px;">overheating in Dubai summer</a> covers the cooling side.</p>
        <p>We are a Nissan Patrol workshop in Ras Al Khor, so if you do end up needing someone to look at a VK56VD, we are here. But this page exists to answer the question you searched for, not to sell you a rebuild. If nothing is wrong with your engine, nothing here is asking you to do anything about it.</p>
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Question%20about%20my%20Patrol%20V8%3A" target="_blank" rel="noopener" class="btn btn-primary">Ask about your V8</a>
      </div>
    </div>
  </section>''',
        "schema_name": "Nissan Patrol V8 engine information",
        "research": True,
    },
]


def build(page):
    html = SRC.read_text(encoding="utf-8")
    for old, new in REWRITES:
        html = html.replace(old, new)

    url = f"https://patrolgarage.ae/services/{page['file']}"
    html = re.sub(r"<title>.*?</title>", f"<title>{page['title']}</title>", html, count=1, flags=re.S)
    html = re.sub(r'<meta name="description" content=".*?">',
                  f'<meta name="description" content="{page["desc"]}">', html, count=1)
    html = re.sub(r'<link rel="canonical" href=".*?">',
                  f'<link rel="canonical" href="{url}">', html, count=1)
    for attr, tag in (("property", "og:title"), ("name", "twitter:title")):
        html = re.sub(rf'<meta {attr}="{tag}" content=".*?">',
                      f'<meta {attr}="{tag}" content="{page["title"]}">', html, count=1)
    for attr, tag in (("property", "og:description"), ("name", "twitter:description")):
        html = re.sub(rf'<meta {attr}="{tag}" content=".*?">',
                      f'<meta {attr}="{tag}" content="{page["desc"]}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content=".*?">',
                  f'<meta property="og:url" content="{url}">', html, count=1)

    # A research page is not a Service offering. Marking it as one would be a lie
    # to Google about intent and to the reader about what the page is.
    if page.get("research"):
        schema = {"@context": "https://schema.org", "@type": "Article",
                  "headline": re.sub("&amp;", "&", page["title"]),
                  "description": page["desc"], "mainEntityOfPage": url,
                  "author": {"@type": "Organization", "name": "Patrol Garage Dubai"},
                  "publisher": {"@type": "Organization", "name": "Patrol Garage Dubai"}}
    else:
        schema = {"@context": "https://schema.org", "@type": "Service",
                  "name": page["schema_name"],
                  "serviceType": page["schema_name"],
                  "url": url,
                  "provider": {"@type": "AutoRepair", "name": "Patrol Garage Dubai",
                               "telephone": "+971585143634",
                               "address": {"@type": "PostalAddress",
                                           "streetAddress": "Ras Al Khor Industrial Area",
                                           "addressLocality": "Dubai", "addressCountry": "AE"}},
                  "areaServed": [{"@type": "City", "name": n} for n in ("Dubai", "Sharjah")]}
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  '<script type="application/ld+json">\n  ' + json.dumps(schema, indent=2) + '\n  </script>',
                  html, count=1, flags=re.S)

    html = re.sub(r'<section class="hero">.*?</section>', page["hero"], html, count=1, flags=re.S)
    start = html.index('<section class="dark">')
    end = html.index('<section class="cta-banner">')
    html = html[:start] + page["body"] + "\n\n  " + html[end:]

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / page["file"]).write_text(html, encoding="utf-8")
    return html


def main():
    for p in PAGES:
        h = build(p)
        bad = re.findall(r'(?:href|src|srcset)="(?!https?:|/|#|tel:|mailto:)([^"]+)"', h)
        ok = 0
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            json.loads(m.group(1)); ok += 1
        print(f"  built services/{p['file']}")
        print(f"        {len(h):,} bytes | ld+json valid: {ok} | AED: {h.count('AED')} | "
              f"relative paths left: {len(set(bad))} {sorted(set(bad))[:3] if bad else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
