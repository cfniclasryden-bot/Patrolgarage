#!/usr/bin/env python3
"""In-body money-page links — the topchallenger CONTENT-MODEL pattern, adapted.

Measured problem (2026-08-12): 0 of 44 posts linked to /services or / from inside
<article>. The 133 /services links in the blog are nav/footer boilerplate, which
Google discounts. Meanwhile /services sits at position 17.7 with 1 click.

The rule, from topchallenger/site/CONTENT-MODEL.md §4.1:

  * Every post carries exactly ONE in-body /services link, placed in the
    "When to bring it to Patrol Garage" section.
  * Anchor text rotates so a run of posts does not point at one page with one
    repeated anchor.
  * Pillars additionally carry one in-body link to `/`.

Adapted because Patrol Garage has ONE services page, not topchallenger's seven.
There is no per-cluster service page to link down to, so the anchor carries the
topical signal instead: it names the real service category from services.html
that matches the post's subject.

Link form is root-absolute `.html` (`/services.html`), matching the site's
existing in-body convention (119 in-body links, all `/blog/<slug>.html`) and the
canonical form. If the site later migrates to extensionless URLs, this is one
sed away.

Idempotent via the MARKER comment. Fail-safe: every public function returns the
body unchanged on any error, so it can never break a nightly publish.
"""
import re

MARKER = "<!-- MONEYLINK -->"

SERVICES_URL = "/services.html"
HOME_URL = "/"

# Real service categories, lifted from the <h3>s in services.html so an anchor
# never promises a service the workshop does not list.
SERVICE_ANCHORS = {
    "transmission": "Y62 gearbox and transmission work",
    "engine": "Y62 engine diagnostics and repair",
    "suspension": "Y62 suspension and lift kit work",
    "ac": "Y62 AC service and repair",
    "electrical": "Y62 electrical and diagnostic work",
    "brakes": "Y62 brakes, tyres and batteries",
    "service": "Y62 servicing and maintenance",
    "mods": "Y62 modifications and performance upgrades",
}

# Slug keyword -> service key. First match wins, so order matters: the more
# specific patterns sit above the general ones.
TOPIC_RULES = [
    (r"transmission|gearbox|torque-converter|differential|cv-joint|driveshaft|diff", "transmission"),
    (r"suspension|air-bag|lift-kit|shock|hbmc", "suspension"),
    (r"\bac\b|air-con|compressor", "ac"),
    (r"abs|brake|battery|tyre", "brakes"),
    (r"dashcam|sensor|electrical|starter-motor|fourth-brake-light", "electrical"),
    (r"turbo|intercooler|snorkel|tow-bar|paint-protection|ppf|upgrade|modification", "mods"),
    (r"oil|service|interval|how-many-km|maintenance", "service"),
    (r"water-pump|coolant|overheat|radiator|thermostat|head-gasket|valve-cover|"
     r"spark-plug|injector|fuel-pressure|crankshaft|oxygen|throttle|engine-mount|misfire", "engine"),
]

# Pillars — the hub pages. These also link home.
PILLARS = {
    "nissan-patrol-y62-dubai-complete-guide",
    "nissan-patrol-y61-dubai-complete-guide",
    "nissan-patrol-service-dubai-complete-guide",
    "nissan-patrol-y62-problems-dubai",
    "nissan-patrol-y62-transmission-problems-dubai",
}

# Three sentence shapes. Rotated by slug hash so neighbouring posts differ and
# the choice is stable across re-runs (no random, no drift between deploys).
TEMPLATES = [
    'Here is what <a href="{url}">{anchor}</a> covers at the workshop.',
    'Here is <a href="{url}">what we do to a Y62</a>, job by job.',
    'The rest of the work handled at <a href="{url}">our Y62 workshop in Ras Al Khor</a> is listed here.',
]

HOME_SENTENCE = (
    ' <a href="{url}">Patrol Garage</a> is a Nissan Patrol specialist workshop in Ras Al Khor, Dubai.'
)


def service_key(slug):
    for pattern, key in TOPIC_RULES:
        if re.search(pattern, slug):
            return key
    return "service"


def _sentence(slug):
    """Deterministic anchor + template choice for this slug."""
    key = service_key(slug)
    anchor = SERVICE_ANCHORS[key]
    # Template 0 is the only one that uses the topical anchor, so weight toward
    # it: it carries the keyword signal. Stable per-slug, but varied across the
    # catalogue.
    idx = sum(ord(c) for c in slug) % 3
    return TEMPLATES[idx].format(url=SERVICES_URL, anchor=anchor)


def already_linked(body):
    return MARKER in body


def add_money_links(body, slug):
    """Return `body` with one in-body /services link (and, for pillars, one home
    link). Returns the body untouched if it already has them or if no safe
    insertion point exists."""
    try:
        if already_linked(body):
            return body

        addition = _sentence(slug)
        if slug in PILLARS:
            addition += HOME_SENTENCE.format(url=HOME_URL)

        # Preferred slot: first paragraph of the "When to bring it to …" section.
        m = re.search(
            r"<h2[^>]*>\s*When to [Bb]ring[^<]*</h2>\s*(<p>.*?</p>)",
            body, re.S,
        )
        if m:
            close = m.end(1) - len("</p>")
            return body[:close] + " " + addition + MARKER + body[close:]

        # Fallback: first paragraph after the SECOND <h2>, keeping the link
        # mid-article rather than stranded at the end.
        h2s = list(re.finditer(r"<h2[^>]*>.*?</h2>", body, re.S))
        if len(h2s) >= 2:
            after = body[h2s[1].end():]
            para = re.search(r"<p>.*?</p>", after, re.S)
            if para:
                close = h2s[1].end() + para.end() - len("</p>")
                return body[:close] + " " + addition + MARKER + body[close:]

        # Last resort: first paragraph in the body at all.
        para = re.search(r"<p>.*?</p>", body, re.S)
        if para:
            close = para.end() - len("</p>")
            return body[:close] + " " + addition + MARKER + body[close:]

        return body
    except Exception:
        # Never fail a nightly publish over an internal link.
        return body
