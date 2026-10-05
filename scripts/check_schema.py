#!/usr/bin/env python3
"""Fail the build if placeholder, broken, or premises-claiming JSON-LD would ship.

    python3 scripts/check_schema.py            # every page that ships
    python3 scripts/check_schema.py a.html ... # just these

Exit 0 clean, 1 on any failure. run_pipeline.py runs this as a BLOCKING
pre-publish stage, scoped to the post being written.

Ported from topchallenger-site on 2026-10-05. The parse and placeholder rules
are identical. HTML comments are stripped BEFORE looking for JSON-LD: a block
inside a comment is not parsed by any consumer, so it is not "shipped".

ADAPTED FOR THIS SITE: the business entity. topchallenger is a workshop with
premises, so its version fails a LocalBusiness that is MISSING an address. This
site is the opposite. patrolgarage.ae has no premises (owner, 2026-08-21), and
patch_entity_schema.py (commit 89a64ee) stripped address, geo and
openingHoursSpecification from every AutoRepair node while deliberately KEEPING
@type AutoRepair: "the service is real and so is the brand". This guard follows
that decision rather than reopening it. So here a premises claim is the defect:

  * any node carrying address, geo, openingHoursSpecification or openingHours
  * the partner workshop's name or domain anywhere in the JSON-LD

Booking hours are real and live on a ContactPoint as hoursAvailable, which this
does not touch: the key it fails on is the premises property, not the type.

assemble.py builds a post's schema from a template that is a real published
post, so a premises claim that crept back into the template would ride into
every new post. This is the stage that stops it.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shipped_pages

SITE = Path(__file__).parent.parent

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
LD_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                   re.S | re.I)
# Any placeholder marker worth blocking. TODO( is the project's convention;
# the rest are the ones that show up when a template is filled in a hurry.
PLACEHOLDER_RE = re.compile(r"TODO\(|FIXME|XXX{2,}|<PLACEHOLDER|lorem ipsum", re.I)

PREMISES_PROPS = {"address", "geo", "openingHoursSpecification", "openingHours"}
PARTNER_RE = re.compile(r"top\s*challenger|topchallenger\.ae", re.I)


def active_blocks(html_text):
    """JSON-LD that a consumer would actually parse: comments removed first."""
    return LD_RE.findall(COMMENT_RE.sub(" ", html_text))


def check_file(path):
    """Returns a list of failure strings. Empty means the file is clean."""
    fails = []
    html_text = path.read_text(encoding="utf-8")
    # A path passed on the command line can sit outside SITE (a temp copy, a
    # file being checked before it is moved into place); relative_to() raises
    # on those, so fall back to the path as given rather than crashing.
    try:
        rel = path.resolve().relative_to(SITE.resolve())
    except ValueError:
        rel = path

    for i, raw in enumerate(active_blocks(html_text), 1):
        raw = raw.strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            fails.append(f"{rel}: JSON-LD block {i} does not parse — {e}")
            continue

        # Search the re-serialised object, not the raw source: that way a
        # placeholder cannot hide behind odd whitespace or escaping.
        blob = json.dumps(parsed)
        for m in set(PLACEHOLDER_RE.findall(blob)):
            for k, v in _walk(parsed):
                if isinstance(v, str) and PLACEHOLDER_RE.search(v):
                    fails.append(f"{rel}: JSON-LD block {i} ships a placeholder "
                                 f"at {k} = {v[:70]!r}")
            break

        # No premises: see the docstring. An address, geo or opening-hours
        # property asserts a location this business does not have.
        for keypath, node in _walk_nodes(parsed):
            t = node.get("@type")
            for prop in PREMISES_PROPS & set(node):
                fails.append(f"{rel}: JSON-LD block {i} has {prop!r} on a {t} at "
                             f"{keypath or 'root'} — this site has no premises")
        if PARTNER_RE.search(blob):
            fails.append(f"{rel}: JSON-LD block {i} names the partner workshop")
    return fails


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from _walk(v, f"{path}[{n}]")
    else:
        yield path, obj


def _walk_nodes(obj, path=""):
    if isinstance(obj, dict):
        if "@type" in obj:
            yield path, obj
        for k, v in obj.items():
            yield from _walk_nodes(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from _walk_nodes(v, f"{path}[{n}]")



# One definition of "what ships", shared by every guard. See shipped_pages.py.
_shipped_pages = shipped_pages.shipped_pages


def main(argv):
    if argv:
        files = [Path(a) for a in argv]
    else:
        files = _shipped_pages()

    fails = []
    blocks = 0
    for f in files:
        blocks += len(active_blocks(f.read_text(encoding="utf-8")))
        fails += check_file(f)

    if fails:
        print(f"\n[!] SCHEMA CHECK FAILED — {len(fails)} problem(s). "
              f"Build stopped; nothing deployed.\n")
        for f in fails:
            print(f"    {f}")
        # Only give the placeholder advice when a placeholder is what failed.
        # Printing it under a JSON parse error sends the reader to the wrong file.
        if any("no premises" in f for f in fails):
            print("\n    This site books work for a partner workshop and has no address. "
                  "Remove\n    the address/geo/opening hours; see patch_entity_schema.py and CLAUDE.md.")
        print()
        return 1

    print(f"[+] Schema check: {len(files)} page(s), {blocks} live JSON-LD block(s), "
          f"no placeholders, all parse.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
