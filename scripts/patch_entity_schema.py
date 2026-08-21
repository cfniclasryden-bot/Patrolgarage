#!/usr/bin/env python3
"""Strip the physical-location claims from every AutoRepair node on the site.

WHY
patrolgarage.ae has no premises. It is a lead-generation brand: enquiries are
booked here and the work is fulfilled by a partner workshop. Selling a service
you subcontract is ordinary commerce and needs no disclosure. Asserting a
postal address, a map pin and opening hours for premises you do not have is a
different thing, and the site did it on 37 pages.

The pin was also simply wrong. It claimed 25.1768 / 55.3537. The workshop that
actually does the work sits at 25.1768895 / 55.3373777 — same latitude, ~1.6 km
off in longitude. It pointed at nothing.

WHAT CHANGES, PER AutoRepair NODE
  removed  geo                       fabricated coordinates
  removed  address                   no premises to give an address for
  removed  openingHoursSpecification means "hours these premises are open"
  added    contactPoint              booking hours, which are real, kept as
                                     hoursAvailable on a ContactPoint
  kept     @type AutoRepair, name, telephone, url, image, areaServed,
           knowsAbout, serviceType — the service is real and so is the brand.

`Service.provider` nodes are retyped the same way.

WHAT THIS DOES NOT DO
It does not touch visible copy. Premises claims in prose ("our Ras Al Khor
workshop", driving directions) are handled separately — fixing markup while the
body still invites a drive-over is worse than either state alone.

MTIME IS PRESERVED. journal_update.py derives each post's displayed date AND
the blog listing sort order from the file's mtime, and publish.py runs it on
every deploy — so a bulk rewrite that lets mtime drift silently re-dates the
whole blog and ships it. Every write here restores the original mtime.

    python3 scripts/patch_entity_schema.py --dry-run
    python3 scripts/patch_entity_schema.py
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Hours are real — they are when a booking can be made. They just are not
# "hours a building is open", which is what openingHoursSpecification asserts.
CONTACT_POINT = {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "telephone": "+971585143634",
    "areaServed": "AE",
    "availableLanguage": ["en", "ar"],
    "hoursAvailable": [
        {"@type": "OpeningHoursSpecification",
         "dayOfWeek": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
         "opens": "09:00", "closes": "19:00"},
        {"@type": "OpeningHoursSpecification",
         "dayOfWeek": "Saturday", "opens": "09:00", "closes": "14:00"},
    ],
}

PLACE_PROPS = ("geo", "address", "openingHoursSpecification", "hasMap", "map")


def clean_node(node):
    """Return (node, changed). Recurses so Service.provider is caught too."""
    changed = False
    if not isinstance(node, dict):
        return node, False

    for key, val in list(node.items()):
        if isinstance(val, dict):
            node[key], c = clean_node(val)
            changed = changed or c
        elif isinstance(val, list):
            for i, item in enumerate(val):
                val[i], c = clean_node(item)
                changed = changed or c

    if node.get("@type") != "AutoRepair":
        return node, changed

    for prop in PLACE_PROPS:
        if prop in node:
            del node[prop]
            changed = True

    # Only the top-level business node carries contact details; a nested
    # provider stub is just an identity reference and needs no contactPoint.
    if "telephone" in node and "contactPoint" not in node:
        node["contactPoint"] = json.loads(json.dumps(CONTACT_POINT))
        changed = True

    return node, changed


def patch_file(path, dry_run=False):
    html = path.read_text(encoding="utf-8")
    out = []
    changed_blocks = 0
    pos = 0

    for m in re.finditer(
        r'(?is)(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', html
    ):
        raw = m.group(2)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if "AutoRepair" not in raw:
            continue

        data, changed = clean_node(data) if isinstance(data, dict) else (
            [clean_node(x)[0] for x in data], True)
        if not changed:
            continue

        # Match the surrounding indentation so the diff stays readable and the
        # file keeps the shape assemble.py produces.
        indent = re.search(r'\n([ \t]*)$', html[:m.start(2)])
        pad = indent.group(1) if indent else "  "
        body = json.dumps(data, indent=2, ensure_ascii=False)
        body = "\n".join((pad + ln) if ln.strip() else ln for ln in body.split("\n"))

        out.append(html[pos:m.start(2)])
        out.append("\n" + body + "\n" + pad)
        pos = m.end(2)
        changed_blocks += 1

    if not changed_blocks:
        return 0
    out.append(html[pos:])
    new = "".join(out)

    if not dry_run:
        st = path.stat()
        path.write_text(new, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))  # see module docstring
    return changed_blocks


def target_files():
    """Every deployed page. Mirrors patch_favicon.target_files(), which unlike
    patch_clarity's does include services/."""
    files = sorted(ROOT.glob("*.html"))
    files += sorted(ROOT.glob("services/*.html"))
    files += sorted(p for p in ROOT.glob("blog/*.html"))
    files += sorted(ROOT.glob("blog/page/*/*.html"))
    return files


def main():
    dry = "--dry-run" in sys.argv
    total_files = total_blocks = 0
    for f in target_files():
        n = patch_file(f, dry_run=dry)
        if n:
            total_files += 1
            total_blocks += n
            print(f"  {'would patch' if dry else 'patched'}: {f.relative_to(ROOT)} ({n} block{'s' if n > 1 else ''})")
    print(f"\n{total_blocks} schema blocks across {total_files} files"
          f"{' (dry run, nothing written)' if dry else ''}")


if __name__ == "__main__":
    main()
