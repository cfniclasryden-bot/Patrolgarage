#!/usr/bin/env python3
"""Regression for the Abu Dhabi hub, routing and queue (2026-10-09). Spends nothing.

  * ad_city.ad_city_for / is_ad_page: which slugs and pages are Abu Dhabi;
  * check_city.problems(): an Abu Dhabi post needs the city in title, H1, meta
    and opening, and a Dubai post is ignored;
  * apply_routing(): the ask with pg-ad-wa / pg-ad-wa-ar / pg-ad-call, every
    WhatsApp pre-fill starting "Mussafah:", the Arabic one intact, idempotent;
  * every shipped Abu Dhabi page already carries that routing;
  * the hub: Y62-led title and H1, one Mussafah statement, areas served once,
    FAQPage with the three ownership questions, no price, figure, interval,
    premises claim or partner name;
  * generate.py adds the city block for an Abu Dhabi slug only;
  * the picker orders by queue_position first, and a requeue clears it;
  * seed_ad_queue's keywords pass Gate 0b and the order is AD, AD, other.

    python3 scripts/test_ad_queue.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ad_city      # noqa: E402
import check_city   # noqa: E402
import seed_ad_queue as seed  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


# ------------------------------------------------------------------ city
check(ad_city.ad_city_for("is-the-nissan-patrol-reliable-in-abu-dhabi") == "Abu Dhabi", "slug not AD")
check(ad_city.ad_city_for("nissan patrol long term ownership abu dhabi") == "Abu Dhabi", "kw not AD")
check(ad_city.ad_city_for("nissan-patrol-y62-problems-dubai") is None, "Dubai slug read as AD")
check(ad_city.is_ad_page("nissan-patrol-abu-dhabi.html"), "hub not an AD page")
check(ad_city.is_ad_page("blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html"), "AD post")
check(not ad_city.is_ad_page("blog/nissan-patrol-service-cost-dubai.html"), "Dubai post read as AD")

tmp = Path(subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip())
good = tmp / "nissan-patrol-long-term-ownership-abu-dhabi.html"
good.write_text('<title>Owning a Y62 in Abu Dhabi | Patrol Garage</title>'
                '<meta name="description" content="What keeping a Y62 in Abu Dhabi involves.">'
                '<h1>Y62 ownership, Abu Dhabi</h1><article><div class="direct-answer"><p>'
                '<strong>Quick answer:</strong> In Abu Dhabi the Y62 holds up when ...</p></div>'
                '<div class="early-cta" data-cta="early"><p>Own one?</p></div><p>Intro.</p></article>')
check(check_city.problems(good) == [], f"good AD page flagged: {check_city.problems(good)}")
bad = tmp / "is-the-nissan-patrol-reliable-in-abu-dhabi.html"
bad.write_text('<title>Y62 reliability | Patrol Garage</title><meta name="description" content="x">'
               '<h1>Y62 reliability</h1><article><p>Intro.</p><p>More.</p></article>')
check(check_city.problems(bad) == ["<title>", "<h1>", "meta description", "first paragraph"],
      f"bad AD page not fully flagged: {check_city.problems(bad)}")
dubai = tmp / "nissan-patrol-brake-problems.html"
dubai.write_text(bad.read_text())
check(check_city.problems(dubai) == [], "a Dubai post must be ignored")

# --------------------------------------------- Y61 / Y63 on Abu Dhabi posts
def ad_post(name, body="<p>Intro in Abu Dhabi.</p>", title="Y62 in Abu Dhabi | Patrol Garage",
            extra=""):
    f = tmp / f"{name}.html"
    f.write_text(f'<header><a>Y61 nav</a></header><title>{title}</title>'
                 '<meta name="description" content="Abu Dhabi owners.">'
                 f'<h1>Y62, Abu Dhabi</h1><article>{body}{extra}</article>'
                 '<footer>Y63 footer</footer>')
    return f


MODEL = "Y61/Y63 mentioned"
clean = ad_post("nissan-patrol-long-term-ownership-abu-dhabi")
check(check_city.problems(clean) == [], f"clean AD post flagged (header/footer must not count): "
      f"{check_city.problems(clean)}")
passing = ad_post("what-to-check-on-a-used-nissan-patrol-in-abu-dhabi",
                  body="<p>Intro in Abu Dhabi.</p><p>Unlike the Y63, it is simple.</p>")
check(any(MODEL in x for x in check_city.problems(passing)), "a passing Y63 mention must block")
check(check_city.model_mentions(passing) == ["Unlike the Y63, it is simple."],
      f"flagged sentence for the retry: {check_city.model_mentions(passing)}")
link = ad_post("how-abu-dhabi-heat-affects-nissan-patrol-maintenance",
               extra="<ul><li><a href='/blog/nissan-patrol-y61-dubai-complete-guide'>Owner guide</a></li></ul>")
check(any(MODEL in x for x in check_city.problems(link)), "a related link to a Y61 post must block")
titled = ad_post("is-the-nissan-patrol-reliable-in-abu-dhabi", title="Y62 vs y61 in Abu Dhabi")
check(any(MODEL in x for x in check_city.problems(titled)), "a lowercase y61 in the title must block")
dubai_y61 = ad_post("nissan-patrol-y61-vs-y62-dubai", body="<p>The Y61 and Y63.</p>")
check(check_city.problems(dubai_y61) == [], "a Dubai post may mention the Y61/Y63")
base = "nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026"
live = (ROOT / "blog" / f"{base}.html").read_text(encoding="utf-8")
check(check_city.problems(ROOT / "blog" / f"{base}.html") == [], "baseline post fails at its baseline")
more = tmp / f"{base}.html"
more.write_text(live.replace("</article>", "<p>The Y61 too.</p></article>", 1))
check(any(MODEL in x for x in check_city.problems(more)), "a NEW mention on the baseline post must block")
check(all(v >= 1 for v in check_city.MODEL_BASELINE.values()), "empty baseline entries should be deleted")
check("Y61" in ad_city.AD_CITY_RULES and "not even in passing" in ad_city.AD_CITY_RULES,
      "the prompt does not tell the writer the Y61/Y63 rule")
asrc = (HERE / "assemble.py").read_text(encoding="utf-8")
check("skip_other_models=bool(ad_city.ad_city_for(slug))" in asrc,
      "assemble.py may put a Y61/Y63 post in an Abu Dhabi post's related reading")

# ------------------------------------------------------------------ routing
WA = ad_city.WA
page = ('<head></head><h1>Title</h1><p class="hero-lede">Lede.</p>'
        f'<a href="https://wa.me/{WA}?text={quote("Hi, I read your guide", safe="")}">x</a>'
        f'<a href="https://wa.me/{WA}">footer</a>'
        '<div class="pg-ask" data-fs="1">\n  <a data-cta-label="pg-hero-wa" href="#">d</a>\n</div>')
once = ad_city.apply_routing(page)
check(ad_city.apply_routing(once) == once, "apply_routing is not idempotent")
for label in ("pg-ad-wa", "pg-ad-wa-ar", "pg-ad-call"):
    check(f'data-cta-label="{label}"' in once, f"routing: no {label}")
check("pg-hero-wa" not in once, "routing kept the Dubai first-screen ask")
texts = [unquote(m) for m in re.findall(rf'href="https://wa\.me/{WA}\?text=([^"]*)"', once)]
check(len(texts) == 4 and all(t.startswith("Mussafah:") for t in texts),
      f"routing: a WhatsApp pre-fill does not start with Mussafah: {texts}")
check(any("أبوظبي" in t for t in texts), "routing: Arabic pre-fill missing")
check(once.index(ad_city.MARKER) > once.index('class="hero-lede"'), "ask is not under the H1/lede")

shipped = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
                         text=True).stdout.split()
ad_pages = sorted(set(f for f in shipped if ad_city.is_ad_page(f)) | {ad_city.HUB})
for f in ad_pages:
    html = (ROOT / f).read_text(encoding="utf-8")
    check(ad_city.apply_routing(html) == html, f"{f}: Mussafah routing not applied")
    check(html.count('class="pg-ad"') == 1, f"{f}: expected exactly one Abu Dhabi ask")
    check("closest('[data-cta-label]')" in html, f"{f}: tracker does not read data-cta-label")

# ------------------------------------------------------------------ hub
hub = (ROOT / ad_city.HUB).read_text(encoding="utf-8")
title = re.search(r"<title>(.*?)</title>", hub).group(1)
h1 = re.sub(r"<[^>]+>", " ", re.search(r"<h1>(.*?)</h1>", hub, re.S).group(1))
check(title.startswith("Nissan Patrol Y62 Abu Dhabi"), f"hub title: {title}")
check(re.sub(r"\s+", " ", h1).strip().startswith("Nissan Patrol Y62"), f"hub H1: {h1}")
# The page's own copy: hero + body. The shared CTA banner and footer are site chrome.
main = hub[hub.index('<section class="hero">'):hub.index('<section class="cta-banner">')]
visible = re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", main, flags=re.S))
check(visible.count("work is carried out in Mussafah") == 2, "hub: Mussafah statement (lede + booking)")
check(visible.count("Khalifa City") == 1, "hub: areas served should be listed once")
for banned in ("Top Challenger", "topchallenger", "AED", "dirham", "opening hours",
               "streetAddress", "our workshop", "visit us"):
    check(banned.lower() not in hub.lower(), f"hub carries {banned!r}")
check(not re.search(r"\d", visible.replace("Y62", "").replace("VK56VD", "").replace("JR710E", "")
                    .replace("P0300", "").replace("+971 58 514 3634", "")
                    .replace("01 · Booking", "").replace("4x4", "").replace("V8", "")),
      "hub: a figure in visible copy (no figures, prices or intervals)")
faq = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', hub, re.S)]
faq = [b for b in faq if b.get("@type") == "FAQPage"]
check(len(faq) == 1, "hub: no FAQPage schema")
if faq:
    qs = " ".join(q["name"].lower() for q in faq[0]["mainEntity"])
    for need in ("maintenance cost", "reliable for long-term ownership", "expensive to maintain"):
        check(need in qs, f"hub FAQ: no question on {need!r}")
    for q in faq[0]["mainEntity"]:
        check(q["acceptedAnswer"]["text"] in hub.replace("\n", " ") or
              q["acceptedAnswer"]["text"] in re.sub(r"\s+", " ", visible),
              f"hub FAQ answer not visible on the page: {q['name']}")

# ------------------------------------------------------------------ generator
gsrc = (HERE / "generate.py").read_text(encoding="utf-8")
check("city_block(slug)" in gsrc, "generate.py does not add the city block")
check(ad_city.ad_city_rules_for("nissan-patrol-brake-problems") is None, "city rules on a Dubai slug")
rules = ad_city.ad_city_rules_for("nissan-patrol-running-costs-abu-dhabi") or ""
check("carried out in" in rules and "Mussafah" in rules and "Top Challenger" not in rules,
      "AD city rules: Mussafah line or partner name")

# ------------------------------------------------------------------ picker + requeue
rp = (HERE / "run_pipeline.py").read_text(encoding="utf-8")
check('QUEUE_ORDER = "queue_position.asc.nullslast,created_at.asc"' in rp, "picker order")
check(rp.count('"order": QUEUE_ORDER') == 2, "both the run and the dry run must use QUEUE_ORDER")
check('"order": "created_at.asc", "limit": "1"' not in rp, "picker still oldest-first only")
check("check_city.py" in rp, "check_city is not a gate")
sl = (HERE / "supabase_log.py").read_text(encoding="utf-8")
check('"queue_position": None' in sl, "requeue_to_back must clear queue_position")

# ---------------------------------------------- city gate retry + mix warning
import run_pipeline as rp  # noqa: E402
check(rp.CITY_STAGE in rp.RETRYABLE and rp.CLAIMS_STAGE in rp.RETRYABLE, "city gate not retryable")
check(any(d == rp.CITY_STAGE for _, d, _ in rp.gate_stages("x-abu-dhabi")), "city gate not in the gates")
_calls = {"regen": []}
_gates = [rp.CITY_STAGE, None]
_saved = rp.run_gates, rp.city_flagged
rp.run_gates = lambda slug: _gates.pop(0)
rp.city_flagged = lambda slug: ["Unlike the Y63, it is simple."]
try:
    res = rp.gate_with_one_retry("x-abu-dhabi", lambda env: _calls["regen"].append(env["GATE_FEEDBACK"]))
finally:
    rp.run_gates, rp.city_flagged = _saved
check(res is None and _calls["regen"] == ["Unlike the Y63, it is simple."],
      f"city block: one regenerate fed the Y63 sentence ({res}, {_calls})")

ad3 = seed.AD_KEYWORDS[:3]
check(ad_city.ad_mix_warning(ad3 + ["nissan patrol fuel smell"]) is None, "warned with 3 AD pending")
w = ad_city.ad_mix_warning(ad3[:2] + ["nissan patrol fuel smell"])
check(w and "only 2 Abu Dhabi" in w, f"no warning with 2 AD pending: {w}")
check(ad_city.ad_mix_warning([]) is not None, "no warning on an empty queue")
rp_src = (HERE / "run_pipeline.py").read_text(encoding="utf-8")
check("warn_ad_mix(pending_rows)" in rp_src and "warn_ad_mix(pending)" in rp_src,
      "the mix warning is not called by the run and the dry run")

# ------------------------------------------------------------------ seed
check("nissan patrol running costs abu dhabi" not in seed.AD_KEYWORDS
      and "nissan patrol running costs abu dhabi" in seed.RETIRE_UNQUEUED, "running costs not retired")
check("nissan patrol exhaust smoke" in seed.RETIRE, "exhaust smoke not retired")
check(seed.problems([]) == [], f"seed keywords break a rule: {seed.problems([])}")
check(seed.problems(["y62 limp mode abu dhabi"]) == [], "seed vs TC overlap check")
check(seed.problems(["y62 rust from humidity uae"]) != [], "overlap check never fires")
rows = [{"keyword": k} for k in ["a", "b"] + seed.AD_KEYWORDS[:3] + ["c"]]
got = ["AD" if ad_city.ad_city_for(r["keyword"]) else "x" for r in seed.order(rows)]
check(got == ["AD", "AD", "x", "AD", "x", "x"], f"seed order pattern: {got}")

if fails:
    print(f"[!] Abu Dhabi regression FAILED - {len(fails)} problem(s):")
    for f in fails:
        print("    -", f)
    sys.exit(1)
print(f"[+] Abu Dhabi regression passed: city gate, Mussafah routing on {len(ad_pages)} page(s), "
      f"hub copy and FAQ, queue order and seed rules.")
