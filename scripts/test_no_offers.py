#!/usr/bin/env python3
"""No page offers to fit, install or supply anything (owner, 2026-11-09). Spends nothing.

A customer called the partner workshop asking for a tow bar after the tow bar
post closed with "bring it to us at Patrol Garage". This site has no premises
and books nothing it can fit: every closing line stays neutral ("Ask us about
your Patrol on WhatsApp").

Fails on, in the visible text, title and meta description of every shipped page:
  * first-person fit / install / supply / sell / stock offers ("we fit",
    "we'll install", "we supply", "we can source and fit", "our fitters")
  * "bring it to us", "bring it in", "bring your Patrol to Patrol Garage",
    "When to bring it to Patrol Garage", "drop it off with us"
  * "fitted / installed by us", "done here"

Also fails if generate.py's prompt still grants "bring it to us" or keeps the old
closing H2, if early_cta / cta_lib copy carries offer wording, or if the topic
blocklist stops catching its own topics.

    python3 scripts/test_no_offers.py           # all shipped pages
    python3 scripts/test_no_offers.py a.html    # just these (any path, drafts too)
"""
import html as H
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

OFFER = re.compile(
    r"\bbring (?:it|the car|the vehicle|your (?:car|patrol|y6[123]|vehicle|truck))"
    r" (?:to us|in\b|over|round|to patrol garage|to the workshop)"
    r"|\bwhen to bring it\b"
    r"|\bwe(?:'ll|’ll| will| can| also| do| would| then)?\s+(?:also\s+)?"
    r"(?:fit|fits|install|installs|supply|supplies|sell|sells|stock|stocks|source and fit|wire|mount|bolt on)\b"
    r"|\bwe(?:'re|’re| are)\s+(?:fitting|installing|supplying|selling)\b"
    r"|\bour (?:fitters?|installers?|fitting (?:team|service|bay)|installation (?:team|service))\b"
    r"|\b(?:drop|leave) (?:it|the car|your (?:car|patrol)) (?:off )?(?:with|at) us\b"
    r"|\b(?:fitted|installed|supplied) (?:by us|at patrol garage|here)\b"
    r"|\bwe (?:also )?carry (?:stock|parts|the (?:relevant |right )?parts)\b|\bcarry stock of\b"
    r"|\bcarry the (?:relevant |right )?parts\b",
    re.I)

_DROP = re.compile(r"<(script|style|noscript|svg)\b.*?</\1>", re.S | re.I)


def visible_text(page_html):
    t = _DROP.sub(" ", page_html)
    title = re.search(r"<title>(.*?)</title>", page_html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', page_html)
    t = re.sub(r"<[^>]+>", " ", t)
    extra = " ".join(x.group(1) for x in (title, desc) if x)
    return H.unescape(re.sub(r"\s+", " ", extra + " " + t))


def sentences_with_offers(page_html):
    text = visible_text(page_html)
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text):
        if OFFER.search(s):
            out.append(s.strip()[:300])
    return out


def shipped():
    from shipped_pages import shipped_pages
    return shipped_pages()


def main(argv):
    paths = [Path(a) for a in argv] or shipped()
    fails = []
    for p in paths:
        for s in sentences_with_offers(p.read_text(encoding="utf-8")):
            try:
                name = p.resolve().relative_to(ROOT)
            except ValueError:
                name = p
            fails.append(f"{name}: {s}")

    if not argv:
        prompt = (SCRIPTS / "generate.py").read_text(encoding="utf-8")
        # The permission line the prompt used to carry, and the old closing H2.
        # (The prompt now quotes "bring it to us" only to forbid it.)
        for bad in ('you may write "we", "our", "at the workshop", "bring it to us"',
                    "When to bring it to Patrol Garage"):
            if bad in prompt:
                fails.append(f"scripts/generate.py: prompt still contains {bad}")
        if "Ask us about your Patrol on WhatsApp" not in prompt:
            fails.append("scripts/generate.py: prompt lacks the neutral closing line")
        import early_cta
        for kind, copy in early_cta.COPY.items():
            for piece in copy:
                if OFFER.search(piece):
                    fails.append(f"scripts/early_cta.py {kind}: {piece}")
        import topic_blocklist
        for kw in ("y62 tow bar fitting cost", "ppf cost dubai", "y61 snorkel fitting",
                   "y63 dashcam installation", "lift kit y62", "roof rack installation"):
            if not topic_blocklist.is_blocked(kw):
                fails.append(f"topic_blocklist: no longer blocks {kw!r}")
        for kw in ("y62 gearbox repair cost", "nissan patrol overheating", "y62 fuel line fitting leak"):
            if topic_blocklist.is_blocked(kw):
                fails.append(f"topic_blocklist: wrongly blocks {kw!r}")

    if fails:
        print(f"[FAIL] {len(fails)} offer sentence(s) / problem(s):")
        for f in fails:
            print("  " + f)
        return 1
    print(f"[OK] no fit / install / supply / bring-it-to-us offers on {len(paths)} page(s)"
          + ("" if argv else "; prompt, early CTA copy and topic blocklist clean"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
