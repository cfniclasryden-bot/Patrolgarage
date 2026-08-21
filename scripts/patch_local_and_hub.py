#!/usr/bin/env python3
"""(1) Ras Al Khor local layer on / and /contact.html. (2) Turn /services.html
into a hub that stops competing with the homepage.

WHY (measured 2026-08-13, GSC 90d + DataForSEO UAE):

Local terms nobody targets, and the workshop is physically there:
    car garage ras al khor   210/mo  MEDIUM  $2.64
    garage ras al khor       140/mo  MEDIUM  $2.01
350/mo of local intent — larger than the entire specialist cluster (140/mo) and
larger than any Patrol-qualified service cluster except engine research.

The term is generic but the intent is local, and Patrols are common enough in
the UAE that a share of those searchers are Patrol owners. So the copy leads
with the location and is immediately, explicitly honest that this is a
Patrol-only workshop. Anyone else is told to go elsewhere, in the first
paragraph. That is the deal: we rank for a generic local term, we do not
pretend to be a general garage.

Cannibalisation, measured:
    "nissan patrol garage"       /  pos  4.0 (34 impr, 3 clk)
                     /services.html  pos 45.0 ( 1 impr)
    "nissan patrol service dubai" /  pos 39.3
                     /services.html  pos 83.0
/services.html has NO query it wins. The homepage outranks it on both of its own
target keywords by 41 and 44 positions. Its title
("Nissan Patrol Services Dubai") competes head-on with the homepage's
("Nissan Patrol Garage Dubai") for the same garage/service intent.

So services.html is retitled as a MENU/hub — the word "garage" is removed
entirely so it stops bidding against the page that already wins — and it will
distribute to the three service pages once those exist.

Schema gaps fixed while here: the homepage AutoRepair had geo but NO
postalAddress, and contact.html had NO schema at all. For local intent that is
the most valuable structured data on the site.

Titles measured at 20px Arial, descriptions at 14px Arial, all inside Google's
desktop truncation limits.

Idempotent via MARKER. Run --dry-run first.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!-- LOCALLAYER -->"

HOME_TITLE = "Nissan Patrol Garage in Ras Al Khor, Dubai | Y62 Specialists"   # 540px
HOME_DESC = ("Nissan Patrol specialist garage in Ras Al Khor, Dubai. Patrols only: "
             "engine, gearbox, major servicing and diagnostics. Call +971 58 514 3634.")

CONTACT_TITLE = "Patrol Garage, Ras Al Khor | Nissan Patrol Workshop Dubai"    # 531px
CONTACT_DESC = ("Patrol Garage is in the Ras Al Khor industrial area, Dubai. Directions, "
                "hours and WhatsApp. We work on Nissan Patrol only, Y61 through Y63.")

# "garage" deliberately absent — that is the word it was losing on to the homepage.
SERVICES_TITLE = "Nissan Patrol Service Menu | Engine, Gearbox, Suspension"    # 529px
SERVICES_DESC = ("Every job we do on a Nissan Patrol, by system: engine, gearbox and "
                 "transmission, suspension, AC, electrical and periodic servicing.")


# Homepage: replace the thin "Coverage" blurb with a real Ras Al Khor block.
HOME_OLD_HEAD = """<h2>Serving all of<br>Dubai.</h2>
        <p style="margin-left: auto; margin-right: auto;">Based in Ras Al Khor — within easy reach of every major area.</p>"""

HOME_NEW_HEAD = """<h2>A garage in<br>Ras Al Khor.</h2>
        <p style="margin-left: auto; margin-right: auto;">We are in the Ras Al Khor industrial area, off the Dubai to Al Ain road and a few minutes from Nad Al Hamar. If you are looking for a car garage in Ras Al Khor, one thing is worth knowing before you drive over: we only take Nissan Patrols.</p>
        <p style="margin-left: auto; margin-right: auto;">That is not a preference, it is the whole workshop. The diagnostic kit is set up for the VK56VD and the JR710E, the parts on the shelf are Patrol parts, and the fault history we work from is Patrol fault history. If you drive something else we will say so straight away rather than waste your morning, and we can usually point you to someone nearby who can help.</p>
        <p style="margin-left: auto; margin-right: auto;">Patrol owners come to us from across Dubai, Sharjah and the Northern Emirates for exactly that reason.</p>""" + MARKER

CONTACT_BLOCK = """
      <div class="section-head" style="margin-top:4rem;">
        <div class="section-num">02 &mdash; Finding Us</div>
        <h2>Ras Al Khor<br>Industrial Area.</h2>
        <p>We are in the Ras Al Khor industrial area in Dubai, just off the Dubai to Al Ain road (E66) and a short drive from Nad Al Hamar, Al Aweer and Mirdif. Ras Al Khor is a workshop district, so most of what surrounds us is other garages and parts suppliers rather than shopfronts. Message us on WhatsApp when you set off and we will send a live pin.</p>
        <p>Worth repeating before you make the trip: this is a Nissan Patrol workshop only, Y61 through Y63. We are not a general car garage in Ras Al Khor and we will not pretend to be one. If you drive something else, message us anyway and we will tell you who nearby actually does that car properly.</p>
        <p>Most Patrol owners reach us from Deira, Mirdif, Nad Al Sheba, Al Quoz, Business Bay and Sharjah. Parking is on site and you can wait for shorter jobs.</p>
      </div>""" + MARKER


def patch_home(dry):
    p = ROOT / "index.html"
    h = p.read_text(encoding="utf-8")
    if MARKER in h:
        print("  skip   index.html (already patched)")
        return 0
    if HOME_OLD_HEAD not in h:
        print("  !! index.html: coverage block not found, refusing")
        return -1
    h = re.sub(r"<title>.*?</title>", f"<title>{HOME_TITLE}</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?">',
               f'<meta name="description" content="{HOME_DESC}">', h, count=1)
    h = h.replace(HOME_OLD_HEAD, HOME_NEW_HEAD, 1)

    # The postalAddress this used to inject has been removed: the site has no
    # premises, so there is no address to publish. Re-running this script must
    # not reintroduce it. See scripts/patch_entity_schema.py.

    if not dry:
        p.write_text(h, encoding="utf-8")
    print("  patch  index.html: title, description, Ras Al Khor block, schema address")
    return 1


def patch_contact(dry):
    p = ROOT / "contact.html"
    h = p.read_text(encoding="utf-8")
    if MARKER in h:
        print("  skip   contact.html (already patched)")
        return 0
    h = re.sub(r"<title>.*?</title>", f"<title>{CONTACT_TITLE}</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?">',
               f'<meta name="description" content="{CONTACT_DESC}">', h, count=1)

    # contact.html had NO schema at all — add a full local one.
    schema = {
        "@context": "https://schema.org",
        "@type": "AutoRepair",
        "name": "Patrol Garage Dubai",
        "description": "Nissan Patrol Y62 specialists serving Dubai.",
        "url": "https://patrolgarage.ae/contact.html",
        "telephone": "+971585143634",
        "email": "info@patrolgarage.ae",
        "areaServed": [{"@type": "City", "name": n} for n in ("Dubai", "Sharjah")],
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "telephone": "+971585143634",
            "areaServed": "AE",
            "availableLanguage": ["en", "ar"],
            "hoursAvailable": [
                {"@type": "OpeningHoursSpecification",
                 "dayOfWeek": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
                 "opens": "09:00", "closes": "19:00"},
                {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday",
                 "opens": "09:00", "closes": "14:00"},
            ],
        },
    }
    block = ('<script type="application/ld+json">\n  '
             + json.dumps(schema, indent=2) + '\n  </script>\n\n  ')
    idx = h.find("<style>")
    if idx == -1:
        print("  !! contact.html: no <style> anchor, refusing")
        return -1
    h = h[:idx] + block + h[idx:]

    # visible location content, appended inside the existing dark section
    anchor = '</div>\n  </section>\n\n  <section class="cta-banner">'
    if anchor not in h:
        m = re.search(r'(</div>\s*</section>\s*<section class="cta-banner">)', h)
        if not m:
            print("  !! contact.html: cannot find insert point for the location block")
            return -1
        h = h[:m.start(1)] + CONTACT_BLOCK + "\n    " + h[m.start(1):]
    else:
        h = h.replace(anchor, CONTACT_BLOCK + "\n    " + anchor, 1)

    if not dry:
        p.write_text(h, encoding="utf-8")
    print("  patch  contact.html: title, description, local schema, Ras Al Khor block")
    return 1


def patch_services(dry):
    p = ROOT / "services.html"
    h = p.read_text(encoding="utf-8")
    if SERVICES_TITLE in h:
        print("  skip   services.html (already retitled)")
        return 0
    h = re.sub(r"<title>.*?</title>", f"<title>{SERVICES_TITLE}</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content=".*?">',
               f'<meta name="description" content="{SERVICES_DESC}">', h, count=1)
    h = re.sub(r'<meta name="keywords" content=".*?">',
               '<meta name="keywords" content="Nissan Patrol service menu, Y62 engine work, '
               'Y62 gearbox repair, Y62 suspension, Patrol periodic service">', h, count=1)
    h = re.sub(r'<meta property="og:title" content=".*?">',
               f'<meta property="og:title" content="{SERVICES_TITLE}">', h, count=1)
    h = re.sub(r'<meta name="twitter:title" content=".*?">',
               f'<meta name="twitter:title" content="{SERVICES_TITLE}">', h, count=1)
    if not dry:
        p.write_text(h, encoding="utf-8")
    print("  patch  services.html: retitled as a menu, 'garage' removed so it stops "
          "competing with the homepage")
    return 1


def main():
    dry = "--dry-run" in sys.argv
    rc = 0
    for fn in (patch_home, patch_contact, patch_services):
        r = fn(dry)
        if r < 0:
            rc = 1
    print("\n" + ("DRY RUN — nothing written" if dry else "WRITTEN"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
