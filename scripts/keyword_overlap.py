#!/usr/bin/env python3
"""Two gates that stop the queue competing with the site's own pages.

1. TOPIC OVERLAP vs PUBLISHED posts (not just the queue).
   "y62 gearbox problems" and "y62 transmission problems" are one query to
   Google. The old dedup only compared candidates against other candidates and
   against exact keyword strings, so a synonym of a published pillar sailed
   through. This canonicalises synonyms before comparing, and compares against
   everything already published.

2. EXISTING GSC RANKING.
   If a page already ranks top 20 for the candidate or a close variant, a new
   post is a competitor to it, not an addition. Two pages splitting the same
   intent is how the praha blog ended up needing 301s. Strengthening the page
   that already ranks beats writing a rival to it.

Both gates REJECT. Gate 2 is evidence-based, so absence of a GSC row is not
evidence of absence — a candidate the site has never surfaced for simply
passes, which is correct.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAX_RANK = int(os.environ.get("OVERLAP_MAX_RANK", "20"))
OVERLAP_THRESHOLD = float(os.environ.get("OVERLAP_THRESHOLD", "0.7"))

# A GSC "ranking" needs enough evidence to mean anything. Position is an
# AVERAGE: a page that appeared once, at rank 2, reads as "#2.0" and is pure
# noise. Without this floor the gate rejected three good candidates on
# one-impression queries ('used', 'km mileage', 'nissan patrol problems').
MIN_RANK_IMPRESSIONS = int(os.environ.get("OVERLAP_MIN_IMPRESSIONS", "5"))

# Tokens that mean the same thing to a search engine. Mapped to a canonical
# form before comparison, so "gearbox" and "transmission" collide.
SYNONYMS = {
    "gearbox": "transmission", "gearboxes": "transmission", "transmissions": "transmission",
    "maintenance": "service", "servicing": "service", "serviced": "service", "services": "service",
    "price": "cost", "prices": "cost", "pricing": "cost", "costs": "cost",
    "issue": "problem", "issues": "problem", "problems": "problem",
    "fault": "problem", "faults": "problem", "trouble": "problem",
    "repairs": "repair", "fix": "repair", "fixing": "repair", "fixes": "repair",
    "aircon": "ac", "airconditioning": "ac", "conditioning": "ac",
    "buying": "buy", "purchase": "buy", "purchasing": "buy",
    "kilometres": "mileage", "kilometers": "mileage", "km": "mileage",
    "economy": "consumption", "mpg": "consumption",
    "motor": "engine", "engines": "engine",
    "suspensions": "suspension", "diff": "differential", "differentials": "differential",
    "reliable": "reliability", "dependable": "reliability",
}

# Dropped before comparison: qualifiers that do not change the topic.
NOISE = {
    "nissan", "patrol", "dubai", "uae", "abu", "dhabi", "sharjah", "the", "a",
    "in", "for", "my", "and", "of", "to", "best", "guide", "complete", "2024",
    "2025", "2026", "how", "what", "your", "with", "on", "at", "is", "are",
}


def canonical(text):
    """Topic fingerprint: synonym-folded, noise-stripped token set."""
    toks = re.findall(r"[a-z0-9]+", (text or "").lower())
    out = set()
    for t in toks:
        t = SYNONYMS.get(t, t)
        if t not in NOISE:
            out.add(t)
    return out


def _similarity(a, b):
    """Containment-biased overlap: if one topic's tokens sit entirely inside
    the other, that is a duplicate even when one is wordier.

    Containment needs at least two tokens on both sides. A one-token topic is
    contained in everything — the complete guide canonicalises to just {y62},
    which scored 100% against every candidate mentioning y62. With fewer than
    two tokens on either side, only exact equality counts as a duplicate."""
    if not a or not b:
        return 0.0
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0
    return len(a & b) / min(len(a), len(b))


def overlap_reason(candidate, published, threshold=OVERLAP_THRESHOLD):
    """published: iterable of (label, keyword_or_title). Returns reason or None."""
    ca = canonical(candidate)
    if not ca:
        return None
    best = (0.0, None, None)
    for label, text in published:
        s = _similarity(ca, canonical(text))
        if s > best[0]:
            best = (s, label, text)
    if best[0] >= threshold:
        return (f"topic overlap {best[0]:.0%} with published post "
                f"{best[1]!r} ({best[2]!r})")
    return None


def ranking_reason(candidate, heads, gsc_rows, max_rank=MAX_RANK):
    """Reject if a page already ranks <= max_rank for the candidate or a head.

    gsc_rows: rows from gsc_client.query(["query","page"]).
    """
    targets = {candidate.strip().lower()} | {h.strip().lower() for h in heads}
    tcanon = {frozenset(canonical(t)) for t in targets if canonical(t)}
    hits = []
    for r in gsc_rows:
        q = (r.get("query") or "").strip().lower()
        pos = r.get("position")
        impr = r.get("impressions", 0)
        if pos is None or pos > max_rank:
            continue
        # Enough evidence to call it a ranking, and a substantive query. A
        # single-word query canonicalises to one token that matches almost any
        # head, so it cannot carry a rejection on its own.
        if impr < MIN_RANK_IMPRESSIONS or len(q.split()) < 2:
            continue
        cq = frozenset(canonical(q))
        if len(cq) < 2:
            continue
        if q in targets or cq in tcanon:
            hits.append((q, pos, r.get("page", ""), impr))
    if not hits:
        return None
    hits.sort(key=lambda t: t[1])
    q, pos, page, impr = hits[0]
    page = page.replace("https://patrolgarage.ae", "") or "/"
    return (f"already ranks #{pos:.1f} for {q!r} ({impr} impr) via {page} — "
            f"strengthen that page instead")


def load_published():
    """(label, text) pairs for every published post: keyword AND title."""
    import json
    import pathlib
    out = []
    for p in sorted(pathlib.Path("blog").glob("*.html")):
        if p.name == "index.html":
            continue
        h = p.read_text(encoding="utf-8")
        m = re.search(r"<title>([^<]*)</title>", h)
        out.append((p.stem, m.group(1) if m else p.stem))
        out.append((p.stem, p.stem.replace("-", " ")))
    return out


def main():
    args = [a for a in sys.argv[1:] if a.strip()]
    if not args:
        print(__doc__)
        return 1
    from keyword_breadth import head_candidates
    import gsc_client
    from datetime import date, timedelta

    pub = load_published()
    end = (date.today() - timedelta(days=3)).isoformat()
    start = (date.today() - timedelta(days=93)).isoformat()
    rows = gsc_client.query(["query", "page"], start_date=start, end_date=end, row_limit=25000)

    for k in args:
        o = overlap_reason(k, pub)
        r = ranking_reason(k, head_candidates(k), rows)
        verdict = "REJECT" if (o or r) else "PASS"
        print(f"{verdict}  {k}")
        for why in (o, r):
            if why:
                print(f"        {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
