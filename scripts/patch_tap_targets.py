#!/usr/bin/env python3
"""Make the service cards tappable on mobile (stretched-link pattern).

Measured at 390px with real touch emulation (2026-08-12):
  index.html    6/6 cards — 0 anchors, all 4 corners + centre DEAD (~308-331px
                of dead surface per card)
  services.html 9/9 cards — 1 anchor (the WhatsApp button), all 4 corners +
                centre DEAD

Both pages signalled interactivity with hover-only affordances that do nothing
on touch: `.service-card:hover{background}` and `.service-card:hover .arrow
{transform:translateX(4px)}`. The homepage cards even render a "→" glyph while
containing no <a> at all.

The fix is topchallenger's stretched-link pattern (site/CONTENT-MODEL.md sibling
markup, .svc-row): the card gets position:relative, the HEADING is wrapped in a
real anchor, and that anchor gets a full-bleed ::after{inset:0} overlay. Anchor
text stays exactly the heading text — no "click here", nothing appended — while
the entire card becomes one tap target. :focus-within mirrors :hover so keyboard
users get the same affordance.

Destinations:
  index.html    -> the matching section on /services.html (ids added by this
                   script), so a homepage tap lands on the detail, not a menu.
  services.html -> that card's own WhatsApp href, reusing the per-card prefill
                   the CTA button already carries. The services page IS the
                   destination, so the only forward action is the quote request.

Interactive children (the CTA buttons) are lifted to z-index 2 so they keep
their own click behaviour above the overlay.

Idempotent via MARKER. Static pages only — it never touches blog/, so post
mtimes (which drive the blog's displayed dates and sort order) are untouched.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Must be a substring of the CSS comment actually injected below — the guard is
# what stops a re-run from wrapping the headings in a second anchor.
MARKER = "/* TAPTARGETS"

# homepage card heading -> services.html section id
HOME_MAP = {
    "Engine Diagnostics": "engine-diagnostics-repair",
    "Suspension & Lift Kits": "suspension-upgrade-lift-kits",
    "Brakes & Steering": "brakes-tyres-batteries",
    "Performance & Mods": "modifications-performance-upgrades",
    "AC Service & Repair": "ac-service-repair",
    "Pre-Purchase Inspection": "pre-purchase-inspection",
}

HOME_CSS = """
    /* TAPTARGETS — whole-card tap target. The cards used to be 0-anchor divs
       with a hover-only background and a "→" that never went anywhere; at 390px
       every corner and the centre resolved to DEAD. */
    .service-card { position: relative; }
    .service-card h3 a { color: inherit; text-decoration: none; }
    .service-card h3 a::after { content: ""; position: absolute; inset: 0; z-index: 1; }
    .service-card:focus-within { background: var(--bg-1); }
    .service-card:focus-within .arrow { transform: translateX(4px); }
    .service-card h3 a:focus-visible { outline: 2px solid var(--white); outline-offset: 4px; }
"""

SERVICES_CSS = """
    /* TAPTARGETS — whole-card tap target, same pattern as the homepage. The CTA
       row sits above the overlay so its own link still wins the tap. */
    /* scroll-margin-top clears the sticky header, which is 88px at every
       breakpoint (measured 390/768/1280). Without it a homepage card tap lands
       on /services.html#<id> with 19px of the section heading hidden behind the
       header, so the reader arrives looking at a headless block of text. */
    .service-article { position: relative; scroll-margin-top: 104px; }
    .service-article h2 a { color: inherit; text-decoration: none; }
    .service-article h2 a::after { content: ""; position: absolute; inset: 0; z-index: 1; }
    .service-article:focus-within { background: var(--bg-1); }
    .service-article h2 a:focus-visible { outline: 2px solid var(--white); outline-offset: 4px; }
    .service-cta { position: relative; z-index: 2; }
"""


def slugify(text):
    t = re.sub(r"&amp;", "and", text).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def inject_css(html, css):
    """Put the rules just before </style> of the page's own inline stylesheet."""
    if MARKER in html:
        return html, False
    idx = html.rfind("</style>")
    if idx == -1:
        return html, False
    return html[:idx] + css + "  " + html[idx:], True


def patch_home(html):
    changed = 0

    def repl(m):
        nonlocal changed
        block, heading = m.group(0), m.group(1)
        plain = re.sub(r"<[^>]*>", " ", heading)
        plain = re.sub(r"\s+", " ", plain).replace("&amp;", "&").strip()
        target = HOME_MAP.get(plain)
        if not target or "<a " in heading:
            return block
        changed += 1
        return block.replace(
            f"<h3>{heading}</h3>",
            f'<h3><a href="/services.html#{target}">{heading}</a></h3>',
            1,
        )

    html = re.sub(r"<h3>(.*?)</h3>", repl, html, flags=re.S)
    return html, changed


def patch_services(html):
    changed = 0

    def repl(m):
        nonlocal changed
        block = m.group(0)
        h2 = re.search(r"<h2>(.*?)</h2>", block, re.S)
        if not h2 or "<a " in h2.group(1):
            return block
        wa = re.search(r'<a href="(https://wa\.me/[^"]*)"', block)
        if not wa:
            return block
        heading = h2.group(1)
        sid = slugify(re.sub(r"<[^>]*>", "", heading))
        changed += 1
        block = block.replace(
            '<div class="service-article">',
            f'<div class="service-article" id="{sid}">', 1,
        )
        return block.replace(
            f"<h2>{heading}</h2>",
            f'<h2><a href="{wa.group(1)}" target="_blank" rel="noopener">{heading}</a></h2>',
            1,
        )

    html = re.sub(
        r'<div class="service-article">.*?(?=<div class="service-article">|</section>)',
        repl, html, flags=re.S,
    )
    return html, changed


def main():
    dry = "--dry-run" in sys.argv
    for name, patcher, css in (
        ("index.html", patch_home, HOME_CSS),
        ("services.html", patch_services, SERVICES_CSS),
    ):
        p = ROOT / name
        html = p.read_text(encoding="utf-8")
        if MARKER in html:
            print(f"  skip   {name} (already patched)")
            continue
        html, n = patcher(html)
        html, ok = inject_css(html, css)
        print(f"  patch  {name}: {n} card(s) linked, css={'yes' if ok else 'NO </style> FOUND'}")
        if not dry:
            p.write_text(html, encoding="utf-8")
    print("\n" + ("DRY RUN — nothing written" if dry else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
