#!/usr/bin/env python3
"""Flag figures attributed to an external authority with nothing backing them.

    python3 scripts/check_claims.py                  # everything that ships
    python3 scripts/check_claims.py path.html ...    # named files, incl. drafts/

Exit 0 = clean. Exit 2 = REVIEW REQUIRED, and since 2026-09-06 that BLOCKS a
publish: run_pipeline.py runs this as a pre-publish stage, scoped to the post
being written.

Ported from topchallenger-site on 2026-10-05 with the rules unchanged; the
history below happened there, on the same vehicle, and is why the rule exists.
run_pipeline.py runs this as a BLOCKING pre-publish stage on this site too.

WHY THIS EXISTS
---------------
Sibling of check_model_years.py, and the same class of failure: a fluent,
confident claim of external authority that nothing ever verified.

check_model_years.py catches an invented *taxonomy* — a 2016 facelift that does
not exist, with twelve instances of behaviour attributed to it. This catches an
invented *citation*: a number handed to the reader as though a manufacturer
published it.

The case it was written for, on /blog/y62-transmission-fluid-change-interval-dubai:

    "Factory-published data for Middle East-specification Y62 models cites a
     40,000 km change interval for the transmission fluid."

No such figure could be found in Nissan literature. The Y62 owner's manual
appears to treat the automatic transmission fluid as maintenance-free and
publishes no change interval at all; 40,000 km is what service centres and
workshops recommend. The number may well be sound advice — it is the word
"factory-published" that is doing damage, because it converts a workshop's
judgement into a manufacturer's specification.

That is the exact inversion worth catching. The workshop's own experience is the
site's strongest asset and needs no citation. Borrowed authority it cannot
produce is a liability.

WHY IT BLOCKS, AND WHY EXIT 2 AND NOT 1
---------------------------------------
This was advisory from 2026-08-23 to 2026-09-06, on the reasoning that plenty of
what it flags is fine — "the 10,000 km service interval Nissan prints in the
owner's manual" is checkable and probably true — and that a guard failing on
judgement calls gets routed around.

What ended that: two of the four claims caught in the first week were not
uncited-but-true, they were FALSE. A 5W-30 "meeting Nissan's NS-2 specification"
and a JR710E holding "eight litres of Nissan NS-3 ATF" — NS-2 and NS-3 are both
CVT fluids, named for a car that has no CVT. The model had invented the
authority, not just borrowed it. All four published, and each needed a hand
correction afterwards.

So the check itself was never the weak part. It flagged all four at the right
moment and its own exit code said carry on. A skipped post and a line in the run
log is a cheaper failure than a fabricated technical specification on a client
site, and the three get-outs below mean a legitimate citation is never blocked:
link the source (CITED), disclaim the authority in the sentence (DISCLAIMER), or
record a reviewed attribution in ACCEPTED.

Exit 2 rather than 1 is kept so a human running it directly can still tell "needs
review" from a crash. run_pipeline.py treats any non-zero as a stage failure, so
blocking needs no special casing. Same contract as check_model_years.py.

scripts/test_check_claims.py holds this behaviour against the real sentences —
every historical case must fire, every accepted and disclaimed form must not.

"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shipped_pages
import copy_rules

SITE = Path(__file__).parent.parent

# Words that claim someone else's authority for a statement.
AUTHORITY = re.compile(
    # "Nissan" only counts as an authority when it is NOT the model name.
    # "the Nissan Patrol is all we work on" attributes nothing to anybody.
    r"\b(?:Nissan(?!\s+Patrol)|manufacturer'?s?|factory[- ]?(?:published|specified|set)?|"
    r"official(?:ly)?|published|owner'?s manual|service schedule|"
    r"maintenance schedule|specification|spec sheet|OEM|"
    r"the book(?: figure| interval)?|factory chart)\b", re.I)

# A specific figure: a distance, volume, temperature, pressure, viscosity,
# percentage, or a bare number with a unit. Deliberately not every digit —
# "seven-speed" is a description, not a cited measurement.
#
# SPELLED-OUT numbers are included since 2026-08-23. "Forty thousand kilometres"
# is the same claim as "40,000 km" and the digit-only pattern walked straight
# past it: a description reading "UAE heat degrades it faster than the factory
# chart assumes" alongside "Forty thousand kilometres is the interval" was found
# by reading, not by the guard.
_NUM = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
        r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million)")
_UNIT = (r"(?:km|kilometres?|kilometers?|miles?|litres?|liters?|degrees?|"
         r"months?|years?|bar|psi|Nm|kPa|per ?cent|percent)")
# A unit is REQUIRED. "two of the three bays" and "seven-speed" must not match,
# so the number run has to be followed directly by a measurement word.
_SPELLED = rf"\b{_NUM}(?:[\s-]+(?:{_NUM}|and|to))*[\s-]+{_UNIT}\b"

FIGURE = re.compile(
    r"\b\d{1,3}(?:,\d{3})+\s?(?:km|kilometres|kilometers|miles)\b"
    r"|\b\d{1,6}\s?(?:km|kilometres|kilometers|miles)\b"
    r"|\b\d+(?:\.\d+)?\s?(?:L|litres?|liters?|ml)\b"
    r"|\b\d+\s?(?:degrees?\s?C|°C)\b"
    r"|\b\d{1,2}W-\d{2}\b"
    r"|\bDOT\s?\d\b"
    r"|\b\d+(?:\.\d+)?\s?(?:bar|psi|Nm|kPa)\b"
    r"|\b\d+\s?(?:months?|years?)\b"
    r"|\b\d+\s?%"
    rf"|{_SPELLED}", re.I)

# Anything that would count as actually backing the claim up. Deliberately a
# WHITELIST: the first version treated any outbound link as a citation, which
# meant the WhatsApp contact link on every page suppressed every finding and the
# check reported a clean site. A contact link is not a source.
CITED = re.compile(
    r"<a\b[^>]*href=\"https?://(?:[^\"]*\.)?(?:"
    r"nissan[^\"]*|infiniti[^\"]*|sae\.org|api\.org|iso\.org|nhtsa\.gov|"
    r"jatco[^\"]*|ncm\.gov\.ae"
    r")", re.I)


# Third-party review text is quoted, not generated: a customer writing "4 months
# ago ... experts on Nissan patrol" is not the site attributing a figure to a
# manufacturer. Two permanent false positives came from the homepage reviews
# block, and permanent noise is how a check gets ignored.
#
# Done structurally, not by regex on the section's class: the reviews live in a
# plain <section class="dark">, identified only by the rv-* elements inside it.
# A class-matching regex found nothing.
REVIEW_MARKERS = ("rv-attrib", "rv-track", "rv-strip", "rv-slab")


def strip_reviews(html_text):
    """Remove any <section> containing the reviews carousel.

    Styles and scripts go FIRST: the inlined stylesheet mentions every rv-*
    class, and those hits sit in <head> before any <section> exists, so the
    search walked backwards, found nothing, and gave up without stripping a
    thing. The class names in the CSS are not the carousel.
    """
    out = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.S | re.I)
    for _ in range(6):                      # a handful of sections at most
        pos = min((out.find(m) for m in REVIEW_MARKERS if m in out), default=-1)
        if pos == -1:
            break
        start = out.rfind("<section", 0, pos)
        end = out.find("</section>", pos)
        if start == -1 or end == -1:
            break
        out = out[:start] + " " + out[end + len("</section>"):]
    return out


# A sentence that explicitly DISCLAIMS external authority is the opposite of the
# defect, and flagging it is exactly backwards. Widening FIGURE to spelled-out
# numbers made the corrected copy trip its own guard:
#
#   "Forty thousand kilometres is the interval we work to, and it is our own
#    figure rather than a published one: the owner's manual treats this gearbox
#    as fill-for-life and sets no change interval at all."
#
# That sentence is the fix. It says the number is the workshop's and that no
# published interval exists. Nothing about it needs review.
DISCLAIMER = re.compile(
    r"\bour own\b"
    r"|\brather than (?:a |the )?(?:published|manufacturer|factory|official)"
    r"|\bnot (?:a |the )?(?:published|factory|official|manufacturer)"
    r"|\bsets no\b|\bpublishes no\b"
    r"|\bno (?:published |factory )?(?:change )?interval\b", re.I)


# Attributions reviewed and accepted WITHOUT a link, with the reason. Keep this
# list short and never add to it to silence a finding — the whole value of this
# check is that it stays quiet unless something needs looking at.
ACCEPTED = {
    # Reader-checkable in their own glovebox. Nothing on nissan-me.com states an
    # interval figure: the service portfolio URL redirects to a maintenance page
    # with no numbers, and service-prices is a country-selector hub. Attributing
    # to the manual the owner already has is honest; linking a page that does
    # not contain the figure would not be.
    "The owner's manual sets a 10,000 km or 12 month service interval",
    "rather than the 10,000 km in the owner's manual",
    # 0W-20 for the VK56VD, on /blog/best-engine-oil-for-y62-dubai. Verified in
    # Nissan's own literature rather than accepted on the model's say-so: the
    # 2018 Armada owner's manual (same VK56VD) states Genuine "Nissan Motor Oil
    # 0W-20 SN" is recommended, in the capacities table on p.10-2 and again in
    # the quick-reference at the back.
    #   nissanusa.com/content/dam/Nissan/us/manuals-and-guides/armada/2018/
    #   2018-Nissan-Armada-owner-manual.pdf
    # No link in the copy because the sentence names the document precisely
    # enough for a reader to open it, same call as the 10,000 km entry above.
    # Covers both the body sentence and the FAQ answer, which were pinned to
    # share this wording. (topchallenger-site: site_config.COPY_PINS.)
    "owner's manual for the Armada, which uses the same VK56VD",
}


# The ONLY sentences generate.py may use to state a fluid grade, a capacity or a
# service interval, or to mention an owner's manual at all — copied word for
# word, unchanged. Added 2026-10-05, on topchallenger-site first; identical
# here because the vehicle and the verified facts are the same.
#
# ACCEPTED above holds fragments, which is right for matching but no use as an
# instruction: a model told it may use "rather than the 10,000 km in the owner's
# manual" writes its own sentence around it, and that is how "The VK56VD's
# owner's manual calls for 0W-20, 6.5 litres..." (2026-10-05) and "The owner's
# manual for the VK56VD sets 10,000 km or twelve months..." (2026-10-02) came to
# block two runs in a row on y62-service-cost-dubai. So each entry here is a
# whole sentence already live on the site, and test_check_claims.py holds two
# things true of every one: it contains an ACCEPTED fragment, and the guard is
# quiet on it. A sentence added here that the guard would block fails the test,
# not a 05:00 run.
ACCEPTED_SENTENCES = (
    # /blog/y62-service-interval-dubai-heat, /blog/y62-desert-driving-preparation-uae
    "The owner's manual sets a 10,000 km or 12 month service interval.",
    # /blog/y62-engine-oil-consumption-dubai
    "In Dubai, the practical engine oil change interval for a Y62 is 5,000 to "
    "7,500 km, rather than the 10,000 km in the owner's manual.",
    # /blog/best-engine-oil-for-y62-dubai
    "Nissan's North American owner's manual for the Armada, which uses the same "
    "VK56VD, recommends 0W-20, so the grade is not wrong for the engine.",
)


def visible_text(html_text):
    html_text = strip_reviews(html_text)
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def scopes(raw):
    """(label, text) for every place a claim can reach a reader.

    Originally this scanned visible body text only. That missed the SERP
    entirely: <title> and <meta name="description"> are ATTRIBUTES, stripped
    before the scan, and a meta description is read by more people than the page
    is. The "factory 10,000 km" attribution survived a body-copy fix for exactly
    that reason and stayed live in the description.
    """
    yield "body", visible_text(raw)
    m = re.search(r"<title>(.*?)</title>", raw, re.S | re.I)
    if m:
        yield "title", html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    for m in re.finditer(r'<meta\s+name="description"\s+content="([^"]*)"', raw, re.I):
        yield "meta description", html.unescape(m.group(1))
    for m in re.finditer(r'<meta\s+property="og:description"\s+content="([^"]*)"', raw, re.I):
        yield "og:description", html.unescape(m.group(1))


def review_items(path):
    raw = path.read_text(encoding="utf-8")
    out = []
    for scope_label, text in scopes(raw):
      # A title or a meta description is ONE snippet the reader sees whole, so
      # it is evaluated whole. Splitting it into sentences was how the live case
      # escaped: "Forty thousand kilometres is the interval we work to." and
      # "UAE heat degrades it faster than the factory chart assumes." are two
      # sentences, figure in the first, authority in the second, and neither
      # half trips the check on its own. Body copy stays sentence-split, or a
      # 2,000-word post would flag on any page containing both somewhere.
      units = [text] if scope_label != "body" else sentences(text)
      for sent in units:
        if scope_label == "body" and len(sent) > 400:
            continue
        # Round 6 (2026-10-09): crowd counts and first-hand workshop observations,
        # defined in copy_rules.py. Checked HERE, not in check_prose, so a hit gets
        # the claims regenerate with the sentence fed back. Same tuple shape: the
        # rule name sits where the authority goes, the matched words where the
        # figure goes. No get-out: there is no source to cite for "we often see".
        for rule, hit in copy_rules.unverified_claims(sent):
            out.append((scope_label, rule, hit, sent))
        auth = AUTHORITY.search(sent)
        fig = FIGURE.search(sent)
        if not (auth and fig):
            continue
        # Only a link to a genuine authority counts as backing. See CITED.
        # A link cannot appear in a title or a meta description at all, so the
        # get-out applies to body copy only.
        if scope_label == "body" and CITED.search(raw):
            continue
        if DISCLAIMER.search(sent):
            continue
        if any(a in sent for a in ACCEPTED):
            continue
        out.append((scope_label, auth.group(0), fig.group(0), sent))
    return out


def main(argv):
    # DEFAULT IS WHAT SHIPS, since 2026-09-18. It used to be drafts/, which meant
    # a bare run reported problems that COPY_PINS had already corrected on the
    # way to blog/ — 32 items across 9 drafts, none of them live, none of them
    # reachable by a reader. See scripts/shipped_pages.py.
    #
    # The drafts mode is NOT gone, it just needs naming. An explicit path always
    # wins, which is how run_pipeline.py calls this as a pre-publish stage
    # (blog/<slug>.html) and how a fresh draft is reviewed before assembly
    # (drafts/<slug>.html). --published is now a no-op alias for the default,
    # kept so older callers do not break.
    argv = [a for a in argv if a != "--published"]
    files = [Path(a) for a in argv] if argv else shipped_pages.shipped_pages()

    total = 0
    flagged = 0
    for f in files:
        items = review_items(f)
        if not items:
            continue
        total += len(items)
        flagged += 1
        try:
            name = f.relative_to(SITE)
        except ValueError:
            name = f
        print(f"\n  {name}")
        for scope_label, auth, fig, sent in items:
            if auth in copy_rules.UNVERIFIED_RULES:
                print(f"     · [{scope_label}] {auth}: {fig!r} (unverifiable)")
            else:
                print(f"     · [{scope_label}] attributes {fig!r} to {auth!r}")
            print(f"       {sent[:250]}")

    if total:
        # flagged, not len(files) — see the note in check_model_years.py.
        print(f"\n[!] REVIEW REQUIRED — {total} claim(s) with nothing behind them "
              f"(an uncited authority, a crowd count or a first-hand observation), "
              f"across {flagged} of {len(files)} file(s) scanned.")
        print("    For each: produce the source, or drop the attribution and keep the "
              "figure as\n    the workshop's own recommendation. A number the workshop "
              "stands behind needs\n    no citation; borrowed authority it cannot produce "
              "is a liability.\n"
              "    CROWD / FIRST_HAND: state the mechanism in general terms instead; "
              "nobody\n    counted the crowd and the site cannot vouch for the workshop's "
              "caseload.\n")
        return 2

    print(f"[+] Claims check: {len(files)} file(s), no uncited authority claims.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
