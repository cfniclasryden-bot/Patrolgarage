#!/usr/bin/env python3
"""Topic-breadth gate: can this topic climb to a head term that has demand?

WHY THIS REPLACED THE VOLUME GATE
The first gate validated the exact target keyword's search volume. Measured
against the site's own history, that test is wrong — it would have rejected the
five best posts on the site (2,138 / 701 / 523 / 439 / 331 impressions), because
ALL 44 published posts target keywords with zero measured volume. Exact volume
carries no signal here.

What the GSC page-level data actually shows (90 days, top 10 posts):
  * 0 of 10 rank for the keyword they were built to target.
  * 86% of their impressions come from queries of 1-3 words.
  * Every target keyword was 5-9 words.

So posts do not rank AT the long tail they target — they rank UP it, on the
short head terms their topic contains. The long-tail keyword is a writing
prompt; the head term is the ranking target.

THE RULE
A candidate passes if some 1-3 word head term inside (or constructible from)
it has real demand. The candidate's own volume is irrelevant and is not checked
— zero is normal and is not disqualifying.

Bare brand heads do not count. "nissan patrol" measures 22,200/mo and appears
inside almost anything, so accepting it would wave everything through; it is
also not what any winner actually ranks for. Winners rank for "nissan patrol
y62", "nissan patrol y61", "nissan patrol service", "nissan patrol y62
problems" — model-qualified or topic-qualified, never the bare brand.

Component patterns stay banned. That is the one thing the data rules out
cleanly: every component post earned zero, and their head terms ("y62 water
pump", "y62 abs sensor") do not exist as queries either.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from keyword_volume import (  # noqa: E402
    VolumeError,
    banned_reason,
    search_volumes,
    shape_reason,
)

MIN_HEAD_VOLUME = int(os.environ.get("MIN_HEAD_VOLUME", "10"))

# Stripped before building heads: they qualify a query without being its topic.
GEO_YEAR = {
    "dubai", "uae", "abu", "dhabi", "sharjah", "ajman", "2024", "2025", "2026",
    "in", "the", "a", "for", "my", "and", "of", "to", "vs", "near", "me",
    "best", "cost", "price", "guide", "complete",
}

# Heads too generic to mean anything. "nissan patrol" is inside nearly every
# candidate, so allowing it would pass everything including component posts.
DISQUALIFIED_HEADS = {
    "nissan", "patrol", "nissan patrol", "car", "cars", "y61", "y62", "y63",
    "nissan y61", "nissan y62", "nissan y63", "patrol y61", "patrol y62",
    "patrol y63",
}

BRAND = {"nissan", "patrol", "y61", "y62", "y63"}


def head_candidates(keyword):
    """1-3 word heads contained in, or constructible from, the keyword."""
    toks = [t for t in re.findall(r"[a-z0-9]+", keyword.lower()) if t not in GEO_YEAR]
    heads = set()

    # contiguous n-grams
    for n in (1, 2, 3):
        for i in range(len(toks) - n + 1):
            heads.add(" ".join(toks[i:i + n]))

    # constructed: brand/model + each topic token, and + adjacent topic pairs.
    # This is what catches "nissan patrol gearbox problems" -> "nissan patrol
    # problems", where the useful head is not contiguous in the original.
    topic = [t for t in toks if t not in BRAND]
    models = [t for t in toks if t in {"y61", "y62", "y63"}]
    for t in topic:
        heads.add(f"nissan patrol {t}")
        for m in models:
            heads.add(f"nissan patrol {m} {t}")
            heads.add(f"{m} {t}")
    for a, b in zip(topic, topic[1:]):
        heads.add(f"{a} {b}")
        heads.add(f"nissan patrol {a} {b}")

    # A head must be >=2 words. Single words are generic English with big
    # meaningless volume — "service" 12,100, "gasket" 2,900, "rear" 1,000 —
    # and let component posts through on words that say nothing about whether
    # this site can rank.
    heads = {h for h in heads
             if h not in DISQUALIFIED_HEADS and 2 <= len(h.split()) <= 4}

    # The head must be brand- or model-qualified. Generic all-car phrases carry
    # real volume the site cannot capture: "head gasket" 480/mo, "rear
    # differential" 170, "service centre" 320 — every one of those let a
    # zero-earning component post through. A Patrol-only workshop ranks for
    # "nissan patrol <topic>", not for the topic in the abstract.
    heads = {h for h in heads if any(b in h.split() for b in BRAND)}

    # A head must also be about the TOPIC, not merely the model. Otherwise any
    # keyword containing "nissan patrol y62" (720/mo) passes, including
    # "...y62 head gasket replacement cost", which earned zero.
    #
    # Exception: when the keyword has no topic tokens at all, the model IS the
    # topic — that is the "complete guide" shape, the site's best-performing
    # post, and its head is legitimately "nissan patrol y62".
    topic = [t for t in toks if t not in BRAND]
    if topic:
        heads = {h for h in heads if any(t in h.split() for t in topic)}
    else:
        heads = {h for h in heads if any(m in h.split() for m in ("y61", "y62", "y63"))}

    return sorted(heads)


def evaluate(keywords, min_head=MIN_HEAD_VOLUME):
    """Return (accepted, rejected).

    accepted: [(keyword, best_head, head_volume), ...]
    rejected: [(keyword, reason), ...]

    Raises VolumeError if head volumes could not be established — callers must
    let that propagate and add nothing (fail closed, unchanged)."""
    rejected, candidates = [], []
    for k in keywords:
        k = k.strip().lower()
        why = shape_reason(k) or (
            f"banned component pattern {banned_reason(k)}" if banned_reason(k) else None
        )
        if why:
            rejected.append((k, why))
        else:
            candidates.append(k)
    if not candidates:
        return [], rejected

    heads_by_kw = {k: head_candidates(k) for k in candidates}
    all_heads = sorted({h for hs in heads_by_kw.values() for h in hs})
    vols = {}
    for i in range(0, len(all_heads), 700):
        vols.update(search_volumes(all_heads[i:i + 700]))

    accepted = []
    for k in candidates:
        scored = [(h, vols.get(h) or 0) for h in heads_by_kw[k]]
        scored.sort(key=lambda t: -t[1])
        best_h, best_v = scored[0] if scored else ("", 0)
        if best_v >= min_head:
            accepted.append((k, best_h, best_v))
        else:
            rejected.append((k, f"no head term reaches {min_head}/mo "
                                f"(best: {best_h!r} at {best_v})"))
    accepted.sort(key=lambda t: -t[2])
    return accepted, rejected


def main():
    args = [a for a in sys.argv[1:] if a.strip()]
    if not args:
        print(__doc__)
        return 1
    try:
        acc, rej = evaluate(args)
    except VolumeError as e:
        print(f"[breadth] {e}")
        return 1
    print(f"ACCEPTED ({len(acc)}):")
    for k, h, v in acc:
        print(f"  {v:>6}/mo via {h!r}\n           <- {k}")
    print(f"\nREJECTED ({len(rej)}):")
    for k, why in rej:
        print(f"  {k}\n      -> {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
