#!/usr/bin/env python3
"""check_city.py — an Abu Dhabi post must say so where it counts.

Ported 2026-10-09 from topchallenger-site (scripts/check_city.py there, added
2026-10-07), with the Abu Dhabi queue. A post whose slug names Abu Dhabi
(ad_city.ad_city_for) must carry "Abu Dhabi" or "Mussafah" in all four places
a searcher and Google read first:

  * <title>
  * the visible <h1>
  * <meta name="description">
  * the opening of the article: the quick answer or the first body paragraph

The slug carries it by construction. Every other post passes untouched, so
this is a no-op for the Dubai and UAE posts.

It also blocks ANY mention of the Y61 or Y63 on an Abu Dhabi post (2026-10-09,
owner decision), passing mentions included: title, meta, H1, body, FAQ,
related-reading links and JSON-LD. Only the site header and footer are
excluded. One post predates the rule; its mentions are frozen in
MODEL_BASELINE and a new one on that page still fails.

    python3 scripts/check_city.py                 # every post
    python3 scripts/check_city.py blog/<slug>.html

Exit 1 on any failure, so run_pipeline.py can use it as a blocking gate.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ad_city  # noqa: E402

CITY = re.compile(r"abu\s*dhabi|mussafah", re.I)
OTHER_MODEL = re.compile(r"\by6[13]\b", re.I)

# Abu Dhabi posts published before the Y61/Y63 rule: slug -> mentions allowed.
# Lower the number (or delete the entry) when the page is cleaned; never raise it.
MODEL_BASELINE = {
    "nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026": 5,  # Y63 section x3, Y61 link x2
}


def _scope(html):
    """Everything a reader or Google sees for this post, minus site chrome."""
    html = re.sub(r"<header\b.*?</header>", " ", html, flags=re.S)
    html = re.sub(r"<footer\b.*?</footer>", " ", html, flags=re.S)
    return html


def model_mentions(path):
    """Sentences (or link labels) on an Abu Dhabi post naming the Y61 or Y63."""
    if not ad_city.ad_city_for(path.stem):
        return []
    scope = _scope(path.read_text(encoding="utf-8"))
    hits = []
    for m in OTHER_MODEL.finditer(scope):
        start = max(scope.rfind(".", 0, m.start()), scope.rfind(">", 0, m.start())) + 1
        end_dot = scope.find(".", m.end())
        end_tag = scope.find("<", m.end())
        ends = [e for e in (end_dot + 1 if end_dot >= 0 else -1, end_tag) if e > 0]
        end = min(ends) if ends else len(scope)
        hits.append(re.sub(r"\s+", " ", scope[start:end]).strip())
    return hits


def _text(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or "")).strip()


def problems(path):
    """List of the places that lack the city; [] if fine or not an Abu Dhabi post."""
    if not ad_city.ad_city_for(path.stem):
        return []
    html = path.read_text(encoding="utf-8")
    out = []
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    art = re.search(r"<article>(.*?)</article>", html, re.S)
    # The early CTA sits between the quick answer and the intro; it is not the opening.
    body = re.sub(r'<div class="early-cta".*?</div>', "", art.group(1) if art else "", flags=re.S)
    paras = [p for p in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", body, re.S)
             if "Part of:" not in p][:2]
    for name, val in (("<title>", title and title.group(1)), ("<h1>", h1 and h1.group(1)),
                      ("meta description", desc and desc.group(1))):
        if not CITY.search(_text(val)):
            out.append(name)
    if not any(CITY.search(_text(p)) for p in paras):
        out.append("first paragraph")
    n = len(model_mentions(path))
    if n > MODEL_BASELINE.get(path.stem, 0):
        out.append(f"Y61/Y63 mentioned ({n}x; none allowed on an Abu Dhabi post)")
    return out


def main():
    files = [Path(a) for a in sys.argv[1:]] or sorted(
        p for p in (ROOT / "blog").glob("*.html") if p.name != "index.html")
    bad, checked = 0, 0
    for f in files:
        f = f if f.is_absolute() else ROOT / f
        if ad_city.ad_city_for(f.stem):
            checked += 1
        miss = problems(f)
        if miss:
            bad += 1
            print(f"[!] {f.stem}: {'; '.join(miss)}")
            for sent in model_mentions(f)[:10]:
                print(f"      Y61/Y63: {sent[:160]}")
    if bad:
        print(f"[!] City check: {bad} Abu Dhabi post(s) missing the city.")
        return 1
    print(f"[+] City check: {checked} Abu Dhabi post(s), city present in title, H1, meta and opening, no Y61/Y63.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
