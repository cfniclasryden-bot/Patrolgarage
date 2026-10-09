#!/usr/bin/env python3
"""Business-copy rules shared by check_prose.py, check_model_years.py and
(Round 6) check_claims.py.

Added 2026-10-05, after a cleanup of this site found the same four defects on
page after page, none of which any guard was looking for:

  PRICE        an AED figure, a dirham amount or a dealer/labour total. The
               no-prices rule applies to both sites: a number the reader
               takes as a quote is a commitment nobody priced.
  Y61_SERVICE  the Y61 / Super Safari presented as work the business takes on.
               Both sites service the Y62 only; the Y61 may appear as a
               comparison, never as a job ("we fit snorkels to the Y61").
  TENURE       years in business, or a count of cars / customers / jobs
               ("10+ years", "serviced thousands of Patrols", "over a
               decade"). None of these was ever true of anything checkable.
  REFRESH      "refreshed in 2016", "pre-refresh", "mid-cycle", "the 2020
               refresh": refresh or update wording tied to a year. The 2016
               "refresh" is the same invention as the 2016 facelift that
               check_model_years already blocks, in a word it did not know.

Round 3 (also 2026-10-05) added four unverified-figure rules:

  HORSEPOWER   any power figure ("400 hp", "450-500hp", "210 horsepower").
               None was ever sourced, and "400 hp" was repeated on 19 pages.
  TORQUE       any torque figure in Nm ("560 Nm", "18 to 20 Nm").
  Y63_DETAIL   a Y63 launch year (2024 or earlier) or a Y63 spec: a
               displacement, the VR3x engine code, "9-speed". The Y63 is
               described as a twin-turbo V6 and nothing more.
  GRADE_0W20   "0W-20", unless the sentence carries an approved check_claims
               ACCEPTED wording (the Armada-manual sentence).

Round 4 (2026-10-05) added two more, the same shape:

  GRADE_5W30   "5W-30", with the same ACCEPTED exemption. Patrolgarage stated
               it as a requirement on four pages with no source.
  INTERVAL_10K_6M  "10,000 km or 6 months". The interval the owner's manual
               actually sets (verified on topchallenger) is 10,000 km or 12
               months, so "6 months" was a wrong figure, not just an unsourced
               one.

Round 5 (2026-10-05) generalised the last two and added an offer rule:

  OIL_GRADE    ANY oil grade (0W-20, 5W-30, 5W-40, 10W-40, 20W-50...), with the
               ACCEPTED exemption. Replaces GRADE_0W20 and GRADE_5W30.
  INTERVAL_KM_MONTHS  any "N km or N months" service interval ("5,000 km or
               3 months", "10,000 km or 6 months"), ACCEPTED exempt. Replaces
               INTERVAL_10K_6M.
  MOD_OFFER    a modification or upgrade (turbo kit, supercharger, performance
               intake or exhaust, ECU tuning or remap, lift kit, suspension
               lift, stereo or audio upgrade, body kit, NISMO kit, performance
               parts, intercooler upgrade) presented as a service: the term plus
               a first-person business subject or booking / quote wording, in
               one sentence, not negated. Neither business does modifications.
               Neutral owner information ("after a lift kit has been fitted by a
               third party...", "aftermarket parts can affect the warranty")
               passes, because it offers nothing.

Round 6 (2026-10-09) added two unverifiable-claim rules. They are NOT in
sentence_findings(), so check_prose never sees them: check_claims.py calls
unverified_claims() instead, which puts a hit through the ONE claims
regenerate (run_pipeline feeds check_claims' sentences back to generate.py)
instead of a hard prose block with no retry. Found on the auto-published
y62-liwa-trip-preparation-uae:

  CROWD        a crowd or volume count followed by a claim about what those
               people or cars do: "hundreds of Patrols make the same drive",
               "most owners skip it", "many Patrols run hot". Nobody counted.
               "Thousands of kilometres" (a unit) and "most owners." with no
               claim after it do not fire.
  FIRST_HAND   a first-hand workshop observation: "the ones we see",
               "we often see / find", "we regularly see", "in our experience",
               "most cars we get", "the component we see". Neither site knows
               which cars have been through a workshop, and Patrolgarage has no
               premises at all. A general statement of the mechanism is the
               replacement ("fluid left too long can contribute to wear").

Kept in one module, identical in topchallenger-site and Patrolgarage, so the
two sites cannot drift. A rule can be switched off for ONE site in that
repo's copy_rules_site.py (DISABLED = {...}); topchallenger disables
OIL_GRADE, because its oil-grade post states grades as the workshop's own
recommendation, which is that site's call and not an unverified figure. test_copy_rules.py holds every rule against sentences
that must fire and sentences that must not.

Sentence-level and deliberately narrow. TENURE and Y61_SERVICE need a
first-person business subject in the same sentence, because "the Y62 has been
on UAE roads since 2010" and "the Y61 uses a TB48" are true and wanted. A
sentence that negates the service ("the Y61 falls outside what we service") is
the correct statement, not the defect.
"""
import html
import re

YEAR = r"(?:19|20)\d\d"

PRICE = re.compile(
    r"\bAED\s?\d|\d[\d,.]*\s?(?:k\s)?AED\b|\bdirhams?\b|\bDhs?\.?\s?\d", re.I)

REFRESH = re.compile(
    rf"\b(?:pre|post)[- ]refresh\b|\bmid[- ]cycle\b"
    rf"|\brefresh(?:es|ed)?\b[^.!?]{{0,40}}\b{YEAR}\b"
    rf"|\b{YEAR}(?:\s*[-–]?\s*(?:onwards?|and later))?\s+(?:refresh|update)(?:es|ed|s)?\b"
    rf"|\bRefreshed\s+{YEAR}", re.I)

FIRST_PERSON = re.compile(
    r"\b(?:we|we've|we're|we'll|our|us)\b|\bPatrol Garage\b|\bTop Challenger\b", re.I)

Y61 = re.compile(r"\b(?:Y61|Super Safari)\b", re.I)
SERVICE = re.compile(
    r"\b(?:servic\w*|repair\w*|fit|fits|fitted|fitting|diagnos\w*|rebuild\w*|"
    r"work(?:s|ing)? on|specialis\w*|specializ\w*|handle\w*|take on|bring|"
    r"book\w*|stock\w*|install\w*|inspect\w*|maintain\w*|experience)\b", re.I)
NEGATION = re.compile(
    r"\b(?:not|no longer|never|outside|only (?:the )?Y62|Y62[- ]only|except|"
    r"instead|rather than|isn't|aren't|doesn't|don't)\b", re.I)

TENURE_ALWAYS = re.compile(
    r"\b\d+\+?\s*years?\s+(?:in business|of experience|experience|specialis\w*|"
    r"specializ\w*|trading|serving)\b"
    r"|\byears in business\b"
    r"|\b\d[\d,]*\+?\s+(?:Patrols|cars|vehicles|customers|trucks|jobs|owners)\s+"
    r"(?:serviced|repaired|fixed|completed|served|helped)\b", re.I)
TENURE_FIRST_PERSON = re.compile(
    r"\b(?:over|more than) (?:a|one|two) decades?\b(?! old)"
    r"|\bfor (?:\d+|many|several) years\b"
    rf"|\bsince (?:{YEAR}|(?:the model|it|they) launched)\b"
    r"|\b(?:hundreds|thousands|dozens|\d[\d,]*\+?)\s+of\s+(?:Patrols|Y6[123]s?|"
    r"cars|vehicles|customers|trucks|owners|transmissions|engines|jobs|"
    r"gearboxes|overheated Patrols)\b", re.I)

HORSEPOWER = re.compile(r"\b\d{2,3}(?:,\d{3})?\s?-?(?:hp|bhp|horsepower|PS)\b", re.I)
TORQUE = re.compile(r"\b\d+(?:\.\d+)?(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?)?\s?Nm\b")
Y63_WORD = re.compile(r"\bY63\b", re.I)
Y63_YEAR = re.compile(
    r"\bY63\b[^.!?]{0,80}?\b(?:launch\w*|introduc\w*|arriv\w*|releas\w*|debut\w*|"
    r"unveil\w*|landed|since|from|in|\()\s*(?:the UAE |UAE showrooms |showrooms |the GCC |"
    r"late |early )?(?:in )?(?:20(?:0\d|1\d|2[0-4]))\b"
    r"|\b20(?:0\d|1\d|2[0-4])\b[^.!?]{0,20}\bY63\b", re.I)
Y63_SPEC = re.compile(r"(?<![\d.])(?!5\.6)\d\.\d\s?-?(?:L|litre|liter)\b|\bVR3\d\w*|\b9-speed\b", re.I)
OIL_GRADE = re.compile(r"\b\d{1,2}W-?\d{2,3}\b", re.I)   # engine AND gear oil (75W-140)
INTERVAL_KM_MONTHS = re.compile(
    r"\b\d{1,3}(?:,\d{3})?\s?(?:km|kilomet\w+)\s+or\s+(?:every\s+)?"
    r"(?:\d+|one|two|three|four|six|twelve)[\s-]*months?\b", re.I)
MOD_TERM = re.compile(
    r"\b(?:turbo(?:charger)?\s+(?:kits?|upgrades?|conversions?|install\w*|setups?|builds?)"
    r"|(?:twin|single)[- ]turbo\s+(?:kits?|upgrades?|conversions?|setups?|builds?)"
    r"|supercharg\w*"
    r"|(?:cold[- ]air|performance|aftermarket)\s+intakes?|intake\s+upgrades?"
    r"|(?:performance|aftermarket|sports?|cat[- ]back|straight[- ]through)\s+exhausts?"
    r"|exhaust\s+(?:upgrades?|mods?|modifications?)"
    r"|ECU\s+(?:tun\w*|remap\w*|flash\w*)|remap\w*|(?:performance|dyno|engine|ECU)\s+tuning|tuning\s+(?:packages?|services?|work)"
    r"|lift\s+kits?|suspension\s+lifts?|body\s+lifts?"
    r"|(?:stereo|audio|sound system|speaker|head unit)\s+(?:upgrades?|install\w*|fit\w*)"
    r"|body\s+kits?|nismo\s+kits?"
    r"|performance\s+(?:parts|upgrades?|mods?|modifications?)"
    r"|intercooler\s+(?:upgrades?|kits?|install\w*))\b", re.I)
OFFER = re.compile(
    r"\b(?:book\w*|get (?:a|your|an) (?:exact |free )?quote|quote (?:you|the job|it)|"
    r"we (?:fit|install|supply|offer|do|can|will|carry|stock))\b", re.I)

# Round 6 (2026-10-09): unverifiable crowd counts and first-hand observations.
# Checked by check_claims.py through unverified_claims(), never by check_prose.
_QUAL = r"(?:(?:Y62|Patrol|Nissan|UAE|Dubai|Abu Dhabi|local|other|desert|weekend)\s+){0,3}"
CROWD = re.compile(
    rf"\b(?:(?:hundreds|tens) of thousands|hundreds|thousands|dozens|scores)\s+of\s+{_QUAL}"
    r"(?:Patrols?|Y62s?|owners|drivers|families|people|enthusiasts|motorists|customers|"
    r"cars|vehicles|4x4s|SUVs|trucks)\b"
    rf"|\b(?:most|many|plenty of|the majority of|countless|a lot of|lots of|nearly all|"
    rf"almost all|a large number of)\s+{_QUAL}"
    r"(?:owners|drivers|Patrols|Y62s|families|people|enthusiasts|motorists|customers)\b", re.I)
# The claim after the count: a verb within the next few words. "most owners."
# or "for most owners" at a sentence end states nothing about anybody.
CROWD_CLAIM = re.compile(
    r"^\s*(?:'s\s+)?(?:[\w-]+\s+){0,4}?(?:\w+(?:s|ed)|are|were|is|was|do|don't|drive|make|run|"
    r"use|take|get|go|have|had|think|know|skip|ignore|leave|choose|prefer|need|want|buy|"
    r"head|find|treat|wait|tow|carry|come|bring|book|change|end|forget|miss|keep|try|"
    r"tend|will|would|can|never|rarely|only|still|already|just|also|often|usually|"
    r"swear|rely|drop|fit|spend|pay|learn|discover|underestimate|overlook)\b", re.I)
FIRST_HAND = re.compile(
    r"\b(?:the|those)\s+ones\s+we\s+(?:see|get|find)\b"
    r"|\bwe\s+(?:often|regularly|frequently|usually|commonly|typically|routinely|always|"
    r"constantly|repeatedly|tend\s+to)\s+(?:see|find|get|notice|come\s+across|deal\s+with|"
    r"hear|meet|replace|fix|repair|catch)\b"
    r"|\bin\s+our\s+(?:own\s+)?experience\b"
    r"|\b(?:most|many|plenty\s+of|a\s+lot\s+of)\s+(?:of\s+the\s+)?(?:cars?|Patrols?|Y62s?|vehicles|"
    r"gearboxes|engines|jobs)\s+(?:that\s+)?we\s+(?:see|get|work\s+on|service|repair|inspect|handle)\b"
    r"|\bwe\s+see\s+(?:a\s+lot|plenty|many|most|(?:this|it|them)\s+(?:a\s+lot|often|regularly|"
    r"all\s+the\s+time|every\s+week))\b"
    r"|\b(?:component|part|fault|problem|failure|issue|mistake)s?\s+(?:that\s+)?we\s+see\b", re.I)
UNVERIFIED_RULES = ("CROWD", "FIRST_HAND")

try:                                   # per-site switches; see the docstring
    from copy_rules_site import DISABLED
except ImportError:
    DISABLED = set()


def _accepted_fragments():
    try:
        import check_claims
        return tuple(check_claims.ACCEPTED)
    except Exception:
        return ()


MAX_SENTENCE = 300   # longer "sentences" are navigation and footer run together


def sentences(text):
    """Split on sentence ends AND on line breaks: scopes() turns every block
    element boundary into a newline, so a heading, a list item or a table cell
    is never glued to the paragraph after it."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def sentence_findings(sent):
    """[(rule, matched text)] for one sentence."""
    out = []
    m = REFRESH.search(sent)
    if m:
        out.append(("REFRESH", m.group(0)))
    m = PRICE.search(sent)
    if m:
        out.append(("PRICE", m.group(0)))
    for rule, rx in (("HORSEPOWER", HORSEPOWER), ("TORQUE", TORQUE)):
        m = rx.search(sent)
        if m:
            out.append((rule, m.group(0)))
    if Y63_WORD.search(sent):
        m = Y63_YEAR.search(sent) or Y63_SPEC.search(sent)
        if m:
            out.append(("Y63_DETAIL", m.group(0)))
    for rule, rx in (("OIL_GRADE", OIL_GRADE), ("INTERVAL_KM_MONTHS", INTERVAL_KM_MONTHS)):
        m = rx.search(sent)
        if m and not any(a in sent for a in _accepted_fragments()):
            out.append((rule, m.group(0)))
    if len(sent) <= MAX_SENTENCE:
        if (Y61.search(sent) and FIRST_PERSON.search(sent) and SERVICE.search(sent)
                and not NEGATION.search(sent)):
            out.append(("Y61_SERVICE", Y61.search(sent).group(0)))
        m = TENURE_ALWAYS.search(sent)
        if not m and FIRST_PERSON.search(sent):
            m = TENURE_FIRST_PERSON.search(sent)
        if m:
            out.append(("TENURE", m.group(0)))
        m = MOD_TERM.search(sent)
        if m and (FIRST_PERSON.search(sent) or OFFER.search(sent)) and not NEGATION.search(sent):
            out.append(("MOD_OFFER", m.group(0)))
    return [f for f in out if f[0] not in DISABLED]


def unverified_claims(sent):
    """[(rule, matched text)] for Round 6 (CROWD, FIRST_HAND), one sentence.

    Called by check_claims.review_items(), deliberately not by
    sentence_findings(): a hit here blocks at the claims gate, so the pipeline
    regenerates once with the sentence fed back, as for any other claims hit.
    """
    out = []
    if len(sent) > MAX_SENTENCE:
        return out
    for m in CROWD.finditer(sent):
        # "for most owners in the city this is a local trip", "applies to most
        # Y62 Patrols": a scope, not a claim about what anybody does.
        if re.search(r"\b(?:for|to)\s+$", sent[:m.start()], re.I):
            continue
        if CROWD_CLAIM.match(sent[m.end():]):
            out.append(("CROWD", m.group(0)))
            break
    m = FIRST_HAND.search(sent)
    if m:
        out.append(("FIRST_HAND", m.group(0)))
    return [f for f in out if f[0] not in DISABLED]


def scopes(raw):
    """(label, text) for everywhere copy reaches a reader or a SERP: visible
    text, <title>, meta descriptions, and the JSON-LD strings (FAQ answers are
    duplicated there and are what rich results show)."""
    # Site chrome (header, nav, footer) is navigation, not copy. Left in, the
    # <title>, the nav labels and the hero heading run together into one short
    # "sentence" — "... Y61 ... Patrol Garage ... Services ..." — and read as a
    # service claim. Found on the first full run, 2026-10-05.
    vis = re.sub(r"<(script|style|header|nav|footer)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    vis = re.sub(r"<!--.*?-->", " ", vis, flags=re.S)
    vis = re.sub(r"</?(?:p|li|h[1-6]|td|th|tr|div|section|ul|ol|br|dt|dd|blockquote|table)\b[^>]*>",
                 "\n", vis, flags=re.I)
    vis = re.sub(r"<[^>]+>", " ", vis)
    vis = html.unescape(vis)
    vis = re.sub(r"[ \t\r\f\v]+", " ", vis)
    yield "body", re.sub(r"\s*\n\s*", "\n", vis).strip()
    m = re.search(r"<title>(.*?)</title>", raw, re.S | re.I)
    if m:
        yield "title", html.unescape(re.sub(r"\s+", " ", m.group(1)))
    for m in re.finditer(r'<meta\s+(?:name|property)="(?:description|og:description|'
                         r'twitter:description|og:title|twitter:title)"\s+content="([^"]*)"',
                         raw, re.I):
        yield "meta", html.unescape(m.group(1))
    no_comments = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    for m in re.finditer(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', no_comments, re.S | re.I):
        for s in re.findall(r'"(?:text|description|name|headline|abstract)"\s*:\s*'
                            r'"((?:[^"\\]|\\.)*)"', m.group(1)):
            yield "json-ld", s


def page_findings(raw):
    """[(scope, rule, matched, sentence)] across every scope of one page."""
    out = []
    for scope, text in scopes(raw):
        for sent in sentences(text):
            for rule, hit in sentence_findings(sent):
                out.append((scope, rule, hit, sent))
    # One sentence can sit in the body AND in the FAQ JSON-LD; report it once
    # per scope, but never twice in the same scope.
    seen, uniq = set(), []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq
