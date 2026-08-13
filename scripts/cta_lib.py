#!/usr/bin/env python3
"""cta_lib.py — shared conversion-CTA logic.

Single source of truth for: context-rich WhatsApp pre-fills, intent-tailored
end-of-article banners, and the mid-article inline CTA. Imported by BOTH
patch_cta.py (fixes existing static pages) and assemble.py (so future cron
articles inherit the same behaviour instead of blank/boilerplate CTAs).

Pure functions, no I/O. All derivation is deterministic from the page title/slug.
"""
import re
import urllib.parse

WA_NUM = "971585143634"
# Used on non-article pages (home, about, services, contact) — no article context.
GENERIC_QUOTE = "Hi, I'd like a quote for my Nissan Patrol"

# Tokens kept uppercase when rebuilding a human-readable topic phrase.
_ACR = {"y61", "y62", "y63", "v8", "v6", "ac", "gcc", "tb48", "cvt", "ecu", "uae", "aed", "suv"}
# Components we can name explicitly in banner/CTA copy (first match wins).
_COMPONENTS = ["transmission", "gearbox", "differential", "suspension", "turbo",
               "radiator", "clutch", "engine", "brake", "alternator", "overheating"]
_LEADING_FILLER = {"common", "best", "top", "the", "your", "ultimate", "complete", "guide"}


def enc(text):
    return urllib.parse.quote(text, safe="")


def topic_phrase(title):
    """'Nissan Patrol Transmission Rebuild Cost Dubai AED 2026 | Patrol Garage'
    -> 'Patrol transmission rebuild cost'."""
    t = title.split("|")[0]
    t = re.sub(r"\(.*?\)", " ", t)
    t = re.sub(r"[:|–-]", " ", t)
    t = re.sub(r"(?i)\bnissan\b", " ", t)                       # 'Patrol' implies Nissan
    t = re.sub(r"(?i)\b(20\d\d|dubai|uae|aed|in|of)\b", " ", t)  # drop year / location / currency
    t = re.sub(r"(?i)\b(guide|the|complete|owner.?s|ultimate)\b", " ", t)  # drop title filler
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    # strip leading filler words ("Common", "Best", ...)
    while words and words[0].lower() in _LEADING_FILLER:
        words.pop(0)
    words = [w.upper() if w.lower() in _ACR else w.lower() for w in words]
    topic = " ".join(words).strip()
    if not topic:
        return "Nissan Patrol"
    return topic[:1].upper() + topic[1:]


def classify(slug, title=""):
    """Return intent bucket: 'problems' | 'cost' | 'service' | 'guide'."""
    s = (slug + " " + (title or "")).lower()
    if re.search(r"\b(problem|problems|issue|issues|fault|faults|trouble)\b", s):
        return "problems"
    if re.search(r"\b(cost|price|pricing|aed|rebuild|quote|repair)\b", s):
        return "cost"
    if re.search(r"\b(service|maintenance|interval|km|oil)\b", s):
        return "service"
    return "guide"


def _model(s):
    m = re.search(r"\b(y6[123])\b", s.lower())
    return m.group(1).upper() if m else None


def _component(s):
    sl = s.lower()
    for c in _COMPONENTS:
        if c in sl:
            return c
    return None


# Slug -> fixed topic phrase, overriding whatever topic_phrase() derives from the
# title. Use this when the title names something the workshop does not sell: the
# pre-fill is an OFFER ("can I get an exact quote"), so it must not invite work we
# do not do, even if the title legitimately covers it as owner information.
#
# nissan-patrol-suspension-dubai: titled "Suspension Repair & Lift Kits", which
# made all four WhatsApp CTAs read "I read your Patrol suspension repair & lift
# kits guide — can I get an exact quote". The workshop does suspension REPAIR
# (shocks, HBMC accumulators, bushes) but not lift kits / height modification.
# Owner decision 2026-08-13: keep the title and the informational lift-kit
# section, hardcode the CTA so it cannot regenerate the offer from the title.
PREFILL_TOPIC_OVERRIDES = {
    "nissan-patrol-suspension-dubai": "Patrol suspension repair",
}


def prefill_for(title, slug):
    """Context-rich WhatsApp message for an article, e.g.
    'Hi, I read your Patrol transmission rebuild cost guide — can I get an exact quote for my Patrol?'"""
    intent = classify(slug, title)
    topic = PREFILL_TOPIC_OVERRIDES.get(slug) or topic_phrase(title)
    ask = {
        "cost": "can I get an exact quote for my Patrol?",
        "problems": "I think my Patrol might have an issue — can you help?",
        "service": "can I get a service quote for my Patrol?",
        "guide": "can you help with my Patrol?",
    }[intent]
    return f"Hi, I read your {topic} guide — {ask}"


def banner_for(title, slug):
    """Intent-tailored end-of-article banner. Returns (heading, paragraph, button_label)."""
    intent = classify(slug, title)
    blob = slug + " " + (title or "")
    comp = _component(blob)
    model = _model(blob) or "Patrol"

    if intent == "cost":
        subj = comp or (model if model != "Patrol" else None)
        if subj:
            h2 = f"Get your exact {subj} quote"
            p = (f"You've seen the price ranges — now get a real number for your Patrol. "
                 f"Send your car's details on WhatsApp and we'll quote your {subj} job fast.")
        else:
            h2 = "Get your exact Patrol quote"
            p = ("You've seen the price ranges — now get a real number. Send your Patrol's "
                 "details on WhatsApp and we'll quote you fast.")
        label = "Get my quote on WhatsApp"
    elif intent == "problems":
        if comp:
            h2 = f"{comp.capitalize()} trouble with your Patrol?"
            p = (f"Describe the symptoms on WhatsApp and we'll tell you what's likely wrong "
                 f"and what the {comp} fix costs. Same-day reply.")
        else:
            h2 = f"Think your {model} has a problem?"
            p = (f"Describe the symptoms on WhatsApp and we'll tell you what's likely wrong "
                 f"with your {model} and what it costs to fix. Same-day reply.")
        label = "Message a specialist on WhatsApp"
    elif intent == "service":
        h2 = "Ready to book your Patrol service?"
        p = ("Message us on WhatsApp for a transparent service quote — Patrol specialists, "
             "no dealer markup.")
        label = "Get my service quote"
    else:
        h2 = "Questions about your Patrol?"
        p = "Chat with a Patrol specialist on WhatsApp for quick, honest answers and a clear quote."
        label = "Chat on WhatsApp"
    return h2, p, label


def wants_mid_cta(slug, title=""):
    """Mid-article CTA only on high-intent pages (cost / problems)."""
    return classify(slug, title) in ("cost", "problems")


def mid_cta_html(title, slug):
    """Self-contained inline mid-article CTA. Theme-agnostic (WhatsApp-green accent,
    works on light or dark). Carries data-cta="mid" marker for idempotency."""
    intent = classify(slug, title)
    prefill = prefill_for(title, slug)
    if intent == "problems":
        hook = "Not sure how serious it is? Describe the symptoms and get a straight answer."
        label = "Ask a Patrol specialist on WhatsApp →"
    elif intent == "service":
        hook = "Want a transparent price for your service? Skip the dealer markup."
        label = "Get your service quote on WhatsApp →"
    else:  # cost / guide
        hook = "Want the exact number for your Patrol — not just a range?"
        label = "Get your quote on WhatsApp →"
    href = f"https://wa.me/{WA_NUM}?text={enc(prefill)}"
    return (
        '<div class="mid-cta" data-cta="mid" '
        'style="margin:2.5rem 0;padding:1.4rem 1.5rem;border:1px solid rgba(37,211,102,0.45);'
        'background:rgba(37,211,102,0.07);border-radius:14px;text-align:center;">'
        f'<p style="margin:0 0 1rem;font-weight:700;font-size:1.05rem;">{hook}</p>'
        f'<a href="{href}" target="_blank" rel="noopener" class="btn" '
        f'style="background:#25D366;color:#fff;display:inline-flex;">{label}</a>'
        "</div>"
    )


# Matches a WhatsApp href with OR without an existing ?text= query.
_WA_HREF_RE = re.compile(r'href="https://wa\.me/' + WA_NUM + r'(?:\?text=[^"]*)?"')


def set_all_wa_prefill(html, prefill):
    """Point every WhatsApp link on the page at the same context-rich pre-fill.
    Idempotent: re-running with the same prefill is a no-op."""
    repl = f'href="https://wa.me/{WA_NUM}?text={enc(prefill)}"'
    return _WA_HREF_RE.sub(repl, html)


# Generic boilerplate banner that shipped on the high-intent pages — only rewrite these.
def banner_is_generic(banner_html):
    return ("Need Help With Your Y62?" in banner_html
            or "If you're experiencing any of these issues" in banner_html)


def insert_mid_cta(article_body, block):
    """Insert the mid-article CTA before the H2 nearest the article's middle,
    skipping the first H2 and the last two (FAQ / closing). Idempotent via marker."""
    if 'data-cta="mid"' in article_body:
        return article_body
    offsets = [m.start() for m in re.finditer(r"<h2\b", article_body, re.I)]
    if len(offsets) < 3:
        return article_body  # too short to place mid-way meaningfully
    candidates = offsets[1:-2] or offsets[1:-1] or offsets
    mid = len(article_body) / 2
    pos = min(candidates, key=lambda o: abs(o - mid))
    return article_body[:pos] + block + "\n      " + article_body[pos:]
