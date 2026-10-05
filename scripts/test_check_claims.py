#!/usr/bin/env python3
"""Regression test for check_claims.py.

Ported from topchallenger-site on 2026-10-05 with the guard. The MUST_FIRE and
MUST_NOT_FIRE cases are that site's history, kept verbatim: it is the same
vehicle and the same guard, so they hold the same contract here.

Every published page passing is an invariant here too, since 2026-10-05: the
26 pages that carried findings when the gate was ported were corrected the same
day (see CLAIMS-CLEANUP-2026-10-05.md). If this fails, something was deployed
around the pipeline.

    python3 scripts/test_check_claims.py

Exit 0 = all cases behave. Exit 1 = at least one case does not.

WHY THIS EXISTS
---------------
check_claims.py blocks a publish as of 2026-09-06. A guard that can skip the
day's post has to be held to both halves of its contract, because the two
failures cost different things and only one of them is loud:

  - a MISS ships a fabricated specification to a client site, silently
  - a FALSE POSITIVE skips a post, noisily, and the next person to be blocked by
    a finding they believe is wrong will reach for the ACCEPTED list to make it
    go away, which is how the whole thing decays

So every case below is a real sentence with a date, not a synthetic string. The
MUST_FIRE block is the history of what has actually gone live on this site. The
MUST_NOT_FIRE block is every legitimate shape a sourced or self-owned figure
takes here, including all three get-outs — cite it (CITED), disclaim it
(DISCLAIMER), or record it as reviewed (ACCEPTED).

Adding a sentence to check_claims.ACCEPTED without adding it here is how a
silenced finding becomes permanent.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_claims                                          # noqa: E402

SITE = Path(__file__).parent.parent

PAGE = """<!doctype html><html><head>
<title>{title}</title>
<meta name="description" content="{desc}">
</head><body>{extra}<article>{body}</article>
<p><a href="https://wa.me/971500000000">WhatsApp us</a></p>
</body></html>"""

NEUTRAL_TITLE = "Y62 servicing in Dubai"
NEUTRAL_DESC = "What we check and why."

# The WhatsApp link at the foot of every page is deliberate: it is the exact
# thing that once suppressed every finding on the site, back when any outbound
# link counted as a citation. If it ever counts again, MUST_FIRE goes quiet.

MUST_FIRE = [
    # --- the four that went live, in order -----------------------------------
    ("2026-08-23 /y62-transmission-fluid-change-interval-dubai",
     "<p>Factory-published data for Middle East-specification Y62 models cites a "
     "40,000 km change interval for the transmission fluid.</p>"),

    ("2026-09-06 /best-engine-oil-for-y62-dubai, the European schedule",
     "<p>The European service schedule allows up to 15,000 km between changes "
     "under normal conditions.</p>"),

    # This one turned out to be TRUE and kept its attribution. It must still
    # fire: the check cannot verify anything, and flagging a claim that survives
    # review is the system working, not a false positive.
    ("2026-09-06 /best-engine-oil-for-y62-dubai, the 0W-20 attribution",
     "<p>0W-20 appears in some international Nissan documentation for this engine "
     "in certain markets.</p>"),

    ("2026-09-06 /y62-engine-oil-consumption-dubai, NS-2 (a CVT fluid)",
     "<p>The VK56VD calls for a 5W-30 fully synthetic meeting Nissan's NS-2 "
     "specification or equivalent.</p>"),

    ("2026-09-06 /y62-transmission-overheating-dubai, NS-3 (also a CVT fluid)",
     "<p>The JR710E holds roughly eight litres of Nissan NS-3 ATF in normal "
     "operation, though the full system capacity including the cooler lines is "
     "higher.</p>"),

    ("2026-09-06 /y62-transmission-overheating-dubai, the 60,000 km interval",
     "<p>The factory service interval for the JR710E is often quoted at 60,000 km "
     "under normal conditions.</p>"),

    # A meta description reaches more people than the page. Both halves of this
    # pair are needed and neither trips alone, which is how it survived a
    # body-copy fix and stayed live in the description.
    ("meta description, evaluated whole rather than sentence-split",
     "<p>Nothing to see in the body.</p>",
     {"desc": "Forty thousand kilometres is the interval we work to. UAE heat "
              "degrades it faster than the factory chart assumes."}),

    ("title, same rule",
     "<p>Nothing to see in the body.</p>",
     {"title": "The factory 10,000 km figure and why it does not fit Dubai"}),
]

MUST_NOT_FIRE = [
    # --- ACCEPTED: reviewed attributions, recorded with their reason ---------
    ("ACCEPTED, the glovebox-checkable interval",
     "<p>The owner's manual sets a 10,000 km or 12 month service interval. That is "
     "a global figure for a car sold into a great many markets, and Dubai is at "
     "the far end of what any of them have to cope with.</p>"),

    ("ACCEPTED, the same figure in its second phrasing",
     "<p>In Dubai, the practical engine oil change interval for a Y62 is 5,000 to "
     "7,500 km, rather than the 10,000 km in the owner's manual.</p>"),

    ("ACCEPTED, 0W-20 traced to the Armada manual (body form)",
     "<p>Nissan does specify 0W-20 for this engine in some markets: the North "
     "American owner's manual for the Armada, which uses the same VK56VD, asks for "
     "it by name.</p>"),

    ("ACCEPTED, 0W-20 traced to the Armada manual (FAQ form)",
     "<p>Nissan's North American owner's manual for the Armada, which uses the "
     "same VK56VD, recommends 0W-20, so the grade is not wrong for the engine.</p>"),

    # --- DISCLAIMER: the sentence owns the figure itself ---------------------
    ("DISCLAIMER, the 40,000 km fix",
     "<p>Forty thousand kilometres is the interval we work to, and it is our own "
     "figure rather than a published one: the owner's manual treats this gearbox "
     "as fill-for-life and sets no change interval at all.</p>"),

    ("DISCLAIMER, the NS-2 fix",
     "<p>The VK56VD wants a fully synthetic 5W-30, and that is our own "
     "recommendation rather than a published specification.</p>"),

    ("DISCLAIMER, the NS-3 fix",
     "<p>The JR710E takes Matic S ATF, and holds roughly eight litres of it in "
     "normal operation. Eight litres is our own working figure: Nissan names the "
     "fluid but publishes no fill capacity for this gearbox.</p>"),

    # --- CITED: a link to an authority that actually backs the sentence ------
    ("CITED, a genuine manufacturer link",
     '<p>Nissan specifies a 10,000 km service interval for this car '
     '(<a href="https://www.nissan-me.com/owners/maintenance-and-repair.html">'
     'Nissan Middle East</a>).</p>'),

    # --- shapes that are not claims at all -----------------------------------
    ("'Nissan Patrol' is a model name, not an authority",
     "<p>The Nissan Patrol is all we work on, and we see 40,000 km between fluid "
     "changes as the sensible ceiling here.</p>"),

    ("a number without a unit is a description, not a measurement",
     "<p>The factory fitted a seven-speed automatic, and two of the three bays are "
     "set up for it.</p>"),

    # THE BOUNDARY, and it is a real gap rather than a nicety. This shipped on
    # /blog/y62-gearbox-shudder-dubai and is borrowed authority by any reading —
    # but it names no figure, and figure + authority is this check's whole
    # contract, so it is out of scope and stays out. What actually caught it was
    # check_prose, on the [NEEDS_SOURCE] marker the model left behind; had the
    # sentence been written without the marker, nothing here would have seen it.
    # Widening FIGURE to cover "a standard change interval" would mean flagging
    # every sentence that mentions a manufacturer and a service, which is most
    # of the site.
    ("out of scope: authority asserted with no figure attached",
     "<p>Nissan publishes a standard change interval for the JR710E "
     "[NEEDS_SOURCE: Nissan official UAE service schedule].</p>"),

    # Two permanent false positives came from here. Quoted customer text is not
    # the site attributing anything.
    ("a customer review quoting a figure",
     "<p>Nothing in the article body.</p>",
     {"extra": '<section class="dark"><div class="rv-strip"><div class="rv-slab">'
               '<p>Took my Nissan Patrol in at 60,000 km, the factory service was '
               'twice the price. Real experts.</p>'
               '<span class="rv-attrib">A customer, 4 months ago</span>'
               '</div></div></section>'}),
]


def _write(tmp, body, title=NEUTRAL_TITLE, desc=NEUTRAL_DESC, extra=""):
    f = tmp / "case.html"
    f.write_text(PAGE.format(title=title, desc=desc, body=body, extra=extra),
                 encoding="utf-8")
    return f


def _case(entry):
    label, body = entry[0], entry[1]
    return label, body, (entry[2] if len(entry) > 2 else {})


def main():
    failures = []
    _tmp_root = tempfile.TemporaryDirectory()   # removed at exit
    tmp_root = Path(_tmp_root.name)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        for entry in MUST_FIRE:
            label, body, kw = _case(entry)
            items = check_claims.review_items(_write(tmp, body, **kw))
            if not items:
                failures.append(f"MISS   — should have fired: {label}")
            else:
                print(f"  fires    {label}")
                for scope, auth, fig, _ in items:
                    print(f"             [{scope}] {fig!r} -> {auth!r}")

        for entry in MUST_NOT_FIRE:
            label, body, kw = _case(entry)
            items = check_claims.review_items(_write(tmp, body, **kw))
            if items:
                failures.append(f"FALSE+ — should have been quiet: {label}")
                for scope, auth, fig, sent in items:
                    failures.append(f"           [{scope}] {fig!r} -> {auth!r}: {sent[:120]}")
            else:
                print(f"  quiet    {label}")

    # ACCEPTED_SENTENCES (2026-10-05) are the only form in which generate.py
    # may state a grade, a capacity or an interval. Each must carry an ACCEPTED
    # fragment, must pass the guard on its own, and must reach the prompt, or
    # the generator is being told to write something the gate will block.
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-only-no-call-is-made")
    import generate
    if "refreshed in 2016" in generate.DUBAI_CONTEXT:
        failures.append("PROMPT — the invented 2016 refresh is back in DUBAI_CONTEXT")
    for s in check_claims.ACCEPTED_SENTENCES:
        if not any(a in s for a in check_claims.ACCEPTED):
            failures.append(f"SANCTIONED — carries no ACCEPTED fragment: {s[:80]}")
        elif check_claims.review_items(_write(tmp_root, f"<p>{s}</p>")):
            failures.append(f"SANCTIONED — the guard blocks it: {s[:80]}")
        elif f'"{s}"' not in generate.DUBAI_CONTEXT:
            failures.append(f"SANCTIONED — not in the generate.py prompt: {s[:80]}")
        else:
            print(f"  quiet    sanctioned: {s[:60]}...")

    # The published site is now an invariant, not an aspiration: with the gate
    # blocking, no new post can go live carrying a finding. If this fails, either
    # something was deployed around the pipeline or a pin has drifted.
    live = sorted(f for f in (SITE / "blog").glob("*.html") if f.name != "index.html")
    live += sorted((SITE / "services").glob("*.html"))
    live += [p for p in (SITE / "services.html", SITE / "index.html",
                         SITE / "nissan-patrol-abu-dhabi.html") if p.exists()]
    dirty = [(f, check_claims.review_items(f)) for f in live]
    dirty = [(f, i) for f, i in dirty if i]
    if dirty:
        for f, items in dirty:
            failures.append(f"LIVE   — {f.relative_to(SITE)} carries {len(items)} finding(s)")
    else:
        print(f"  quiet    all {len(live)} published page(s)")

    print()
    if failures:
        print(f"[!] check_claims regression FAILED — {len(failures)} problem(s):")
        for f in failures:
            print("    " + f)
        return 1
    print(f"[+] check_claims regression passed: {len(MUST_FIRE)} must-fire, "
          f"{len(MUST_NOT_FIRE)} must-not-fire, {len(live)} published page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
