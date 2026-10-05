#!/usr/bin/env python3
"""Flag generated copy that asserts a model-year, facelift or generation split.

    python3 scripts/check_model_years.py                     # everything that ships
    python3 scripts/check_model_years.py blog/some-slug.html  # one live post
    python3 scripts/check_model_years.py drafts/some-slug.html  # pre-publish review

Exit 0 = nothing to review. Exit 2 = REVIEW REQUIRED.

Exit 2 BLOCKS A PUBLISH. run_pipeline.py runs this as a pre-publish stage and
treats any non-zero code as a stage failure, so a post that trips it is never
deployed and the keyword stays `pending` for the next run. That changed on
2026-08-24 — see WHY THIS BLOCKS NOW at the bottom. Run by hand it is still just
a report.

Ported from topchallenger-site on 2026-10-05 with the rules unchanged; the
history below happened there, on the same vehicle, and is why the rule exists.
run_pipeline.py runs this as a BLOCKING pre-publish stage on this site too.

WHY THIS EXISTS
---------------
On 2026-08-23 an audit found the site asserting a "2016 facelift" of the Nissan
Patrol Y62 across five posts, twelve times. Nissan never facelifted the Y62 in
2016 — the facelifts were 2014 and 2020. The generator invented a model year and
then built a behavioural taxonomy on top of it: different calibrations for
pre-2016 and post-2016 cars, different shift maps, different failure onset. One
instance told owners of pre-2016 cars their engine lacked VVEL, when every
VK56VD has had VVEL since the engine replaced the VK56DE at the end of 2009.

Nothing questioned it because nothing was looking. Each individual sentence read
plausibly; the invention was only visible in aggregate.

WHY THIS BLOCKS NOW
-------------------
This shipped on 2026-08-23 as an advisory check, on the reasoning that a
model-year distinction is not automatically wrong — "on UAE roads since 2010"
and "post-2020 Platinum models" are true and useful — and that a guard which
fails the build gets routed around.

The very next article the pipeline generated, on 2026-08-24, reinvented the
2016 facelift in four fresh sentences and published carrying them. The check
fired correctly and was ignored by design, because advisory is what advisory
means.

Two things came out of that. First, generate.py was the cause: its prompt listed
2016 as a grounded facelift year and offered "post-2016 cars" as a GOOD example,
so the model was following instructions. That is fixed. Second, a failure that
recurs on every run cannot be cleaned up by hand afterwards, so this is now a
blocking pre-publish stage. A blocked run costs one article; a published
invention costs a correction pass and lives on the site until someone notices.

Exit 2 rather than 1 is kept so a human running it directly can still tell
"needs review" apart from a crash, and so check_claims.py keeps the same
contract. That one blocks too, since 2026-09-06 and for the same reason: it
caught four borrowed-authority claims in a week, two of them outright false, and
was overruled by its own exit code every time.

"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shipped_pages

SITE = Path(__file__).parent.parent

# Years that are verifiable for this vehicle. 2010 is the Y62's launch; 2020 is
# a real facelift. Everything else needs a human to check a Nissan document.
VERIFIED_YEARS = {"2010", "2020"}

TRIGGERS = [
    ("facelift/generation split",
     re.compile(r"\b(?:pre|post)[- ](?:facelift|20\d\d)\b", re.I)),
    ("named facelift year",
     re.compile(r"\b(20\d\d)\s+facelift\b", re.I)),
    ("facelift assertion",
     re.compile(r"\bfacelifts?\b(?!\s*$)", re.I)),
    ("generation split",
     re.compile(r"\b(?:earlier|later|newer|older)\s+cars\b", re.I)),
    ("model-year claim",
     re.compile(r"\b(?:from|since|until|before|after)\s+(20\d\d)\b", re.I)),
]


def visible_text(html_text):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def review_items(path):
    text = visible_text(path.read_text(encoding="utf-8"))
    out = []
    for sent in sentences(text):
        if len(sent) > 400:
            continue
        for label, pat in TRIGGERS:
            m = pat.search(sent)
            if not m:
                continue
            years = set(re.findall(r"\b(20\d\d)\b", sent))
            # A sentence whose only years are verified ones, with no facelift or
            # generation language, is fine. Anything else goes to a human.
            unverified = years - VERIFIED_YEARS - {"2026"}
            # A pre-/post-YYYY construction is only suspect when YYYY is not a
            # verified year. "post-2020 Platinum models" is a true statement
            # about a real facelift and must not be flagged forever, or the
            # check becomes noise people learn to ignore. "post-2016" still
            # flags, because 2016 is not in VERIFIED_YEARS.
            boundary_years = set(re.findall(r"(?:pre|post)[- ](20\d\d)", sent, re.I))
            hard = (
                re.search(r"facelift(?![- ])", sent, re.I)
                or re.search(r"(?:pre|post)[- ]facelift", sent, re.I)
                or bool(boundary_years - VERIFIED_YEARS)
                or re.search(r"(?:earlier|later|newer|older)\s+cars", sent, re.I)
            )
            if not unverified and not hard:
                continue
            out.append((label, sorted(unverified), sent))
            break
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
        print(f"\n  {f.relative_to(SITE) if SITE in f.parents else f}")
        for label, years, sent in items:
            yr = f" [unverified year: {', '.join(years)}]" if years else ""
            print(f"     · {label}{yr}\n       {sent[:230]}")

    if total:
        # flagged, not len(files): len(files) is the set SCANNED, so this line
        # read "across 11 file(s)" when 8 of the 11 carried anything.
        print(f"\n[!] REVIEW REQUIRED — {total} model-year / generation assertion(s) "
              f"across {flagged} of {len(files)} file(s) scanned.")
        print("    Verify each against Nissan documentation before publishing.")
        print("    The Y62 facelifts are 2014 and 2020. There was NO 2016 facelift; a "
              "whole\n    taxonomy was once built on that invention — see this script's docstring.")
        print("    Unverifiable? Remove the distinction. Do not soften it.\n")
        return 2

    print(f"[+] Model-year check: {len(files)} file(s), nothing to review.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
