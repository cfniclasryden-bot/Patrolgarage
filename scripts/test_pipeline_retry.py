#!/usr/bin/env python3
"""Regression test for the pre-publish gates, the claims retry and the requeue.

    python3 scripts/test_pipeline_retry.py

Exit 0 = all cases behave. Exit 1 = at least one does not. No network, no
model call, no Supabase: every stage and every Supabase call is stubbed.

Ported from topchallenger-site on 2026-10-05 alongside the logic it tests:
- check_claims, and only check_claims, earns ONE regenerate, with the flagged
  sentences handed to generate.py in GATE_FEEDBACK.
- The regenerated post goes through every gate again; a second block of any
  kind fails the run, and there is never a second retry.
- Two consecutive failed runs on one keyword move it to the back of the queue.
Plus what is specific to this site: the gates sit between the hero image and
publish, the adapted schema/prose/alt rules fire on the right things, and the
neutral alt never names the partner workshop.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-only-no-call-is-made")

import supabase_log                                   # noqa: E402
import run_pipeline as rp                             # noqa: E402
import generate                                       # noqa: E402
import check_alt                                      # noqa: E402
import check_prose                                    # noqa: E402
import check_schema                                   # noqa: E402

failures = []


def check(label, ok, detail=""):
    if ok:
        print(f"  ok       {label}")
    else:
        failures.append(f"{label}{': ' + detail if detail else ''}")


_tmp = tempfile.TemporaryDirectory()
TMP = Path(_tmp.name)
rp.log_file = TMP / "run.log"          # keep the runner's log out of logs/


# ------------------------------------------------------------ streak counting
S = supabase_log.streak_from_runs
check("streak: two failures", S([{"status": "failed"}, {"status": "failed"}]) == 2)
check("streak: success ends it",
      S([{"status": "failed"}, {"status": "success"}, {"status": "failed"}]) == 1)
check("streak: requeued ends it",
      S([{"status": "failed"}, {"status": "requeued"}, {"status": "failed"}]) == 1)
check("streak: 'started' neither counts nor ends it",
      S([{"status": "failed"}, {"status": "started"}, {"status": "failed"}]) == 2)


# --------------------------------------------------------------- retry prompt
os.environ.pop("GATE_FEEDBACK", None)
check("retry block empty without GATE_FEEDBACK", generate.retry_block() == "")
os.environ["GATE_FEEDBACK"] = "First flagged sentence.\nSecond one."
rb = generate.retry_block()
check("retry block lists every flagged sentence",
      '"First flagged sentence."' in rb and '"Second one."' in rb, rb[:200])
os.environ.pop("GATE_FEEDBACK", None)


# --------------------------------------------------------- retry control flow
CLAIMS = rp.CLAIMS_STAGE
MODEL_YEARS = "pre-publish: no invented model-year or generation split"


def simulate(gate_results, regen_ok=True):
    calls = {"gates": 0, "regen": []}
    gates = list(gate_results)

    def fake_gates(slug):
        calls["gates"] += 1
        return gates.pop(0) if gates else None

    def regenerate(env):
        calls["regen"].append(env.get("GATE_FEEDBACK", ""))
        return None if regen_ok else "generate draft (claims retry)"

    saved = rp.run_gates, rp.claims_flagged
    rp.run_gates = fake_gates
    rp.claims_flagged = lambda slug: ["Nissan's published interval is 10,000 km."]
    try:
        return rp.gate_with_one_retry("nissan-patrol-test", regenerate), calls
    finally:
        rp.run_gates, rp.claims_flagged = saved


r, c = simulate([None])
check("clean post: no retry", r is None and not c["regen"])
r, c = simulate([CLAIMS, None])
check("claims block then clean: one regenerate, passes",
      r is None and len(c["regen"]) == 1 and c["gates"] == 2, f"{r} {c}")
check("claims retry is fed the flagged sentences",
      c["regen"] and "published interval" in c["regen"][0])
r, c = simulate([CLAIMS, CLAIMS])
check("claims block twice: hard block, no second retry",
      r == f"{CLAIMS} (after the one claims retry)" and len(c["regen"]) == 1, f"{r} {c}")
r, c = simulate([CLAIMS, MODEL_YEARS])
check("claims retry then a different gate blocks: hard block",
      r == f"{MODEL_YEARS} (after the one claims retry)", r)
r, c = simulate([MODEL_YEARS])
check("non-claims block: no retry at all", r == MODEL_YEARS and not c["regen"])
r, c = simulate([CLAIMS], regen_ok=False)
check("regenerate itself fails: run fails, gates not re-run",
      r == "generate draft (claims retry) (during the one claims retry)" and c["gates"] == 1)


# ------------------------------------------- stage order: gates before publish
order = []
saved = rp.run, rp.gate_with_one_retry
rp.run = lambda cmd, desc, show_stdout_on_fail=False, env=None: order.append(desc) or True
rp.gate_with_one_retry = lambda slug, regen: order.append("GATES") or None
try:
    rp.run_stages("nissan patrol test", "nissan-patrol-test", dry_run=False)
finally:
    rp.run, rp.gate_with_one_retry = saved
check("gates run after the hero image and before publish",
      order.index("GATES") == order.index("generate hero image") + 1
      and order[-1] == "publish + sitemap + deploy", str(order))

order.clear()
rp.run = lambda cmd, desc, show_stdout_on_fail=False, env=None: order.append(desc) or True
rp.gate_with_one_retry = lambda slug, regen: None
try:
    rp.run_stages("nissan patrol test", "nissan-patrol-test", dry_run=True)
finally:
    rp.run, rp.gate_with_one_retry = saved
check("dry run never reaches publish", not any("publish" in d for d in order), str(order))


# ----------------------------------------------------------------- requeue
# ------------------------------------------- Round 6 reaches the retry (10-09)
# CROWD / FIRST_HAND hits come from check_claims, so the real claims_flagged()
# must return them and the regenerate prompt must carry them, worded for what
# they are (not as an authority claim). Real functions, a real page on disk.
_r6 = tempfile.TemporaryDirectory()
(Path(_r6.name) / "blog").mkdir()
_crowd = ("December is busy because the festival runs then, and hundreds of "
          "Patrols make the same drive in the same week.")
_first = ("Cars at higher mileage that have had the fluid changed late are the "
          "ones we see with early wear in the valve body.")
(Path(_r6.name) / "blog" / "r6-case.html").write_text(
    f"<html><body><article><p>{_crowd}</p>"
    f"<p>{_first}</p><p>Check the coolant first.</p></article></body></html>",
    encoding="utf-8")
_saved_root = rp.ROOT
rp.ROOT = Path(_r6.name)
try:
    _flagged = rp.claims_flagged("r6-case")
finally:
    rp.ROOT = _saved_root
check("Round 6: claims_flagged returns the crowd and first-hand sentences",
      _flagged == [_crowd, _first], str(_flagged))
os.environ["GATE_FEEDBACK"] = "\n".join(_flagged)
try:
    _prompt = generate.retry_block()
finally:
    del os.environ["GATE_FEEDBACK"]
check("Round 6: the regenerate prompt carries both sentences",
      _crowd in _prompt and _first in _prompt)
check("Round 6: the regenerate prompt names crowd counts and first-hand observations",
      "crowd or volume count" in _prompt and "first-hand workshop observation" in _prompt)


def requeue_case(streak):
    moved = []
    saved = supabase_log.failure_streak, supabase_log.requeue_to_back
    supabase_log.failure_streak = lambda kw: streak
    supabase_log.requeue_to_back = lambda aid, kw, reason: moved.append(reason) or True
    try:
        rp.requeue_if_stuck("article-id", "nissan patrol test", "some gate")
    finally:
        supabase_log.failure_streak, supabase_log.requeue_to_back = saved
    return moved

check("requeue: 1 failure stays put", requeue_case(1) == [])
check("requeue: 2 consecutive failures move to the back", len(requeue_case(2)) == 1)


# ------------------------------------------------- this site's adapted rules
def page(body="", ld=None):
    f = TMP / "case.html"
    blocks = "".join(f'<script type="application/ld+json">{x}</script>' for x in (ld or []))
    f.write_text(f"<html><head>{blocks}</head><body>{body}</body></html>", encoding="utf-8")
    return f

ok_org = ('{"@context":"https://schema.org","@type":"AutoRepair","name":"Patrol Garage",'
          '"areaServed":"AE","contactPoint":{"@type":"ContactPoint","hoursAvailable":'
          '{"@type":"OpeningHoursSpecification","opens":"09:00"}}}')
check("schema: AutoRepair with no premises properties passes (the 89a64ee shape)",
      check_schema.check_file(page(ld=[ok_org])) == [])
check("schema: an address is a premises claim",
      check_schema.check_file(page(ld=['{"@type":"AutoRepair","address":{"@type":"PostalAddress"}}'])) != [])
check("schema: geo is a premises claim",
      check_schema.check_file(page(ld=['{"@type":"Organization","geo":{"@type":"GeoCoordinates"}}'])) != [])
check("schema: opening hours on the business is a premises claim",
      check_schema.check_file(page(ld=['{"@type":"AutoRepair","openingHoursSpecification":[]}'])) != [])
check("schema: the partner workshop named in JSON-LD fails",
      check_schema.check_file(page(ld=['{"@type":"Organization","name":"Top Challenger"}'])) != [])
check("schema: a placeholder still fails",
      check_schema.check_file(page(ld=['{"@type":"Organization","name":"TODO(name)"}'])) != [])
check("prose: the partner workshop named in visible copy fails",
      check_prose.check_file(page("<p>We send the work to Top Challenger.</p>")) != [])
check("prose: a NEEDS_SOURCE marker fails",
      check_prose.check_file(page("<p>Dealers charge more [NEEDS_SOURCE].</p>")) != [])
check("prose: ordinary copy passes",
      check_prose.check_file(page("<p>The Y62 gearbox is a seven-speed automatic.</p>")) == [])
check("alt: neutral alt names nobody and passes its own rule",
      not check_alt.offences(check_alt.NEUTRAL_ALT)
      and "challenger" not in check_alt.NEUTRAL_ALT.lower())
check("alt: the headline-style alt this site writes is repaired",
      bool(check_alt.offences("Patrol 4WD Not Engaging")))


print()
if failures:
    print(f"[!] pipeline retry regression FAILED — {len(failures)} problem(s):")
    for f in failures:
        print("    " + f)
    sys.exit(1)
print("[+] pipeline retry regression passed.")
