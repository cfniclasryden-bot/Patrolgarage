#!/usr/bin/env python3
"""Guard: a generated hero's alt must not assert what the picture cannot support.

    python3 scripts/check_alt.py                    # every published post
    python3 scripts/check_alt.py blog/<slug>.html   # one post
    python3 scripts/check_alt.py --repair blog/...  # fix in place, never block

Four posts have now shipped an alt describing a picture that does not exist:

    y62-cooling-ac-problems-dubai ...... "Y62 engine bay open on a workshop lift"
    y62-gearbox-shudder-dubai .......... "Y62 transmission removed on a workshop lift"
    y62-service-interval-dubai-heat .... "Y62 engine bay open on a lift"
    y62-suspension-hbmc-problems-dubai . "Nissan Patrol Y62 on a workshop lift
                                          during hydraulic suspension inspection"

In every one the bonnet is shut, nothing is on a lift, and the vehicle is not a
Y62 — it renders as a US-market Armada with a mangled non-Nissan grille mark.
The first three were rewritten by hand on 2026-08-23; the fourth published on
2026-08-24 and shipped the identical defect. Fixing instances does not fix this.
This is the check that runs every time.

PORTED from topchallenger-site on 2026-10-05, rules unchanged. The four
instances above happened there; this site's image_gen.py uses the same model
and prompt shape, and its alts were never derived from the picture at all:
assemble.py writes the post's short headline into alt=, so "Patrol 4WD Not
Engaging" names a model the picture does not reliably show. Under the same
rule every such alt is repaired to NEUTRAL_ALT, which is the intended effect.
Every hero on this site is generated: there is no site_config, no pinned
workshop photograph and no HERO_OVERRIDES, so is_generated() is always True.

SCOPE (topchallenger): generated heroes only, decided by `site_config.hero_for(slug)["pinned"]`.
A pinned hero is a real photograph of the actual workshop, and its alt is
allowed to say things this one forbids — `y62-service-diagnostics-dubai` names a
Nissan because a Nissan dashboard is in the frame, and the transmission-slipping
hero says "raised on a two-post lift" because the car is on one. Those alts are
hand-written against the photograph and are not this guard's business.

WHAT IS OBJECTIVE AND WHAT IS HEURISTIC — worth knowing before tuning it:

  * The make/model rule is objective. `image_gen.build_prompt` instructs the
    image model to render no legible badge text at all, and what comes back is
    not a Y62. So NO generated hero can support a make or model name, ever,
    regardless of what the picture looks like. This rule alone fires on all four
    instances above.

  * The state rule is a heuristic and cannot be otherwise, because whether
    "raised" is true depends on the image, which this script cannot see. It is
    tuned against the alts actually on the site: it fires on the phrasings the
    generator produces and stays silent on the three hand-written alt-only
    entries, which correctly describe a second vehicle on a lift behind the
    subject.

    Known gap, stated rather than hidden: `on a two-post lift` attributed to the
    PRIMARY subject would pass. It is not matched because two correct alts use
    that exact phrase for a background vehicle, and no regex separates those
    without reading the picture. The make/model rule is the backstop, and it
    caught all four real instances on its own.

The vision pass in `image_gen.py` validates its own output through this module
before writing it, so a fresh post should never reach the guard dirty. If one
does, `--repair` swaps in NEUTRAL_ALT and exits 0: an unattended 05:00 cron must
not stop over an alt when a safe alternative exists.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent

# The fallback, and the ceiling on what can be claimed without looking at the
# file. Everything here is true of any image build_prompt can return: it is an
# illustration, it is not a photograph of this workshop, and SUBJECT_HINT
# guarantees the subject is a large SUV. It deliberately claims nothing else.
#
# Adapted for this site: image_gen.build_prompt asks for "a Dubai workshop or
# desert setting", and this business has no workshop of its own to disclaim. It
# must also never name the partner workshop, which topchallenger's version does.
NEUTRAL_ALT = ("Illustration for this article: a large SUV in a workshop or "
               "desert setting. Not a photograph of a customer's vehicle.")

MAKE_MODEL = re.compile(
    r"\b("
    r"y6[12]|nissan|patrol|armada|nismo|infiniti|qx\d{2}|"
    r"toyota|land\s*cruiser|lexus|prado|ford|chevrolet|gmc|jeep|mitsubishi|pajero"
    r")\b", re.I)

# Each entry is (regex, what it asserts). Phrases, not bare words: "open" is in
# "open shutter door" and "raised" is in "another vehicle raised behind it",
# both of which are correct in alts currently on the site.
STATE = [
    (re.compile(r"\bon an?\s+(?:workshop\s+)?lift\b", re.I), "the subject on a lift"),
    (re.compile(r"\bengine bay open\b", re.I), "an open engine bay"),
    (re.compile(r"\bremoved\b", re.I), "a component removed"),
    (re.compile(r"\bexposed\b", re.I), "a component exposed"),
    (re.compile(r"\binspect(?:ion|ed|ing)\b", re.I), "an inspection in progress"),
    (re.compile(r"\bundergoing\b", re.I), "work in progress"),
    (re.compile(r"\bbeing\s+(?:serviced|repaired|rebuilt|worked on)\b", re.I),
     "work in progress"),
    (re.compile(r"\bdismantled|stripped down\b", re.I), "a stripped vehicle"),
]

HERO_IMG = re.compile(r'<div class="hero-bg">.*?<img[^>]*\balt="([^"]*)"',
                      re.S | re.I)


def offences(alt):
    """[(category, matched text)] — empty means the alt is safe to ship."""
    out = [("make/model", m.group(0)) for m in MAKE_MODEL.finditer(alt)]
    for rx, what in STATE:
        m = rx.search(alt)
        if m:
            out.append((what, m.group(0)))
    return out


def hero_alt(html):
    m = HERO_IMG.search(html)
    return m.group(1) if m else None


def is_generated(slug):
    """True when image_gen.py owns this post's picture: always, on this site."""
    return True  # no pinned photographs on this site; see the docstring


def _published_posts():
    return sorted(p for p in (SITE / "blog").glob("*.html") if p.name != "index.html")


def _set_alt(html, alt):
    m = HERO_IMG.search(html)
    if not m:
        return html
    s, e = m.span(1)
    return html[:s] + alt.replace('"', "&quot;") + html[e:]


def main(argv):
    repair = "--repair" in argv
    argv = [a for a in argv if a != "--repair"]
    files = [Path(a) for a in argv] if argv else _published_posts()

    checked, findings, repaired = 0, [], []
    for f in files:
        path = f if f.is_absolute() else (SITE / f)
        if not path.exists():
            print(f"  [!] missing {f}")
            return 1
        slug = path.stem
        if not is_generated(slug):
            continue
        html = path.read_text(encoding="utf-8")
        alt = hero_alt(html)
        if alt is None:
            print(f"  [!] {slug}: no hero <img alt> found")
            return 1
        checked += 1
        bad = offences(alt)
        if not bad:
            continue
        if repair:
            path.write_text(_set_alt(html, NEUTRAL_ALT), encoding="utf-8")
            repaired.append((slug, alt, bad))
        else:
            findings.append((slug, alt, bad))

    if repaired:
        print(f"\n[~] ALT REPAIRED — {len(repaired)} generated hero(es) asserted "
              f"something the picture cannot support, and were reset to the "
              f"neutral alt.")
        for slug, alt, bad in repaired:
            print(f"\n  blog/{slug}.html")
            print(f"     was: {alt}")
            for what, txt in bad:
                print(f"      · {what} — {txt!r}")
            print(f"     now: {NEUTRAL_ALT}")
        print("\n    The post is publishable. This is a fallback, not a fix: "
              "assemble.py writes\n    the headline into alt= rather than "
              "describing the picture. Look at the\n    image and write one by "
              "hand when someone is next at a keyboard.\n")
        return 0

    if findings:
        print(f"\n[!] ALT CHECK FAILED — {len(findings)} generated hero(es) assert "
              f"something the picture cannot support.\n")
        for slug, alt, bad in findings:
            print(f"  blog/{slug}.html")
            print(f"     {alt}")
            for what, txt in bad:
                print(f"      · {what} — {txt!r}")
            print()
        print("    A generated hero is not a photograph of a real vehicle and does "
              "not\n    contain a readable badge. Describe only what is visible, "
              "name no make\n    or model, and assert no state you cannot see. "
              "Re-run with --repair to\n    reset it to the neutral alt.\n")
        return 2

    print(f"[+] Alt check: {checked} generated hero(es), no unsupportable claims.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
