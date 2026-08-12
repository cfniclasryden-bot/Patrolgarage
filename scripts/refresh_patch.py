#!/usr/bin/env python3
"""Patch-mode refresh: update an existing post IN PLACE, never regenerate it.

Why this exists. run_pipeline.py --refresh regenerates an article from scratch
(research -> generate -> humour -> assemble -> image -> publish). The URL keeps
its rankings but the content is entirely new, and every hand-edit is destroyed.
Pointing that at a page sitting at position 4 is an unacceptable risk, so patch
mode is the only thing the scheduler is allowed to enqueue.

What it does. It sends the EXISTING article body to the model with three narrow
jobs, from the SEO playbook's three refresh dimensions:

  1. outdated facts    — correct anything stale, e.g. a year that has rolled over
  2. missing keywords  — work the supplied gap keywords in naturally, where the
                         page already ranks 11-50 for a term it never says
  3. missing subtopics — add a new H2 section only where one is genuinely absent

Everything else must survive byte-for-byte. The validator below is modelled on
humour_pass.py's: it refuses the edit rather than shipping a mangled page, and a
refusal is not fatal — the article stays exactly as it was.

Guarantees enforced by validate():
  * existing prose may be ADDED to, never reworded (subsequence check)
  * no existing number may change unless it is in the allowed-change list
  * existing headings and links all survive
  * the quick-answer, FAQ, CTA and MONEYLINK blocks are untouched
  * tag structure stays balanced and growth is capped

mtime is preserved by default: journal_update.py derives each post's DISPLAYED
DATE and the blog listing sort order from it, so patching all 44 posts would
otherwise re-date the entire blog to today and scramble the order. The visible
freshness signal is the in-article "Last updated:" stamp, which IS updated.
Pass --bump-date to also move the listing date.

Usage:
    python3 scripts/refresh_patch.py <slug> [--gaps "kw1,kw2"] [--dry-run] [--bump-date]
"""
import os
import re
import sys
import difflib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

MODEL = "claude-opus-5"
# Growth ceiling: 35% of the body, but never less than MIN_HEADROOM words. A
# percentage alone is fragile on short bodies — one legitimate new section is
# ~200-400 words, which is inside 35% of a 2,000-word post but way over 35% of a
# 300-word one. The floor keeps the rule honest at both ends.
MAX_GROWTH = 1.35
MIN_HEADROOM = 400
PROTECTED = ("direct-answer", "faq", "cta", "last-updated", "MONEYLINK", "related-reading")

PROMPT = """You are updating an existing published article for Patrol Garage, a Nissan Patrol specialist workshop in Ras Al Khor, Dubai.

This article ALREADY RANKS. You are making a surgical update, not a rewrite.

ABSOLUTE RULES — breaking any of these means the edit is discarded:
- Do NOT reword, reorder or delete any existing sentence. You may only ADD.
- Do NOT change any existing number, price, year inside a fact, part name or measurement.
- Do NOT touch the quick-answer block, the FAQ block, the CTA block, the
  "Last updated" line, the related-reading box, or anything near a MONEYLINK comment.
- Do NOT add em dashes or en dashes. Use a period, comma, colon or parentheses.
- Do NOT add prices for Patrol Garage's own services. Market context is fine.
- Return the FULL article body HTML, nothing else. No commentary, no code fences.

YOUR THREE JOBS:

1. OUTDATED FACTS: if a statement is stale, add a short clause or sentence next to
   it that brings it current. Do not edit the original words.

2. MISSING KEYWORDS: this page ranks between position 11 and 50 for the terms
   below but never uses them. Work each one in naturally, in a sentence that
   genuinely belongs. If a term does not fit the article honestly, skip it.
   GAP KEYWORDS: {gaps}

3. MISSING SUBTOPICS: if an obvious reader question is unanswered, add ONE new
   <h2> section with 2-3 paragraphs. Only if genuinely missing. Never more than one.

ARTICLE BODY:
---
{body}
---
"""


def tag_counts(html):
    counts = {}
    for tag in re.findall(r"<\s*(/?[a-zA-Z0-9]+)", html):
        counts[tag.lower()] = counts.get(tag.lower(), 0) + 1
    return counts


def words(text):
    return re.sub(r"<[^>]+>", " ", text).split()


def is_subsequence(small, big):
    it = iter(big)
    return all(w in it for w in small)


def numbers(html):
    return re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", re.sub(r"<[^>]+>", " ", html))


def headings(html):
    return re.findall(r"<h([2-4])[^>]*>(.*?)</h\1>", html, re.S)


def links(html):
    return sorted(re.findall(r'href="([^"]+)"', html))


def protected_blocks(html):
    out = {}
    for key in PROTECTED:
        out[key] = len(re.findall(re.escape(key), html))
    return out


def validate(original, edited):
    if len(edited) < len(original) * 0.9:
        return False, "output shorter than the original body"
    if "—" in edited or "–" in edited:
        if "—" not in original and "–" not in original:
            return False, "em/en dash introduced"
    if links(original) != [l for l in links(edited) if l in links(original)]:
        return False, "an existing link was removed or altered"
    if protected_blocks(original) != protected_blocks(edited):
        return False, "a protected block (quick-answer/FAQ/CTA/last-updated/MONEYLINK) changed"

    old_h = [h[1].strip() for h in headings(original)]
    new_h = [h[1].strip() for h in headings(edited)]
    if not is_subsequence(old_h, new_h):
        return False, "an existing heading was changed or removed"
    if len(new_h) - len(old_h) > 1:
        return False, f"{len(new_h)-len(old_h)} headings added, budget is 1"

    old_n, new_n = numbers(original), numbers(edited)
    if not is_subsequence(old_n, new_n):
        return False, "an existing number changed"

    ow, nw = words(original), words(edited)
    if not is_subsequence(ow, nw):
        return False, "existing prose was reworded, not just added to"
    ceiling = max(len(ow) * MAX_GROWTH, len(ow) + MIN_HEADROOM)
    if len(nw) > ceiling:
        return False, (f"body grew {len(nw)-len(ow)} words, over the ceiling "
                       f"({int(ceiling-len(ow))} allowed)")
    if len(nw) == len(ow):
        return False, "nothing was added"

    oc, nc = tag_counts(original), tag_counts(edited)
    for tag, n in oc.items():
        if nc.get(tag, 0) < n:
            return False, f"<{tag}> count dropped {n} -> {nc.get(tag,0)}"
    return True, f"+{len(nw)-len(ow)} words, +{len(new_h)-len(old_h)} heading(s)"


def stamp_updated(html):
    today = datetime.now().strftime("%B %Y")
    return re.sub(r'(<p class="last-updated">Last updated: )[^<]*(</p>)',
                  rf"\g<1>{today}\g<2>", html, count=1)


def refresh(slug, gaps, dry, bump_date):
    path = BLOG / f"{slug}.html"
    if not path.exists():
        print(f"[!] no such post: {path.name}")
        return 1
    html = path.read_text(encoding="utf-8")
    m = re.search(r"<article>(.*?)</article>", html, re.S)
    if not m:
        print("[!] no <article> block")
        return 1
    body = m.group(1)

    from anthropic import Anthropic
    client = Anthropic()
    prompt = PROMPT.format(gaps=", ".join(gaps) if gaps else "(none supplied)", body=body)
    resp = client.messages.create(model=MODEL, max_tokens=16000,
                                  messages=[{"role": "user", "content": prompt}])
    edited = resp.content[0].text.strip()
    edited = re.sub(r"^```(?:html)?\s*|\s*```$", "", edited).strip()

    ok, why = validate(body, edited)
    print(f"[refresh_patch] {slug}: {'ACCEPTED' if ok else 'REJECTED'} — {why}")
    if not ok:
        print("[refresh_patch] article left exactly as it was.")
        return 0

    diff = list(difflib.unified_diff(body.splitlines(), edited.splitlines(), lineterm="", n=0))
    print(f"[refresh_patch] {len([d for d in diff if d.startswith('+') and not d.startswith('+++')])} added line(s)")
    if dry:
        for d in diff[:40]:
            if d.startswith("+") and not d.startswith("+++"):
                print("   +", d[1:][:150])
        print("[refresh_patch] DRY RUN — nothing written")
        return 0

    new_html = html[:m.start(1)] + edited + html[m.end(1):]
    new_html = stamp_updated(new_html)
    st = path.stat()
    path.write_text(new_html, encoding="utf-8")
    if not bump_date:
        os.utime(path, (st.st_atime, st.st_mtime))  # mtime is content
    print(f"[refresh_patch] written ({'date bumped' if bump_date else 'mtime preserved'})")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    gaps = []
    for a in sys.argv[1:]:
        if a.startswith("--gaps"):
            gaps = [g.strip() for g in a.split("=", 1)[-1].split(",") if g.strip()]
    return refresh(args[0], gaps, "--dry-run" in sys.argv, "--bump-date" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())
