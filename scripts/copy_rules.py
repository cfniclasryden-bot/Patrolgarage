#!/usr/bin/env python3
"""Business-copy rules shared by check_prose.py and check_model_years.py.

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

Kept in one module, identical in topchallenger-site and Patrolgarage, so the
two sites cannot drift. A rule can be switched off for ONE site in that
repo's copy_rules_site.py (DISABLED = {...}); topchallenger disables
GRADE_0W20, because its oil-grade post states grades as the workshop's own
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
GRADE_0W20 = re.compile(r"\b0W-?20\b", re.I)

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
    m = GRADE_0W20.search(sent)
    if m and not any(a in sent for a in _accepted_fragments()):
        out.append(("GRADE_0W20", m.group(0)))
    if len(sent) <= MAX_SENTENCE:
        if (Y61.search(sent) and FIRST_PERSON.search(sent) and SERVICE.search(sent)
                and not NEGATION.search(sent)):
            out.append(("Y61_SERVICE", Y61.search(sent).group(0)))
        m = TENURE_ALWAYS.search(sent)
        if not m and FIRST_PERSON.search(sent):
            m = TENURE_FIRST_PERSON.search(sent)
        if m:
            out.append(("TENURE", m.group(0)))
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
