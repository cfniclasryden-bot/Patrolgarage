#!/usr/bin/env python3
"""Fail the build if an editorial placeholder, or the partner workshop's name,
reaches visible body copy.

    python3 scripts/check_prose.py            # every page that ships
    python3 scripts/check_prose.py a.html ... # just these

Ported from topchallenger-site on 2026-10-05. Same rule: on 2026-08-23 that
site published "[NEEDS_SOURCE: Nissan official UAE service schedule]" in
visible body copy, because nothing between the generator and the deploy was
reading the prose. run_pipeline.py now runs this as a BLOCKING pre-publish
stage, scoped to the post being written.

Scripts, styles, HTML comments and tag attributes are stripped before the scan.
A marker inside a comment is a note to a developer, not something a reader or a
crawler sees, so it is allowed.

ADAPTED FOR THIS SITE: the partner workshop. patrolgarage.ae refers work to a
partner and must never name it (owner instruction 2026-08-21, see CLAUDE.md).
The two sites are kept apart in search on purpose. A generated post that names
it is blocked here exactly like a placeholder, because it is the same kind of
defect: something that must never reach a reader, caught before it can.

TK and XXX are matched on word boundaries, TK case-sensitively, so "tk" inside
a word or "Xxx" in prose will not fire.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shipped_pages
import copy_rules

SITE = Path(__file__).parent.parent

# The markers. Ordered most-specific first so the reported name is the useful one.
MARKERS = [
    ("NEEDS_SOURCE", re.compile(r"NEEDS_SOURCE")),
    ("TODO(",        re.compile(r"TODO\(")),
    ("[CITATION",    re.compile(r"\[CITATION")),
    ("FIXME",        re.compile(r"\bFIXME\b")),
    # Case-sensitive and word-bounded: "TK" the marker, not "tk" inside a word.
    ("TK",           re.compile(r"\bTK\b")),
    ("XXX",          re.compile(r"\bXXX+\b")),
    # The partner workshop. Never named on this site; see the docstring.
    ("partner name", re.compile(r"\btop\s*challenger\b|topchallenger\.ae", re.I)),
]

# Literal strings that are allowed to contain a marker-like run. Empty today;
# add here with a reason rather than weakening a pattern above.
ALLOW = ()


def visible_text(html_text):
    """What a reader sees: no scripts, styles, comments, or tag attributes."""
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)          # drops attributes with the tag
    return re.sub(r"\s+", " ", html.unescape(t))


def check_file(path):
    text = visible_text(path.read_text(encoding="utf-8"))
    for allowed in ALLOW:
        text = text.replace(allowed, " ")
    try:
        rel = path.resolve().relative_to(SITE.resolve())
    except ValueError:
        rel = path

    fails = []
    for name, pat in MARKERS:
        for m in pat.finditer(text):
            start = max(0, m.start() - 70)
            fails.append(f"{rel}: '{name}' in visible copy — "
                         f"…{text[start:m.end() + 90].strip()}…")

    # Business-copy rules (2026-10-05): prices, the Y61 as a service, and
    # years-in-business / car-count claims, in every scope a reader or a SERP
    # sees, not just visible text. See copy_rules.py for what each one means.
    for scope, rule, hit, sent in copy_rules.page_findings(path.read_text(encoding="utf-8")):
        fails.append(f"{rel}: {rule} [{scope}] {hit!r} — {sent[:200]}")
    return fails



# One definition of "what ships", shared by every guard. See shipped_pages.py.
_shipped_pages = shipped_pages.shipped_pages


def main(argv):
    files = [Path(a) for a in argv] if argv else _shipped_pages()

    fails = []
    for f in files:
        fails += check_file(f)

    if fails:
        print(f"\n[!] PROSE CHECK FAILED — {len(fails)} problem(s) in page copy. "
              f"Build stopped; nothing deployed.\n")
        for f in fails:
            print(f"    {f}")
        if any(" PRICE [" in f for f in fails):
            print("\n    PRICE: no AED figure, dirham amount, or dealer or labour total. "
                  "Say what drives\n    the cost and point the reader to a quote.")
        if any(" Y61_SERVICE [" in f for f in fails):
            print("\n    Y61_SERVICE: the Y61 is comparison content only, never a job "
                  "this business takes on.")
        if any(r in f for f in fails for r in (" HORSEPOWER [", " TORQUE [", " Y63_DETAIL [", " GRADE_0W20 [")):
            print("\n    UNVERIFIED FIGURE: no horsepower or torque figure, no Y63 launch year or "
                  "spec\n    (it is a twin-turbo V6, nothing more), no 0W-20 outside an approved "
                  "sentence.")
        if any(" TENURE [" in f for f in fails):
            print("\n    TENURE: no years in business and no counts of cars, customers "
                  "or jobs.")
        print("\n    An editorial marker reached the page. Either resolve it (attach the "
              "source,\n    fill the value) or rewrite the sentence so it does not need "
              "one. Do NOT\n    delete the marker and leave the claim standing.\n")
        return 1

    print(f"[+] Prose check: {len(files)} page(s), no editorial placeholders in visible copy.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
