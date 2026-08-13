#!/usr/bin/env python3
"""Early contextual CTA, placed immediately after the quick-answer block.

MEASURED PROBLEM (2026-08-13, mobile 390px, against Clarity's 40% avg scroll):

    page                 screens  QA ends  1st in-flow CTA  reached at 40%?
    y62-complete-guide      13.9      9%        39%          barely
    homepage                11.2     none        7%          YES
    y62-problems            12.8      9%        35%          yes
    service-cost             7.0     none       47%          NO
    best-oil                15.6      8%        92%          NO
    y62-vs-y63              13.8      9%        91%          NO
    y61-guide               19.0     none       94%          NO

Posts run 11-19 screens. Four of the top seven pages put the first conversion
point at 47-94% of the page; on three of them it is in the final 10%, which
effectively nobody reaches. Meanwhile the quick-answer block ENDS at 9%, where
100% of readers still are, and there is nothing there.

The quick answer is also why they leave: it answers the question completely in
the first screen, which is good content and terrible conversion. So the ask goes
directly under it, while the reader has just had their question answered and
before the 11-19 screens of detail they will not read.

COPY IS PER POST TYPE. A generic "contact us" at 9% is an ad and gets ignored;
the whole point is that the ask matches what the reader just read. Five types,
each with its own hook, button label and WhatsApp pre-fill.

No prices, and no pre-purchase inspection — the workshop does not offer it.

MEASUREMENT. The block carries data-cta="early"; the existing mid-article and
footer CTAs are untouched. patch_early_cta.py also upgrades the (byte-identical
across all 44 posts) click-tracking snippet to append the CTA position to the
GA4 event label, so whatsapp_click tells you WHICH position earned the message
rather than just which page. Without that this change is unmeasurable.
"""
import re

WA = "971585143634"
MARKER = 'data-cta="early"'

# slug pattern -> type. First match wins; order matters.
TYPE_RULES = [
    ("COMPARISON", r'-vs-|vs-y6|y61-vs|specialist-abu-dhabi|independent-service-centre|al-futtaim'),
    ("GUIDE",      r'complete-guide|-problems-dubai$|off-road|pre-purchase|mechanic-al-quoz'),
    ("SERVICE",    r'best-oil|service-every|service-dubai-complete|service-cost'),
    ("SYMPTOM",    r'problem|overheat|failure'),
    ("COST",       r'cost|price'),
]

COPY = {
    "COST": (
        "Want the number for your own Y62, not a range? Send us the year and the "
        "mileage and we will price the actual job.",
        "Get a quote on WhatsApp",
        "Y62 quote - year and mileage: ",
    ),
    "SYMPTOM": (
        "Is yours doing this? Describe what you are hearing or feeling and we will "
        "tell you what it usually turns out to be before the car comes in.",
        "Describe the symptom",
        "Y62 symptom - year and what it is doing: ",
    ),
    "GUIDE": (
        "Own one, or about to? Tell us the year and we will tell you what that "
        "particular car tends to need in Dubai heat.",
        "Ask about your Patrol",
        "Question about my Patrol - year: ",
    ),
    "COMPARISON": (
        "Deciding between them? Tell us which one you are looking at and we will "
        "tell you what that year actually needs.",
        "Ask before you buy",
        "Deciding on a Patrol - which year: ",
    ),
    "SERVICE": (
        "Not sure what yours is due for? Send the year and the mileage and we will "
        "tell you which service it actually needs.",
        "Check what yours needs",
        "Patrol service - year and mileage: ",
    ),
}


def post_type(slug):
    for name, rx in TYPE_RULES:
        if re.search(rx, slug):
            return name
    return "GUIDE"


def enc(text):
    import urllib.parse
    return urllib.parse.quote(text)


def html_for(slug):
    hook, label, prefill = COPY[post_type(slug)]
    href = f"https://wa.me/{WA}?text={enc(prefill)}"
    return (
        f'\n<div class="early-cta" {MARKER} '
        'style="margin:1.5rem 0 2rem;padding:1.1rem 1.25rem;'
        'border:1px solid rgba(37,211,102,0.45);background:rgba(37,211,102,0.07);'
        'border-radius:12px;">'
        f'<p style="margin:0 0 0.9rem;font-weight:600;font-size:1rem;line-height:1.45;">{hook}</p>'
        f'<a href="{href}" target="_blank" rel="noopener" {MARKER} '
        'style="display:inline-flex;align-items:center;gap:0.5rem;background:#25D366;color:#fff;'
        'padding:0.65rem 1.15rem;font-weight:700;font-size:0.8rem;letter-spacing:0.05em;'
        f'text-transform:uppercase;border-radius:8px;">{label} &rarr;</a>'
        '</div>\n'
    )


def already_present(body):
    return MARKER in body


def insert(body, slug):
    """Put the CTA immediately after the quick-answer block.

    Fallback for the 9 posts with no quick-answer block: after the FIRST
    paragraph of the article, which lands at roughly the same depth. Never
    inside the FAQ, CTA or related-reading blocks.

    Fail-safe: returns the body unchanged on any error, so it can never break a
    nightly publish.
    """
    try:
        if already_present(body):
            return body
        block = html_for(slug)

        m = re.search(r'<div class="direct-answer">.*?</div>', body, re.S)
        if m:
            return body[:m.end()] + block + body[m.end():]

        m = re.search(r'<p>.*?</p>', body, re.S)
        if m:
            return body[:m.end()] + block + body[m.end():]
        return body
    except Exception:
        return body
