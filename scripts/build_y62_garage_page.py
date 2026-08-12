#!/usr/bin/env python3
"""Build /y62-garage-dubai.html — a dedicated page for the "y62 garage" query.

Why this page exists. GSC: "y62 garage" = 93 impressions, average position 8.3,
ZERO clicks, and the site has no page targeting it — the homepage was ranking by
accident on the word "garage" in its title.

Calibrate expectations before judging it: a real Dubai business is called Y62
Auto Services Garage (Umm Ramool), and it holds the HiDubai and Facebook
listings for that term. A share of those 93 impressions is navigational intent
for THAT business and will never convert here at any position. This page targets
the remaining intent — an owner looking for a workshop that only does Y62s.

Built from the services.html shell so the header, nav, mobile menu, WhatsApp
float, CTA banner, footer, GA4 and Clarity tags are identical to the rest of the
site and cannot drift. Only the head metadata, hero and main content differ.

No prices anywhere, per the 2026-08-12 decision.

Idempotent: rewrites the file from the current shell each run.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "services.html"
OUT = ROOT / "y62-garage-dubai.html"

URL = "https://patrolgarage.ae/y62-garage-dubai.html"
TITLE = "Y62 Garage Dubai | Nissan Patrol Y62 Specialist Workshop"
# Measured at 14px Arial: must stay under ~920px or Google truncates the tail.
DESC = ("A Y62-only garage in Ras Al Khor, Dubai. VK56VD engines, JR710E "
        "gearboxes, HBMC suspension — from mechanics who work on one car.")
OG_DESC = ("A Dubai workshop built around the Nissan Patrol Y62 — engine, "
           "gearbox, suspension and heat-related faults.")

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
        <span>Ras Al Khor</span>
      </div>
      <h1>The Y62<br>Garage.</h1>
      <p class="hero-lede">
        Most Dubai workshops see a Y62 a few times a month. We see them all day. That is the whole difference &mdash; the faults are familiar before you finish describing them.
      </p>
    </div>
  </section>'''

BODY = '''<section class="dark">
    <div class="container">
      <div class="section-head">
        <div class="section-num">01 &mdash; One Car</div>
        <h2>What a Y62<br>garage does<br>differently.</h2>
        <p>A general garage treats the Y62 as a large SUV. It is not. It is a 5.6-litre VK56VD V8 with direct and port injection, a Jatco JR710E seven-speed automatic, and on higher trims a hydraulic body motion control system with no anti-roll bars at all. Get any of those three wrong and the repair does not stick. Our full <a href="/services.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 workshop service list</a> is built around exactly those systems.</p>
      </div>

      <div class="service-article">
        <h2>VK56VD engines</h2>
        <p>The V8 is durable and largely undramatic, but it has habits. Timing chain noise on cold start, valve cover gaskets weeping onto hot exhaust, coil and injector faults that read as a generic misfire, and oil consumption that owners notice long before a warning light does. Diagnosis starts with live data and a road test, not a code read &mdash; a P0300 on this engine can be coils, injectors or a vacuum leak, and those look nothing alike under load. See our <a href="blog/nissan-patrol-y62-problems-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 problems guide</a> for the full pattern.</p>
      </div>

      <div class="service-article">
        <h2>JR710E gearboxes</h2>
        <p>The seven-speed automatic is the single most expensive thing on the car to get wrong. Shudder under light throttle, a flare between gears, or a delayed engagement from cold are all early signals, and they are all cheaper to address before the torque converter contaminates the rest of the unit. Fluid condition is the first thing we check, every time. Background reading: <a href="blog/nissan-patrol-y62-transmission-problems-dubai.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 transmission problems in Dubai</a>.</p>
      </div>

      <div class="service-article">
        <h2>HBMC hydraulic suspension</h2>
        <p>Hydraulic Body Motion Control replaces conventional anti-roll bars with cross-linked hydraulic rams. It rides beautifully and it is unforgiving of improvisation &mdash; the system holds pressure, the accumulators degrade, and a leaking corner changes how the whole car sits. Fitting conventional shocks to a HBMC car because the parts are cheaper is the most common expensive mistake we undo.</p>
      </div>

      <div class="service-article">
        <h2>Heat, sand and the school run</h2>
        <p>Ambient temperatures of 45&ndash;50&deg;C and 70&deg;C tarmac put the cooling and AC systems under load that the design assumes is occasional. Radiator cores pack with fine sand, condensers block, and a system that is merely low on refrigerant in February is a system that fails in July. Stop-and-go traffic on Sheikh Zayed Road keeps the engine at operating temperature with almost no airflow, which is the condition that finds every weak cooling component. More detail: <a href="blog/nissan-patrol-overheating-dubai-summer-fix.html" style="text-decoration: underline; text-underline-offset: 3px;">Y62 overheating in Dubai summer</a>.</p>
      </div>

      <div class="section-head" style="margin-top:4rem;">
        <div class="section-num">02 &mdash; Where We Are</div>
        <h2>Ras Al Khor,<br>Dubai.</h2>
        <p>We are an independent workshop in Ras Al Khor, working on Nissan Patrols across Dubai, Sharjah and the Northern Emirates. We do not quote a Y62 job from a price list &mdash; we look at the car first, tell you what it actually needs, and price that. Send us the symptom and the year on WhatsApp and you will get a straight answer about whether it is worth bringing in.</p>
      </div>

      <div class="service-cta">
        <a href="https://wa.me/971585143634?text=Y62%20garage%20enquiry%20-%20my%20Patrol%20needs" target="_blank" rel="noopener" class="btn btn-primary">Ask about your Y62</a>
      </div>
    </div>
  </section>'''

SCHEMA = '''<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "AutoRepair",
    "name": "Patrol Garage Dubai",
    "description": "Nissan Patrol Y62 specialist workshop in Ras Al Khor, Dubai.",
    "url": "https://patrolgarage.ae/y62-garage-dubai.html",
    "telephone": "+971585143634",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Ras Al Khor",
      "addressRegion": "Dubai",
      "addressCountry": "AE"
    },
    "areaServed": [
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


def build():
    html = SRC.read_text(encoding="utf-8")

    # --- head metadata -----------------------------------------------------
    html = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", html, count=1)
    html = re.sub(r'<meta name="description" content=".*?">',
                  f'<meta name="description" content="{DESC}">', html, count=1)
    html = re.sub(r'<meta name="keywords" content=".*?">',
                  '<meta name="keywords" content="Y62 garage, Y62 garage Dubai, Nissan Patrol Y62 specialist, '
                  'Y62 workshop Dubai, Patrol Y62 mechanic Ras Al Khor">', html, count=1)
    html = re.sub(r'<link rel="canonical" href=".*?">',
                  f'<link rel="canonical" href="{URL}">', html, count=1)
    html = re.sub(r'<meta property="og:title" content=".*?">',
                  '<meta property="og:title" content="Y62 Garage Dubai | Nissan Patrol Y62 Specialist">', html, count=1)
    html = re.sub(r'<meta property="og:description" content=".*?">',
                  f'<meta property="og:description" content="{OG_DESC}">', html, count=1)
    html = re.sub(r'<meta property="og:url" content=".*?">',
                  f'<meta property="og:url" content="{URL}">', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content=".*?">',
                  '<meta name="twitter:title" content="Y62 Garage Dubai | Nissan Patrol Y62 Specialist">', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content=".*?">',
                  f'<meta name="twitter:description" content="{OG_DESC}">', html, count=1)

    # --- schema ------------------------------------------------------------
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  SCHEMA, html, count=1, flags=re.S)

    # --- hero --------------------------------------------------------------
    html = re.sub(r'<section class="hero">.*?</section>', HERO, html, count=1, flags=re.S)

    # --- main content: replace everything from the first dark section up to
    #     the CTA banner, leaving header/CTA/footer untouched.
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
    print(f"     AED mentions: {html.count('AED')}  (must be 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
