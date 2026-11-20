#!/usr/bin/env python3
"""Blocking pre-draft gate for the post rules in BLOG-AUDIT-2026-11-20 §6.1-6.2.
Identical in topchallenger-site and patrolgarage.

    python3 scripts/check_post_rules.py blog/<slug>.html
    python3 scripts/check_post_rules.py --refresh blog/<slug>.html   # refresh of an existing post

REFRESH (2026-11-20): a rewrite of a post that is already live needs no backlog
entry and no evidence. Its service page is the one the post links (the backlog
entry's, if it has one), its branch comes from the slug, and the photo rule
applies only if a backlog entry names a photo. Every other check is the same,
and a refresh is still draft-only (draft.py, then approve.py).

Exit 2 with one line per problem. Checks, in order:

  topic      the post is a backlog entry (scripts/editorial_backlog.json) with
             evidence, a confirmed service page and no open owner question
  link       ONE service page: the entry's page is linked in the first third
             of the article; no other specific service page is linked (TC: the
             same service's other-branch twin is allowed, and a valve body post
             may link the gearbox pages)
  cta        branch CTA. TC: a WhatsApp link in the article with the branch's
             own number (Ras Al Khor 971566080951, Mussafah 971558175637).
             PG: "Ask us about your Patrol on WhatsApp" and its WhatsApp link.
  photo      TC: the hero is the workshop photo the entry names, if it names
             one. PG: no Top Challenger photograph anywhere on the page.
  answer     an answer block in the first 15% of the article, 25-90 words
  title      under 60 characters before the brand suffix, no year
  meta       no booking line in the meta description
  faq        3 to 5 questions in the FAQPage JSON-LD
  length     1,200 to 1,800 words of article text
  headings   no "Conclusion" / "Summary" / "Final thoughts" H2
  codes      no part / engine / gearbox codes (JR710E, VK56VD, TB48...) in the
             title, metas, JSON-LD headline/description or the answer block
  opener     no "This post covers" / "This article" / "In this guide" in a meta
  procedure  no first-person workshop procedure ("we check / change / measure /
             drop / scan...") unless a first-person sentence on the linked service
             page says the same (half its content words or more)
"""
import html as _html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_rules as er  # noqa: E402

TC_NUM = {"ras_al_khor": ["971566080951"], "mussafah": ["971558175637"],
          "both": ["971566080951", "971558175637"]}
PG_NUM = "971558175637"
BRAND_SUFFIX = re.compile(r"\s*\|\s*(?:Top Challenger|Patrol Garage(?: Dubai)?)\s*$")
WORDS_MIN, WORDS_MAX = 1200, 1800
# Part, engine and gearbox codes (2026-11-20). Fault codes (P0430) are topics,
# not part codes, and stay allowed.
PART_CODE = re.compile(r"\b(?:JR\d{3}[A-Z]{0,2}|VK\d{2}[A-Z]{0,4}|VQ\d{2}[A-Z]{0,4}|RE\d[A-Z]\d{2}[A-Z]?"
                       r"|TB\d{2}[A-Z]{0,2}|TD\d{2}[A-Z]{0,2}|ZD\d{2}[A-Z]{0,2}|KLE\w{5,})\b")
META_OPENER = re.compile(r"\b(?:this|the) (?:post|article|guide|page|blog)\b|\bin this (?:post|article|guide)\b"
                         r"|\bhere(?:'s| is) (?:what|everything)\b", re.I)
FIRST_PERSON_PROC = re.compile(
    r"\b(?:we|our (?:team|technicians?|mechanics?|workshop))\b(?:\s+\w+){0,3}?\s+"
    r"(?:check|checks|change|changes|replace|replaces|measure|measures|inspect|inspects|test|tests|scan|scans|"
    r"look at|looks at|drop|drops|pull|pulls|remove|removes|flush|flushes|clean|cleans|rebuild|rebuilds|strip|"
    r"strips|run|runs|fit|fits|use|uses|start with|starts with|reset|resets|read|reads|combine|pressure-test|"
    r"road-test|top up|bleed|recharge|refill|swap)\b", re.I)
STOP = set("the a an and or of to in on at for with is are be it its this that as by from into before after "
           "any not no if then than we our us you your y62 patrol nissan".split())


def _content_words(t):
    return {w for w in re.findall(r"[a-z][a-z'-]+", t.lower()) if w not in STOP and len(w) > 2}


def _service_page_sentences(target):
    f = er.page_file(target) if target else None
    if not f or not f.exists():
        return []
    raw = f.read_text(encoding="utf-8")
    m = re.search(r"<main\b.*?</main>", raw, re.S) or re.search(r"</header>(.*?)<footer", raw, re.S)
    t = _text(m.group(0)) if m else ""
    return [x for x in re.split(r"(?<=[.!?])\s+", t) if re.search(r"\b(?:we|our|us)\b", x, re.I)]
ANSWER_MIN, ANSWER_MAX = 25, 90


def _text(fragment):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", _html.unescape(t)).strip()


def _words(t):
    return len(re.findall(r"[A-Za-z0-9'’-]+", t))


def _norm(href):
    h = re.sub(r"^https?://(?:www\.)?(?:topchallenger|patrolgarage)\.ae", "", href)
    h = h.split("#")[0].split("?")[0]
    if h.startswith(".."):
        h = h[2:]
    if er.SITE == "tc" and h.endswith(".html"):
        h = h[:-5]
    return h


def _twins(target):
    if er.SITE != "tc":
        return set()
    out = set()
    if target.endswith("-dubai"):
        out.add(target[:-len("-dubai")] + "-abu-dhabi")
    if target.endswith("-abu-dhabi"):
        out.add(target[:-len("-abu-dhabi")] + "-dubai")
    if target == "/services/y62-valve-body-repair":
        out |= {"/services/y62-gearbox-repair-dubai", "/services/y62-gearbox-repair-abu-dhabi"}
    return out


HUBS = {"tc": {"/services", "/abu-dhabi", "/contact", "/"},
        "pg": {"/services.html", "/y62-garage-dubai.html", "/nissan-patrol-abu-dhabi.html",
               "/contact.html", "/"}}


def _refresh_entry(slug, art):
    """A stand-in backlog entry for a refresh: the post's own first service link."""
    import topic_blocklist
    confirmed = {_norm(c): c for c in er.confirmed_service_pages()}
    hubs = HUBS[er.SITE] - ({"/services.html"} if er.SITE == "pg" else set())
    target = None
    for mm in re.finditer(r'<a\b[^>]*href="([^"]+)"', art):
        h = _norm(mm.group(1))
        if h in confirmed and h not in hubs:
            target = confirmed[h]
            break
    branch = "mussafah" if re.search(r"abu-dhabi|mussafah", slug) else "ras_al_khor"
    blocked = topic_blocklist.blocked_topic(slug)
    return {"slug": slug, "service_page": target, "branch": branch, "_blocked": blocked}


def problems(path, refresh=False):
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    slug = path.stem
    out = []
    m = re.search(r"<article\b[^>]*>(.*?)</article>", raw, re.S)
    art = m.group(1) if m else ""
    e = er.entry_for(slug)
    if refresh and not e:
        e = _refresh_entry(slug, art)
        if e["_blocked"]:
            out.append(f"topic: blocked topic ({e['_blocked']})")
        if not e["service_page"]:
            out.append("link: the post links no service page (a refresh keeps one)")
            e["service_page"] = "/__none__"
    elif not e:
        return [f"topic: {slug} is not in scripts/editorial_backlog.json (topics come from the backlog only; "
                "an existing post goes through --refresh)"]
    else:
        tp = [p for p in er.topic_problems(e) if p not in ("already published", "draft already waiting for review")]
        if refresh:
            tp = [p for p in tp if not p.startswith("no evidence")]
        out += [f"topic: {p}" for p in tp]

    if not art:
        return out + ["structure: no <article> element"]
    art_clean = re.sub(r'<div class="related-reading">.*?</div>|<!--.*?-->', " ", art, flags=re.S)
    text = _text(art_clean)

    # link
    target = e["service_page"]
    confirmed = er.confirmed_service_pages()
    hrefs = [(mm.start(), _norm(mm.group(1))) for mm in re.finditer(r'<a\b[^>]*href="([^"]+)"', art)]
    first = next((pos for pos, h in hrefs if h == _norm(target)), None)
    if first is None and target != "/__none__":
        out.append(f"link: the post does not link its service page {target}")
    else:
        share = len(_text(art[:first])) / max(len(_text(art)), 1)
        if share > 0.34:
            out.append(f"link: first link to {target} sits {share:.0%} into the article (must be in the first third)")
    allowed = {_norm(target)} | {_norm(t) for t in _twins(target)} | HUBS[er.SITE]
    others = sorted({h for _p, h in hrefs if h in {_norm(c) for c in confirmed} and h not in allowed})
    if others:
        out.append(f"link: links other service pages {others} (one service page per post)")

    # cta: the article plus the CTA block after it, without the site chrome
    # (header/footer carry the plain numbers on every page).
    content = re.sub(r"<header\b.*?</header>|<footer\b.*?</footer>", " ", raw, flags=re.S)
    if er.SITE == "tc":
        nums = TC_NUM.get(e.get("branch", "ras_al_khor"), TC_NUM["ras_al_khor"])
        if not any(re.search(r'href="https://wa\.me/' + n, content) for n in nums):
            out.append(f"cta: no WhatsApp link with the {e.get('branch')} number in the article")
    else:
        if "Ask us about your Patrol on WhatsApp" not in _text(content):
            out.append('cta: missing the closing line "Ask us about your Patrol on WhatsApp"')
        if f"wa.me/{PG_NUM}" not in content:
            out.append("cta: no WhatsApp link in the article")

    # photo
    if er.SITE == "tc":
        if e.get("photo"):
            hero = re.search(r'<div class="hero-bg">.*?<img[^>]*src="([^"]+)"', raw, re.S)
            if not hero or e["photo"] not in hero.group(1):
                out.append(f"photo: hero is not the workshop photo {e['photo']}")
    else:
        if re.search(r'(?:src|srcset|content)="[^"]*top-challenger[^"]*"', raw):
            out.append("photo: a Top Challenger photograph is on a patrolgarage.ae page")

    # answer first
    am = (re.search(r'<div class="direct-answer"[^>]*>(.*?)</div>', art, re.S)
          or re.search(r"<p>\s*(?:<strong>)?\s*Quick answer:?.*?</p>", art, re.S | re.I))
    if not am:
        out.append("answer: no answer block (direct-answer / Quick answer)")
    else:
        at = _text(am.group(0))
        pos = len(_text(art[:am.start()])) / max(len(_text(art)), 1)
        n = _words(re.sub(r"^\s*Quick answer:?\s*", "", at, flags=re.I))
        if pos > 0.15:
            out.append(f"answer: the answer block sits {pos:.0%} into the article (first 15%)")
        if not ANSWER_MIN <= n <= ANSWER_MAX:
            out.append(f"answer: {n} words (want {ANSWER_MIN}-{ANSWER_MAX})")

    # title
    tm = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = _html.unescape(tm.group(1)).strip() if tm else ""
    core = BRAND_SUFFIX.sub("", title)
    if len(core) >= 60:
        out.append(f"title: {len(core)} characters before the brand suffix (under 60): {core!r}")
    if re.search(r"\b(?:19|20)\d\d\b", core) and not e.get("year_ok"):
        out.append(f"title: carries a year: {core!r}")

    # meta
    dm = re.search(r'<meta name="description" content="([^"]*)"', raw)
    desc = _html.unescape(dm.group(1)) if dm else ""
    if re.search(r"\b(?:book|call us|get a quote|get diagnosed|contact us)\b", desc, re.I):
        out.append(f"meta: booking line in the description: {desc!r}")

    # faq
    n_q = 0
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        try:
            data = json.loads(blk)
        except Exception:
            continue
        for node in (data.get("@graph", [data]) if isinstance(data, dict) else data):
            if isinstance(node, dict) and node.get("@type") == "FAQPage":
                n_q += len(node.get("mainEntity", []))
    if not 3 <= n_q <= 5:
        out.append(f"faq: {n_q} questions in the FAQPage JSON-LD (want 3-5)")

    # length
    n = _words(text)
    if not WORDS_MIN <= n <= WORDS_MAX:
        out.append(f"length: {n:,} words (want {WORDS_MIN:,}-{WORDS_MAX:,})")

    # codes: title, metas, JSON-LD headline/description, answer block
    heads = [("title", title), ("meta", desc)]
    for mm in re.finditer(r'<meta\s+(?:name|property)="(og:title|og:description|twitter:title|twitter:description)"'
                          r'\s+content="([^"]*)"', raw):
        heads.append((mm.group(1), _html.unescape(mm.group(2))))
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        for mm in re.finditer(r'"(headline|description)"\s*:\s*"((?:[^"\\]|\\.)*)"', blk):
            heads.append((f"json-ld {mm.group(1)}", mm.group(2)))
    if am:
        heads.append(("answer block", _text(am.group(0))))
    for where, txt in heads:
        c = PART_CODE.search(txt or "")
        if c:
            out.append(f"codes: part code {c.group(0)!r} in the {where}")
        if where != "answer block" and where != "title" and META_OPENER.search(txt or ""):
            out.append(f"opener: '{META_OPENER.search(txt).group(0)}' in the {where} (lead with the answer)")

    # procedure: first-person workshop process must match the service page
    svc = _service_page_sentences(target) + sum((_service_page_sentences(t) for t in _twins(target)), [])
    svc_words = [_content_words(x) for x in svc]
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if not FIRST_PERSON_PROC.search(sent):
            continue
        cw = _content_words(sent)
        best = max((len(cw & w) / max(len(cw), 1) for w in svc_words), default=0)
        if best < 0.5:
            out.append(f"procedure: first-person workshop claim not on the service page: {sent[:150]!r}")

    # headings
    for h in re.findall(r"<h2[^>]*>(.*?)</h2>", art, re.S):
        if re.search(r"\b(?:conclusion|in summary|summary|final thoughts|wrapping up)\b", _text(h), re.I):
            out.append(f"headings: {_text(h)!r} (no conclusion heading)")
    return out


def feedback(path, refresh=False):
    """The post-rules problems as instructions for the ONE regenerate (2026-11-20).

    Lines start with "FIX: " so generate.retry_block() renders them as
    instructions, not as claims to delete. Problems a rewrite cannot fix (topic,
    service-link placement, photo) are left out: those are assembler or backlog
    matters.
    """
    out = []
    for p in problems(path, refresh=refresh):
        kind, _, detail = p.partition(": ")
        if kind == "length":
            out.append(f"FIX: the article was {detail.split(' (')[0]}; write about 1,400 words of article text, "
                       f"never more than 1,700, and keep every section short.")
        elif kind in ("opener", "meta"):
            out.append("FIX: the meta description must state the answer in its first words. Never "
                       "'This post', 'The post', 'This article', 'This guide' or a booking line. " + detail)
        elif kind == "codes":
            out.append("FIX: no part or engine codes (JR710E, VK56VD...) in the title, meta or direct answer; "
                       "name the part in words. " + detail)
        elif kind == "procedure":
            out.append("FIX: this sentence describes the workshop's own procedure in the first person; "
                       "rewrite it as general advice with no 'we': " + detail.split("service page: ", 1)[-1])
        elif kind in ("answer", "title", "faq", "headings"):
            out.append(f"FIX: {kind}: {detail}")
    return out


def main(argv):
    files = [a for a in argv if not a.startswith("--")]
    refresh = "--refresh" in argv
    if not files:
        print(__doc__)
        return 1
    bad = 0
    for f in files:
        for p in problems(f, refresh=refresh):
            bad += 1
            print(f"  BLOCK {f}: {p}")
    if bad:
        print(f"[!] check_post_rules: {bad} problem(s)")
        return 2
    print(f"[OK] check_post_rules: {len(files)} post(s) meet the post rules")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
