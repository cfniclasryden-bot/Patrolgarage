#!/usr/bin/env python3
"""ad_city.py — what an Abu Dhabi post on this site is, and what it must carry.

Added 2026-10-09, with the Abu Dhabi hub and the Abu Dhabi queue. Ported from
topchallenger-site's site_config (AD_CITY_RULES, ad_city_for, check_city), with
this site's rules instead of the workshop's:

  * Abu Dhabi posts here answer OWNERSHIP questions (reliability, what drives
    maintenance cost, long-term ownership, what the heat does). Fault and repair
    keywords for Abu Dhabi are topchallenger.ae's, and keyword_generator.py's
    Gate 0b rejects them.
  * No premises, so the one location statement is "the work is carried out in
    Mussafah". Never the partner workshop's name.
  * No prices, figures or intervals: the same hard rules as every post, restated
    because a cost keyword invites them.

Every WhatsApp link on an Abu Dhabi page (the hub and every post whose slug
names Abu Dhabi) is pre-filled with a message starting "Mussafah:", so the
inbox can route it, and the page carries the Abu Dhabi first-screen ask with
event labels pg-ad-wa / pg-ad-wa-ar / pg-ad-call. See ad_ask_block() and
apply_routing(); patch_ad_routing.py applies them to the shipped pages and
assemble.py to every new Abu Dhabi post.
"""
import re
from urllib.parse import quote

HUB = "nissan-patrol-abu-dhabi.html"
HUB_PATH = "/" + HUB

WA = "971585143634"
TEL = "+971585143634"
TEL_SHOWN = "+971 58 514 3634"

_AD_RE = re.compile(r"\babu[ -]dhabi\b", re.I)


def ad_city_for(keyword_or_slug):
    """'Abu Dhabi' if the keyword or slug names it, else None.

    Mussafah is not matched on its own: keyword_generator.py rejects it in a
    keyword (it is the workshop district, topchallenger.ae's vocabulary)."""
    s = (keyword_or_slug or "").replace("-", " ")
    return "Abu Dhabi" if _AD_RE.search(s) else None


def is_ad_page(rel_path):
    """True for the hub and for every blog post whose slug names Abu Dhabi."""
    rel = rel_path.lstrip("/")
    if rel == HUB:
        return True
    return rel.startswith("blog/") and bool(ad_city_for(rel[5:].rsplit(".", 1)[0]))


AD_CITY_RULES = """
LOCATION FOR THIS POST: THE READER'S PATROL IS IN ABU DHABI, NOT DUBAI.
  * Use "Abu Dhabi" in the H1, in the first or second sentence of the quick
    answer, and naturally once or twice more. Do not write as though the car
    lives in Dubai traffic. Abu Dhabi context you may use: long highway runs
    (E11 to Dubai, E22 to Al Ain), coastal humidity on the island, summer heat,
    fine sand and dust.
  * Say ONCE, plainly, that for Abu Dhabi owners the work is carried out in
    Mussafah. Nothing else about it: no workshop name, no address, no "our
    workshop", no "visit us", no opening hours, no directions.
  * This is an OWNERSHIP post (reliability, what drives the cost of keeping
    one, long-term ownership, what the climate does). Explain causes and what
    to watch for. Do not turn it into a repair quote.
  * No prices, no AED, no ranges, no percentages, no figures of any kind for
    what anything costs, and no service interval in km, miles or months. Where
    cost comes up, explain what DRIVES it (parts vs labour, repair vs replace,
    how the car has been used, what the diagnosis finds).
  * Link to the Abu Dhabi page once, inline, where the reader would want it:
    <a href="/nissan-patrol-abu-dhabi.html">Nissan Patrol Y62 in Abu Dhabi</a>
    (you may vary the anchor text).
  * The Y62 only. Do not write "Y61", "Y63" or "Super Safari" ANYWHERE in this
    post, not even in passing: no section, no aside, no comparison, no FAQ. A
    pre-publish check blocks the post on a single mention.
  * The "When to bring it to Patrol Garage" section should say Abu Dhabi
    owners can message on WhatsApp with the symptom, the year and the mileage.
"""

AD_META_RULE = (
    "\nCITY: this post is for Nissan Patrol owners in ABU DHABI. \"Abu Dhabi\" must "
    "appear in title, description, og_title, schema_headline and h1_short. The "
    "title ends with '| Patrol Garage' (not 'Dubai'). The year may be left out of "
    "the title if it does not fit. No price, figure or interval in any field.\n"
)


# The 2 of 3 Abu Dhabi mix lives in queue_position (seed_ad_queue.py). When the
# Abu Dhabi rows run low it stops without anyone noticing, so the runner warns.
AD_LOW_WATER = 3


def ad_mix_warning(pending_keywords):
    """A run-log warning when fewer than AD_LOW_WATER Abu Dhabi keywords are
    pending, else None."""
    n = sum(1 for k in pending_keywords if ad_city_for(k))
    if n >= AD_LOW_WATER:
        return None
    return (f"[!] AD MIX: only {n} Abu Dhabi keyword(s) pending (fewer than {AD_LOW_WATER}). "
            "The 2-of-3 Abu Dhabi mix stops when they run out; add rows with "
            "scripts/seed_ad_queue.py (AD_KEYWORDS) and re-run it with --write.")


def ad_city_rules_for(slug):
    return AD_CITY_RULES if ad_city_for(slug) else None


# ------------------------------------------------------------ Mussafah routing

# English pre-fill for every other WhatsApp link on an Abu Dhabi post (banner,
# float, mid and early CTAs). cta_lib.prefill_for() derives a topic from the
# title, which reads badly on a question title ("your Is patrol reliable abu
# dhabi guide"); apply_routing() then puts "Mussafah: " in front.
POST_PREFILL = "Hi, I read your Abu Dhabi Y62 guide and have a question about my Patrol: "

EN = "Mussafah: Hello Patrol Garage, my Nissan Patrol Y62 is in Abu Dhabi and I need help with: "
AR = "Mussafah: السلام عليكم، عندي نيسان باترول Y62 في أبوظبي وأحتاج مساعدة في: "
BUTTON = "WhatsApp us about your Abu Dhabi Y62"
CALL = "Rather talk?"
AR_LINK = "تفضّل العربية؟ راسلنا على واتساب"
MARKER = 'data-cta-label="pg-ad-wa"'
PREFIX = "Mussafah: "

# Same design as patch_first_screen_cta.py's .pg-ask (this site's own button and
# tokens), its own class so assemble.py's template strip never touches it.
CSS = ('<style id="pg-ad-css">'
       '.pg-ad{display:flex;flex-direction:column;align-items:flex-start;gap:.35rem;margin:1.6rem 0 0}'
       '.pg-ad .pg-ad-wa{white-space:normal;text-align:left;margin-bottom:.4rem}'
       '.pg-ad .pg-ad-wa svg{width:16px;height:16px;flex-shrink:0}'
       '.pg-ad-alt{margin:0;font-family:\'JetBrains Mono\',monospace;font-size:.74rem;'
       'letter-spacing:.12em;text-transform:uppercase;color:var(--text-2)}'
       '.pg-ad-alt a,.pg-ad-ar a{display:inline-flex;align-items:center;min-height:44px;'
       'text-decoration:none;color:var(--white)}'
       '.pg-ad-alt a{margin-left:.35rem;border-bottom:1px solid rgba(255,255,255,.3)}'
       '.pg-ad-alt a:hover{border-bottom-color:var(--white)}'
       '.pg-ad-ar{margin:0;font-size:.95rem}'
       '.pg-ad-ar a{color:var(--text);border-bottom:1px solid var(--whatsapp)}'
       '.pg-ad-ar a:hover{color:var(--whatsapp)}'
       '</style>\n')

WA_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
          '<path d="M20.5 3.5A11.9 11.9 0 0 0 12 0C5.4 0 0 5.4 0 12c0 2.1.6 4.2 1.6 6L0 24l6.2-1.6A12 '
          '12 0 0 0 12 24c6.6 0 12-5.4 12-12 0-3.2-1.2-6.2-3.5-8.5zM12 21.9c-1.8 0-3.6-.5-5.1-1.4l-.4-.2'
          '-3.7 1 1-3.6-.2-.4A9.9 9.9 0 0 1 2.2 12C2.2 6.6 6.6 2.2 12 2.2S21.8 6.6 21.8 12 17.4 21.9 12 '
          '21.9z"/></svg>')


def ad_ask_block(indent="      "):
    return (f'{indent}<div class="pg-ad" data-fs="ad">\n'
            f'{indent}  <a class="btn btn-primary pg-ad-wa" {MARKER} '
            f'href="https://wa.me/{WA}?text={quote(EN)}" target="_blank" rel="noopener">{WA_SVG}{BUTTON}</a>\n'
            f'{indent}  <p class="pg-ad-alt">{CALL}<a data-cta-label="pg-ad-call" '
            f'href="tel:{TEL}">{TEL_SHOWN}</a></p>\n'
            f'{indent}  <p class="pg-ad-ar" lang="ar" dir="rtl"><a lang="ar" data-cta-label="pg-ad-wa-ar" '
            f'href="https://wa.me/{WA}?text={quote(AR)}" target="_blank" rel="noopener">{AR_LINK}</a></p>\n'
            f'{indent}</div>')


_WA_HREF = re.compile(r'href="https://wa\.me/' + WA + r'(?:\?text=([^"]*))?"')
_BLOCK_RE = re.compile(r'[ \t]*<div class="pg-ad" data-fs="ad">.*?\n[ \t]*</div>', re.S)


def _prefix_href(m):
    from urllib.parse import unquote
    text = unquote(m.group(1) or "")
    if text.startswith(PREFIX):
        return m.group(0)
    text = PREFIX + (text or "Hello Patrol Garage, my Nissan Patrol Y62 is in Abu Dhabi.")
    return f'href="https://wa.me/{WA}?text={quote(text, safe="")}"'


def apply_routing(html):
    """The page with the Abu Dhabi ask under its H1 and every WhatsApp pre-fill
    starting "Mussafah:". Idempotent.

    The ask goes directly after the hero's closing </h1> plus its lede when
    there is one, the same place as the Dubai first-screen ask. Any Dubai
    first-screen ask (.pg-ask, labels pg-hero-*) on the page is removed: an
    Abu Dhabi reader gets the Abu Dhabi one only.
    """
    html = re.sub(r'\s*<div class="pg-ask" data-fs="1">.*?\n\s*</div>', "", html, count=1, flags=re.S)
    if MARKER not in html:
        m = re.search(r'</h1>\s*<p class="hero-lede">.*?</p>', html, re.S) or re.search(r"</h1>", html)
        if m:
            html = html[:m.end()] + "\n" + ad_ask_block() + html[m.end():]
    if 'id="pg-ad-css"' not in html:
        html = html.replace("</head>", CSS + "</head>", 1)
    return _WA_HREF.sub(_prefix_href, html)
