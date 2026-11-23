# REFRESH proposal (patch mode) for review: nissan-patrol-black-smoke

Generated 2026-11-23 with `scripts/refresh_patch.py --dry-run`. NOT LIVE. The live page is unchanged.

## Why

- Owner input: customers ask about black smoke from the exhaust often (Aamir, 23 Nov). This is a
  frequent customer question, so it is kept as context for the refresh, not written into the post.
- Goal: move /blog/nissan-patrol-black-smoke.html from position 5 (GSC 2026-08-23..2026-11-21:
  502 impressions, 8 clicks, avg position 5.0) into the top 3. Almost all its queries are anonymised
  in GSC, so no single query can be targeted; measured UAE volume (Google Ads, 2026-11-23):
  "black smoke from exhaust" 50/mo, "nissan patrol black smoke" 10/mo (used as gap keywords).
- Patch mode, chosen by the user over a full regenerate: every existing sentence, heading, number and
  link is kept (validator-enforced); only additions.

## Files

- `proposal-article-body.html`: the proposed <article> body (what ships if approved).
- `nissan-patrol-black-smoke.html`: preview of the full page with the proposal in place.
- `brief.txt`: the editor's requirements given to the model (`--brief-file`).

## Additions (+269 words, +1 heading; inserted after the "registration renewal" paragraph in
"How serious is black smoke, and what happens if you ignore it?")

- New H2 "White, black or blue smoke: what each colour points to", an intro line and a 3-row table
  (Colour / What it usually means / What to do).
- A "stop driving if" paragraph (temperature gauge, falling coolant, flashing check engine light,
  strong fuel smell with black smoke from exhaust).
- CTA paragraph: send a short video on WhatsApp (wa.me/971558175637 with a prefill) or call
  +971 55 817 5637.

## Gates on the preview

- PASS: check_prose, check_schema, check_model_years, check_claims, check_city, test_exclusivity,
  test_no_offers, check_editorial (with the page's legacy baseline; the two "genuine" sentences are
  existing, frozen hits).
- check_post_rules --refresh: the same 6 problems the LIVE page already has, none added by the patch:
  service link at 98% (not first third), missing closing line "Ask us about your Patrol on WhatsApp",
  year in the title ("...Fix 2026"), VK56VD in the answer block and JSON-LD description, length
  (2,097 live, 2,365 with the patch; rule 1,200-1,800). Patch mode cannot reword existing text, so
  these need a hand edit or a regenerate.

## Apply (only after approval)

    python3 scripts/refresh_patch.py nissan-patrol-black-smoke \
        --apply-from drafts/review/nissan-patrol-black-smoke/proposal-article-body.html
    # re-validates the saved body, writes it and stamps "Last updated"; then publish as usual.

Do NOT use approve.py for this folder: its post-rule gate fails on the 6 legacy problems above.
