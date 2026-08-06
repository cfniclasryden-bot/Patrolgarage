#!/usr/bin/env python3
"""humour_pass.py — add 3-5 humour beats to a generated draft, then verify nothing else moved.

Runs between generate.py and assemble.py. Operates on drafts/{slug}.html (body prose only,
before schema/nav/hero are wrapped around it by assemble.py).

Applies the house humour-writing rules: sprinkle, never slather; no jokes inside prices,
safety, FAQ answers or the quick-answer block; never change a fact.

The model rewrites the whole body and returns it. Everything it returns is then checked
against the original. If ANY check fails the draft is left exactly as generate.py wrote it.
The pass never fails the pipeline: worst case the post publishes deadpan, which is the
old behaviour.

Disable with HUMOUR_PASS=0 in the Railway env.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DRAFTS_DIR = PROJECT_ROOT / "drafts"

# Budget from the humour-writing skill: 3-5 beats for a 1,500-2,200 word post.
MAX_CHANGED_BLOCKS = 5
MAX_GROWTH = 1.12  # a beat is a clause, not a paragraph


def log(msg):
    print(f"[humour_pass] {msg}", flush=True)


PROMPT = """You are adding humour to a finished blog post for Patrol Garage, a Nissan Patrol \
specialist workshop in Ras Al Khor, Dubai. The readers are Patrol owners in the UAE, often \
reading because something on their truck is broken and they are worried about the bill.

The post is already written. You are NOT rewriting it. You are inserting a few small humour \
beats into the existing prose and returning the whole body back unchanged apart from those \
insertions.

THE BUDGET
- Three to five humour beats in the entire post. Not per section. Total.
- Never two beats in the same H2 section, and never in consecutive paragraphs.
- A beat is ONE wry clause, ONE dry aside, or ONE concrete overstatement. It is never a \
paragraph of material.
- Zero beats is a valid answer. If the post is wall-to-wall pricing and FAQ, return it \
unchanged.

NO-JOKE ZONES. These stay completely deadpan, no exceptions:
- The <div class="direct-answer"> quick-answer block.
- Every <div class="faq"> block. Those get lifted into search results without context.
- Any sentence containing a price, an AED figure, a km interval, a temperature, a year, a \
part name or a measurement.
- Safety and urgency advice, anything a reader could act on wrongly and get hurt or land a \
repair bill.
- The final "When to bring it to Patrol Garage" section and the <div class="cta"> block.
- The first sentence of the post, and the one-sentence direct answer under each H2.

HARD RULES
1. Never change a fact to land a joke. Not a number, an interval, a symptom, a duration, a \
price, a part name, a temperature. If a sentence carries a figure, the humour goes in a \
neighbouring sentence or nowhere.
2. Never joke at the reader's expense. Not at a competitor, a nationality, a religion, a \
gender or a body either. The subject of the joke is the writer, the situation, or an \
inanimate object (the gearbox that would rather be out on the dunes).
3. A joke that does not land gets deleted, not hedged. No "sort of", no winking parentheticals.
4. No em dashes or en dashes anywhere. Use a full stop or a comma.
5. No rule-of-three lists, no "not just X, but Y", no manufactured punchlines.
6. Keep it PG-13 and light-hearted. Nothing political, nothing controversial.

WHERE HUMOUR ACTUALLY WORKS HERE, best first:
1. The shared frustration every UAE Patrol owner already grumbles about (August heat, Sheikh \
Zayed Road at 6pm, sand in everything after a dune run). The reader is in on it.
2. Self-deprecation from the workshop.
3. The object personified lightly, kept to a clause.
4. The gap between an expensive-sounding diagnosis and a boring truth.

MECHANICAL RULES. These are checked automatically and a violation means your whole output \
is thrown away:
- Return the COMPLETE HTML body, start to finish. Not a diff, not a fragment, no commentary, \
no markdown fences.
- You may ONLY INSERT words. Every word of the original must still be present, in the same \
order. Do not reword, reorder, shorten, tidy or re-punctuate anything.
- Do not touch headings, links, anchor text, the <div class="direct-answer"> block, any \
<div class="faq"> block, the <div class="cta"> block, or the last-updated line.
- Do not add, remove or reorder any HTML tag.

Here is the post body:

---
{body}
---

Return the complete HTML body with your beats inserted, and nothing else."""


def words(text):
    return re.findall(r"[A-Za-z0-9]+", text)


def is_subsequence(small, big):
    """Every token of `small` appears in `big`, in order. True when `big` is `small`
    with words inserted, false the moment anything was deleted or reworded."""
    it = iter(big)
    return all(tok in it for tok in small)


def blocks(html):
    """Ordered text of every prose block, so we can tell which ones changed."""
    return re.findall(r"<(?:p|li)\b[^>]*>(.*?)</(?:p|li)>", html, re.S | re.I)


def numbers(html):
    # Standalone figures only. "V8" and "4x4" are words, 45 and 8,000 are facts.
    return sorted(re.findall(r"(?<![A-Za-z0-9])\d[\d,\.]*(?![A-Za-z0-9])", html))


def headings(html):
    return re.findall(r"<(h[1-6])\b[^>]*>(.*?)</\1>", html, re.S | re.I)


def links(html):
    return re.findall(r"<a\b[^>]*>.*?</a>", html, re.S | re.I)


def protected_blocks(html):
    """Chunks that must come back byte-identical."""
    out = []
    out += re.findall(r'<div class="direct-answer">.*?</div>', html, re.S)
    out += re.findall(r'<div class="faq">.*?</div>', html, re.S)
    out += re.findall(r'<div class="cta">.*?</div>', html, re.S)
    out += re.findall(r'<p class="last-updated">.*?</p>', html, re.S)
    return out


def tag_counts(html):
    counts = {}
    for tag in re.findall(r"<\s*(/?[a-zA-Z0-9]+)", html):
        counts[tag.lower()] = counts.get(tag.lower(), 0) + 1
    return counts


def verify(original, edited):
    """Return (ok, reason). Anything suspicious means we keep the deadpan draft."""
    if len(edited) < 500:
        return False, "output too short to be the full body"

    dashes = lambda s: s.count("—") + s.count("–")
    if dashes(edited) > dashes(original):
        return False, "em/en dash introduced"

    if numbers(original) != numbers(edited):
        return False, "a number changed"

    if headings(original) != headings(edited):
        return False, "a heading changed"

    if links(original) != links(edited):
        return False, "a link changed"

    if protected_blocks(original) != protected_blocks(edited):
        return False, "quick-answer, FAQ, CTA or last-updated block changed"

    if tag_counts(original) != tag_counts(edited):
        return False, "HTML tag structure changed"

    orig_blocks, new_blocks = blocks(original), blocks(edited)
    if len(orig_blocks) != len(new_blocks):
        return False, "paragraph/list-item count changed"

    changed = 0
    for old, new in zip(orig_blocks, new_blocks):
        if old == new:
            continue
        changed += 1
        old_w, new_w = words(old), words(new)
        if not is_subsequence(old_w, new_w):
            return False, "existing prose was reworded, not just added to"
        if len(new_w) > len(old_w) + 40:
            return False, "a beat ran long (more than a clause)"

    if changed == 0:
        return False, "no beats added"
    if changed > MAX_CHANGED_BLOCKS:
        return False, f"{changed} blocks touched, budget is {MAX_CHANGED_BLOCKS}"

    ow, nw = len(words(original)), len(words(edited))
    if nw > ow * MAX_GROWTH:
        return False, f"body grew {nw - ow} words, over the {int((MAX_GROWTH - 1) * 100)}% ceiling"

    return True, f"{changed} beats added, +{nw - ow} words"


def strip_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:html)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def run(slug):
    if os.environ.get("HUMOUR_PASS", "1").strip().lower() in ("0", "off", "false", "no"):
        log("disabled via HUMOUR_PASS, leaving draft deadpan")
        return

    draft_path = DRAFTS_DIR / f"{slug}.html"
    if not draft_path.exists():
        log(f"no draft at {draft_path}, skipping")
        return

    original = draft_path.read_text(encoding="utf-8")

    try:
        from anthropic import Anthropic
        client = Anthropic()
        kwargs = dict(
            model="claude-opus-5",
            max_tokens=16000,
            messages=[{"role": "user", "content": PROMPT.format(body=original)}],
        )
        try:
            msg = client.messages.create(output_config={"effort": "medium"}, **kwargs)
        except TypeError:
            # older SDK in the container image, effort is optional anyway
            msg = client.messages.create(**kwargs)
    except Exception as e:
        log(f"[!] API call failed ({type(e).__name__}: {e}), keeping deadpan draft")
        return

    if getattr(msg, "stop_reason", None) == "refusal":
        log("[!] request refused, keeping deadpan draft")
        return

    edited = strip_fences("".join(b.text for b in msg.content if b.type == "text"))

    ok, reason = verify(original, edited)
    if not ok:
        log(f"[!] REJECTED: {reason}. Publishing the deadpan draft unchanged.")
        return

    draft_path.write_text(edited, encoding="utf-8")
    log(f"applied: {reason}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 humour_pass.py <slug>")
        sys.exit(1)
    try:
        run(" ".join(sys.argv[1:]).strip())
    except Exception as e:
        # Never take the daily post down over a joke.
        log(f"[!] unexpected error ({type(e).__name__}: {e}), keeping deadpan draft")
    sys.exit(0)
