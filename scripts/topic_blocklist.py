#!/usr/bin/env python3
"""Topics this site must never publish (owner, 2026-11-09).

A customer called the partner workshop asking for a tow bar after reading
/blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html, which closed with
"bring it to us at Patrol Garage". Neither this site nor the workshop it refers
to fits accessories. That post, the PPF, Y61 snorkel and Y63 dashcam posts were
deleted with 301s the same day, and these topics are blocked so the pipeline
cannot write them again. See topchallenger/site/research/
BLOG-SERVICE-AUDIT-2026-11-09.md, Appendix A.

Checked by:
  * keyword_generator.py  Gate 0c: a blocked candidate is never inserted
  * seed_ad_queue.py      a blocked Abu Dhabi keyword is never queued
  * run_pipeline.py       a blocked pending row is retired, not written
                          (image code: live after the next `railway up`)
  * generate.py           refuses a blocked keyword (exit 5) before any API call
  * assemble.py           refuses to assemble a blocked slug

Matching is on the keyword or slug, hyphens read as spaces. It only has to
recognise a TOPIC. Offer wording inside a post is test_no_offers.py's job.

    python3 scripts/topic_blocklist.py "y62 tow bar fitting cost"   # prints the topic or OK
"""
import re
import sys

# topic label -> pattern. Keep each one about the topic, not a single word that
# appears in ordinary repair keywords ("fitting" alone would block "fuel line
# fitting"; "install" alone would block "injector installation").
TOPICS = {
    "tow bars": r"\btow[\s-]?bars?\b|\btowbars?\b|\bhitch(?:es)?\b|\btrailer (?:wiring|hitch|harness|plug|socket)|\btow (?:ball|hitch|kit|package)",
    "PPF / paint protection": r"\bppf\b|\bpaint protection\b|\bprotection film\b|\bceramic coat\w*|\bwindow tint\w*|\btint(?:ing)? (?:film|cost|specialist|shop)\b|\bvinyl wrap\w*|\bcar wrap\w*",
    "snorkels": r"\bsnorkels?\b|\braised air intake\b",
    "dashcams": r"\bdash[\s-]?cams?\b|\bdashboard cameras?\b",
    "lift kits": r"\blift kits?\b|\bsuspension lift\b|\bbody lift\b|\blevell?ing kits?\b|\b\d(?:\.\d)?[\s-]?inch lift\b",
    "accessory fitting": r"\baccessor(?:y|ies)\b|\broof racks?\b|\bwinch(?:es)?\b|\bbull[\s-]?bars?\b|\bnudge bars?\b|\bside steps?\b|\brock sliders?\b|\bskid plates? install\w*|\bunderbody protection\b|\blight bars?\b|\bspotlights?\b|\bdual battery\b|\bfridge install\w*",
}
_COMPILED = {k: re.compile(v, re.I) for k, v in TOPICS.items()}


def blocked_topic(text):
    """The blocked topic `text` (a keyword or slug) belongs to, or None."""
    if not text:
        return None
    t = str(text).replace("-", " ").replace("_", " ")
    for label, rx in _COMPILED.items():
        if rx.search(t):
            return label
    return None


def is_blocked(text):
    return blocked_topic(text) is not None


if __name__ == "__main__":
    q = " ".join(sys.argv[1:])
    hit = blocked_topic(q)
    print(f"BLOCKED ({hit})" if hit else "OK")
    sys.exit(1 if hit else 0)
