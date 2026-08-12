#!/usr/bin/env python3
"""Keyword-gap detector — the most actionable of the three refresh dimensions.

The question it answers, per page:

    "Which queries does this page already rank 11-50 for, that the article
     never actually says?"

That is a concrete content instruction, not a guess. A page sitting at position
14 for a term it never uses is usually one honest paragraph away from page 1.

Method
  1. GSC query+page, last 90 days, position 11-50 only (page-2 band: real
     visibility, no clicks).
  2. Map each page URL to its local file.
  3. Strip HTML to visible text and lowercase it.
  4. A query is a GAP if any of its content words (stopwords removed) appears
     ZERO times in that text. Partial gaps are reported too, ranked lower.
  5. Score = impressions x closeness-to-page-1, so the biggest, nearest misses
     surface first.

Output feeds refresh_patch.py's --gaps argument and orders refresh_scheduler's
queue by opportunity rather than by age.

Usage:
    python3 scripts/keyword_gaps.py                 # whole site
    python3 scripts/keyword_gaps.py <slug>          # one post
    python3 scripts/keyword_gaps.py --json          # machine-readable
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsc_client

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

MIN_POS, MAX_POS = 10.5, 50.0
MIN_IMPRESSIONS = 3

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "to", "in", "on", "at", "is",
    "are", "do", "does", "how", "what", "why", "when", "which", "with", "my",
    "your", "you", "it", "can", "i", "vs", "near", "me", "best", "much",
}


def visible_text(path):
    html = path.read_text(errors="ignore")
    m = re.search(r"<article>(.*?)</article>", html, re.S)
    body = m.group(1) if m else html
    head = re.findall(r"<title>([^<]*)</title>|<meta name=\"description\" content=\"([^\"]*)\"", html)
    extra = " ".join(x for pair in head for x in pair if x)
    text = re.sub(r"<[^>]+>", " ", body + " " + extra)
    return re.sub(r"\s+", " ", text).lower()


def slug_for_url(url):
    m = re.search(r"/blog/([a-z0-9-]+?)(?:\.html)?/?$", url)
    if m:
        return m.group(1)
    return None


def content_words(q):
    return [w for w in re.findall(r"[a-z0-9]+", q.lower()) if w not in STOPWORDS and len(w) > 1]


def analyse(rows, only_slug=None):
    by_slug = {}
    for r in rows:
        if not (MIN_POS <= r["position"] <= MAX_POS):
            continue
        if r["impressions"] < MIN_IMPRESSIONS:
            continue
        slug = slug_for_url(r["page"])
        if not slug or (only_slug and slug != only_slug):
            continue
        by_slug.setdefault(slug, []).append(r)

    results = []
    for slug, qs in by_slug.items():
        path = BLOG / f"{slug}.html"
        if not path.exists():
            continue
        text = visible_text(path)
        gaps = []
        for r in qs:
            ws = content_words(r["query"])
            if not ws:
                continue
            missing = [w for w in ws if w not in text]
            if not missing:
                continue
            # closeness to page 1: position 11 scores ~1.0, position 50 ~0.
            closeness = max(0.0, (MAX_POS - r["position"]) / (MAX_POS - MIN_POS))
            gaps.append({
                "query": r["query"],
                "impressions": r["impressions"],
                "position": round(r["position"], 1),
                "missing": missing,
                "full_gap": len(missing) == len(ws),
                "score": round(r["impressions"] * closeness * (1.5 if len(missing) == len(ws) else 1.0), 1),
            })
        if gaps:
            gaps.sort(key=lambda g: -g["score"])
            results.append({"slug": slug, "total_score": round(sum(g["score"] for g in gaps), 1),
                            "gaps": gaps})
    results.sort(key=lambda x: -x["total_score"])
    return results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    try:
        rows = gsc_client.query(["query", "page"], row_limit=25000)
    except gsc_client.GSCError as e:
        print(f"[keyword_gaps] {e}")
        return 1

    results = analyse(rows, args[0] if args else None)
    if as_json:
        print(json.dumps(results, indent=1))
        return 0

    if not results:
        print("[keyword_gaps] no gaps found in the position 11-50 band.")
        return 0

    print(f"[keyword_gaps] {len(results)} page(s) with keyword gaps, best opportunity first\n")
    for r in results[:15]:
        print(f"  {r['slug']}   (opportunity {r['total_score']})")
        for g in r["gaps"][:6]:
            tag = "NEVER SAID" if g["full_gap"] else "partial   "
            print(f"      {tag}  pos {g['position']:>4}  {g['impressions']:>4} impr  "
                  f"\"{g['query']}\"  missing: {', '.join(g['missing'][:5])}")
        print()
    print("Feed a page's gaps straight into patch mode:")
    print('  python3 scripts/refresh_patch.py <slug> --gaps="kw one,kw two" --dry-run')
    return 0


if __name__ == "__main__":
    sys.exit(main())
