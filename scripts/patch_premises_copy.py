#!/usr/bin/env python3
"""Remove premises claims from the visible copy, and add the key-facts block.

WHY (two jobs, one pass — see the note at the bottom of this docstring)

1. PREMISES CLAIMS. patrolgarage.ae has no premises of its own; it books the
   work and a partner workshop fulfils it. The pages carried turn-by-turn
   driving directions ("just off the Dubai to Al Ain road (E66), a short drive
   from Nad Al Hamar, Al Aweer and Mirdif"), an invitation to arrive unannounced
   ("before you drive over", "before you make the trip") and an on-site parking
   claim. Those route a stranger to a building. They go.

   What stays: Ras Al Khor as where the work happens, because it is, and the
   brand's own first-person voice. Subcontracting fulfilment is ordinary
   commerce and needs no disclosure. scripts/patch_entity_schema.py did the
   matching markup half.

   Replacing "drive over" with "message first and we confirm the drop-off"
   is also the better funnel: on a lead-generation site the call IS the product,
   and a walk-in that never rings is a lost lead.

2. KEY-FACTS BLOCK. 91-94% of this site's clicks come from queries Search
   Console will not name, and the fragments it does show are conversational
   turns — "find me one", "give me location", "yes please", "anywhere in
   dubai". That is an assistant (ChatGPT, Google AI Mode, Perplexity) reading
   the page mid-conversation and answering on the site's behalf, not a person
   reading from the top. So the facts such an answer needs — which car, where,
   how to book, when, and that there is no walk-in address — have to sit high
   in the DOM as plain extractable text, not be scattered eight sections down.
   Everything in the block is already asserted elsewhere on the site; nothing
   here is a new claim.

Also fixed: contact.html said the workshop takes "Y61 through Y63". The garage
services Y62 only — Y61 is informational content on this site and must never be
service-framed.

MTIME IS PRESERVED (journal_update.py derives the blog's displayed dates and
sort order from it, and publish.py runs on every deploy). Idempotent via the
AIFACTS marker and via exact-string replacement that no-ops once applied.

    python3 scripts/patch_premises_copy.py --dry-run
    python3 scripts/patch_premises_copy.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!-- AIFACTS -->"

FACTS_CSS = """
    /* AIFACTS — key facts, kept high in the DOM and as plain text: this block
       exists to be read aloud by an assistant, not just by a person.
       Each dt/dd pair is wrapped in a div so the grid lays out PAIRS, not
       alternating labels and values across separate columns. */
    .keyfacts{background:#fff;border-top:1px solid #e8e4de;border-bottom:1px solid #e8e4de}
    .keyfacts-inner{max-width:1200px;margin:0 auto;padding:3rem 1.5rem}
    .keyfacts h2{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;
      color:#8a8178;font-weight:600;margin:0 0 2rem}
    .keyfacts dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
      gap:2rem 3rem;margin:0}
    .keyfacts .kf-item{min-width:0}
    .keyfacts dt{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;
      color:#8a8178;font-weight:600;margin:0 0 .5rem}
    .keyfacts dd{margin:0;font-size:.95rem;line-height:1.62;color:#1a1a1a}
    .keyfacts dd a{color:inherit;font-weight:600;white-space:nowrap}
    @media (max-width:600px){.keyfacts-inner{padding:2.25rem 1.25rem}
      .keyfacts dl{gap:1.5rem}}
"""

FACTS_HTML = """  <section class="keyfacts">%s
    <div class="keyfacts-inner">
      <h2>Patrol Garage Dubai &mdash; the essentials</h2>
      <dl>
        <div class="kf-item">
          <dt>What we work on</dt>
          <dd>Nissan Patrol Y62 only &mdash; the VK56VD petrol V8 and the JR710E
              gearbox. We do not take the Y61, and we do not take other makes.</dd>
        </div>
        <div class="kf-item">
          <dt>Work we do</dt>
          <dd>Engine work, gearbox and transmission, major and periodic servicing,
              suspension, AC and diagnostics.</dd>
        </div>
        <div class="kf-item">
          <dt>Where</dt>
          <dd>Ras Al Khor, Dubai. Patrol owners reach us from across Dubai,
              Sharjah and the Northern Emirates.</dd>
        </div>
        <div class="kf-item">
          <dt>Booking</dt>
          <dd>WhatsApp or call
              <a href="tel:+971585143634">+971 58 514 3634</a>.
              You get a quote before any work starts.</dd>
        </div>
        <div class="kf-item">
          <dt>When you can reach us</dt>
          <dd>Sunday to Thursday, 9am&ndash;7pm. Saturday, 9am&ndash;2pm.
              Closed Friday.</dd>
        </div>
        <div class="kf-item">
          <dt>Drop-off</dt>
          <dd>We do not publish a walk-in address. Message or call first and we
              confirm the drop-off point and a time that suits you.</dd>
        </div>
      </dl>
    </div>
  </section>
""" % MARKER

# --- exact-string copy replacements -------------------------------------
# Each is (file, old, new). Exact strings, so a second run finds nothing and
# no-ops rather than corrupting anything.
EDITS = [
    # ---- index.html: coverage section ----
    ("index.html",
     "We are in the Ras Al Khor industrial area, off the Dubai to Al Ain road "
     "and a few minutes from Nad Al Hamar. If you are looking for a car garage "
     "in Ras Al Khor, one thing is worth knowing before you drive over: we only "
     "take Nissan Patrols.",
     "The work happens in Ras Al Khor, Dubai's workshop district. If you are "
     "looking for a car garage in Ras Al Khor, one thing is worth knowing "
     "before you call: we only take Nissan Patrols."),

    ("index.html",
     "That is not a preference, it is the whole workshop. The diagnostic kit is "
     "set up for the VK56VD and the JR710E, the parts on the shelf are Patrol "
     "parts, and the fault history we work from is Patrol fault history. If you "
     "drive something else we will say so straight away rather than waste your "
     "morning, and we can usually point you to someone nearby who can help.",
     "That is not a preference, it is the whole workshop. The diagnostic kit is "
     "set up for the VK56VD and the JR710E, the parts are Patrol parts, and the "
     "fault history we work from is Patrol fault history. If you drive "
     "something else we will say so straight away rather than waste your "
     "morning, and we can usually point you to someone who can help."),

    # ---- contact.html: "Finding Us" -> booking, no directions, no parking claim
    ("contact.html",
     "<div class=\"section-num\">02 &mdash; Finding Us</div>\n"
     "        <h2>Ras Al Khor<br>Industrial Area.</h2>",
     "<div class=\"section-num\">02 &mdash; Booking &amp; Drop-off</div>\n"
     "        <h2>Message first,<br>then bring it in.</h2>"),

    ("contact.html",
     "We are in the Ras Al Khor industrial area in Dubai, just off the Dubai to "
     "Al Ain road (E66) and a short drive from Nad Al Hamar, Al Aweer and "
     "Mirdif. Ras Al Khor is a workshop district, so most of what surrounds us "
     "is other garages and parts suppliers rather than shopfronts. Message us "
     "on WhatsApp when you set off and we will send a live pin.",
     "The work is done in Ras Al Khor, Dubai's workshop district. We do not run "
     "a walk-in counter and we do not publish a street address &mdash; message "
     "us on WhatsApp or call, tell us what the car is doing, and we will "
     "confirm a drop-off point and a time. You will have a quote before "
     "anything is touched."),

    ("contact.html",
     "Worth repeating before you make the trip: this is a Nissan Patrol "
     "workshop only, Y61 through Y63. We are not a general car garage in Ras Al "
     "Khor and we will not pretend to be one. If you drive something else, "
     "message us anyway and we will tell you who nearby actually does that car "
     "properly.",
     "Worth repeating before you get in touch: this is a Nissan Patrol Y62 "
     "workshop only. We are not a general car garage in Ras Al Khor and we will "
     "not pretend to be one. If you drive something else, message us anyway and "
     "we will tell you who actually does that car properly."),

    ("contact.html",
     "Most Patrol owners reach us from Deira, Mirdif, Nad Al Sheba, Al Quoz, "
     "Business Bay and Sharjah. Parking is on site and you can wait for shorter "
     "jobs.",
     "Most Patrol owners reach us from Deira, Mirdif, Nad Al Sheba, Al Quoz, "
     "Business Bay and Sharjah."),

    # ---- about.html ----
    ("about.html",
     "Visit our workshop in Ras Al Khor or give us a call.",
     "Message us on WhatsApp or give us a call."),
]


def write(path, text, dry):
    if dry:
        return
    st = path.stat()
    path.write_text(text, encoding="utf-8")
    os.utime(path, (st.st_atime, st.st_mtime))  # see module docstring


def main():
    dry = "--dry-run" in sys.argv
    changed = {}

    for fname, old, new in EDITS:
        p = ROOT / fname
        h = p.read_text(encoding="utf-8")
        if old not in h:
            if new.split(".")[0][:40] in h:
                print(f"  skip   {fname}: already applied")
            else:
                print(f"  !! MISS {fname}: source string not found — {old[:60]!r}")
            continue
        changed.setdefault(fname, p.read_text(encoding="utf-8"))
        h = h.replace(old, new, 1)
        write(p, h, dry)
        print(f"  edit   {fname}: {old[:52].strip()}…")

    # key-facts block: after the trust strip on the homepage
    p = ROOT / "index.html"
    h = p.read_text(encoding="utf-8")
    if MARKER in h:
        print("  skip   index.html: key-facts block already present")
    else:
        anchor = '  <section class="warm">'
        if anchor not in h:
            print("  !! MISS index.html: no <section class=\"warm\"> anchor, refusing")
        else:
            h = h.replace(anchor, FACTS_HTML + anchor, 1)
            h = h.replace("</style>", FACTS_CSS + "  </style>", 1)
            write(p, h, dry)
            print("  edit   index.html: key-facts block + styles inserted after the trust strip")

    print("\ndry run, nothing written" if dry else "\ndone")


if __name__ == "__main__":
    main()
