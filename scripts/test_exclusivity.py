#!/usr/bin/env python3
"""Exclusivity guard: no shipped page says the business takes one model only.

Owner rule, 2026-11-12: Patrol Garage is described as a Nissan Patrol (Y62)
specialist, never as a business that only works on one model or turns other
makes away. That day the wording was removed from the homepage, contact, About,
the Y62 garage page, the Abu Dhabi service-area page, llms.txt and six posts
("we work exclusively on Patrols" and similar). This test keeps it out.

Fails on, case-insensitive, in the visible text, title, meta / og / twitter
descriptions and JSON-LD of every shipped page (shipped_pages.py, the same set
the other content guards check) and in llms.txt:

    exclusively | Y62 only / Y62-only | only work on | nothing else |
    one car only | other makes are not

HTML comments are internal notes and are not checked.

FALSE POSITIVES are allowed per file and per phrase, never globally, so an
exception on one page cannot hide a real hit on another. Each was read in
context on 2026-11-12. An allowlist entry that no longer matches anything is
reported as stale (a warning, not a failure).

    python3 scripts/test_exclusivity.py              # all shipped pages + llms.txt
    python3 scripts/test_exclusivity.py blog/x.html  # just these files (pipeline gate)
"""
import html as H
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SITE / "scripts"))

PATTERN = re.compile(
    r"\bexclusively\b|\bY62[ -]only\b|\bonly work on\b|\bnothing else\b|\bone car only\b"
    r"|\bother makes are not\b",
    re.I)

# (file relative to the site root, lowercase phrase that must be in the sentence)
ALLOW = [
    ("blog/nissan-patrol-differential-repair-cost-uae.html", "requires dealer parts exclusively"),
    ("blog/nissan-patrol-differential-repair-cost-uae.html", "used exclusively for dubai city driving"),
    ("blog/nissan-patrol-major-service.html", "nothing else touched"),
    ("blog/y62-fuel-injector-cleaning-cost-dubai-2026.html", "nothing else has changed"),
]

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_DROP = re.compile(r"<(script|style|noscript|svg)\b.*?</\1>", re.S | re.I)
_META = re.compile(r'<meta (?:name|property)="(?:description|og:description|og:title|'
                   r'twitter:description|twitter:title)" content="([^"]*)"')


def _ld_strings(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            _ld_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _ld_strings(v, out)
    elif isinstance(obj, str):
        out.append(obj)


def checked_text(page):
    """Everything a reader or a search engine gets from the page, comments excluded."""
    page = _COMMENT.sub(" ", page)
    parts = []
    t = re.search(r"<title>(.*?)</title>", page, re.S)
    if t:
        parts.append(t.group(1))
    parts += _META.findall(page)
    for block in _LD.findall(page):
        try:
            _ld_strings(json.loads(block), parts)
        except ValueError:
            parts.append(block)
    body = re.sub(r"<[^>]+>", " ", _DROP.sub(" ", page))
    parts.append(body)
    return H.unescape(re.sub(r"\s+", " ", " ".join(parts)))


def findings(rel, text, used):
    out = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if not PATTERN.search(sentence):
            continue
        low = sentence.lower()
        hit = next(((f, p) for f, p in ALLOW if f == rel and p in low), None)
        if hit:
            used.add(hit)
            continue
        out.append(sentence.strip()[:200])
    return out


def self_test():
    """Must-fire and must-not-fire cases, so a broken pattern fails loudly."""
    must_fire = ["We work exclusively on Nissan Patrols.", "Nissan Patrol Y62 only.",
                 "Y62-only Nissan Patrol service in Dubai.", "We only work on the Patrol.",
                 "This is a Patrol business and nothing else.", "One car only: the Y62.",
                 "Other makes are not accepted."]
    must_not = ["As Nissan Patrol specialists, we know the VK56VD V8 well.",
                "Patrol Garage is a Nissan Patrol Y62 specialist.",
                "Only the gearbox fluid was changed.", "The Y61 appears as comparison content."]
    bad = [s for s in must_fire if not PATTERN.search(s)]
    bad += [f"false hit: {s}" for s in must_not if PATTERN.search(s)]
    # an allowlisted phrase only passes on its own file
    used = set()
    if not findings("index.html", "Patrols used exclusively for Dubai city driving need less.", used):
        bad.append("allowlist leaked to another file")
    if findings(ALLOW[1][0], "Patrols used exclusively for Dubai city driving need less.", used):
        bad.append("allowlist entry did not apply on its own file")
    return bad


def main(argv):
    problems = [f"self-test: {b}" for b in self_test()]
    if argv:
        paths = [Path(a) if Path(a).is_absolute() else SITE / a for a in argv]
    else:
        from shipped_pages import shipped_pages
        paths = list(shipped_pages()) + [SITE / "llms.txt"]
    used = set()
    for p in paths:
        rel = str(p.resolve().relative_to(SITE))
        raw = p.read_text(encoding="utf-8", errors="replace")
        text = checked_text(raw) if p.suffix == ".html" else raw
        for s in findings(rel, text, used):
            problems.append(f"{rel}: {s}")
    if problems:
        print(f"[!] exclusivity guard FAILED: {len(problems)} finding(s)")
        for f in problems:
            print("    -", f)
        return 1
    if not argv:
        stale = [a for a in ALLOW if a not in used]
        for f, phrase in stale:
            print(f"    [warn] stale allowlist entry, no longer on the page: {f}: {phrase!r}")
    print(f"[+] exclusivity guard passed: {len(paths)} file(s), "
          f"{len(used)} allowlisted false positive(s), self-test clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
