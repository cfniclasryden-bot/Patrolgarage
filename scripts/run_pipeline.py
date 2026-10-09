#!/usr/bin/env python3
"""Daily autonomous pipeline runner."""

import csv
import subprocess
import sys
import re
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

import supabase_log
from supabase_log import log_article, log_run, sync_queue

CSV_FILE = ROOT / "keywords.csv"

# Exit code for a run that found nothing to publish. Distinct from 1 (a stage
# failed) and 2 (sync_to_origin refused to run), so the log says which it was.
IDLE_EXIT = 3

# Queue order (2026-10-09). An explicit queue_position wins, lowest first; rows
# without one (refill inserts, requeued rows) follow, oldest first. Before this
# the picker read created_at only and every queue_position was empty. The Abu
# Dhabi mix (2 of every 3 runs) is written into queue_position, not computed
# here, so the order is the one the table shows.
QUEUE_ORDER = "queue_position.asc.nullslast,created_at.asc"

# The one gate that earns a regenerate. See gate_with_one_retry().
CLAIMS_STAGE = "pre-publish: no figure attributed to an authority we cannot produce"
# The Abu Dhabi gate (check_city.py) earns the same one regenerate since
# 2026-10-09: a Y61/Y63 mention is wording, and a draft told which sentences to
# drop usually drops them. It shares the ONE retry with check_claims.
CITY_STAGE = "pre-publish: an Abu Dhabi post names Abu Dhabi, and no Y61/Y63"
RETRYABLE = (CLAIMS_STAGE, CITY_STAGE)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
log_file = LOG_DIR / f"run_{today}.log"

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def run(cmd, desc, show_stdout_on_fail=False, env=None):
    """Run one stage. False if it failed.

    `show_stdout_on_fail` is for the guards, which report on STDOUT and say
    nothing on stderr; without it a blocked publish logs an empty reason.
    `env` adds variables for this stage only (the claims retry uses it).
    """
    log(f"→ {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                            env={**os.environ, **env} if env else None)
    # The humour pass never fails the run, so surface its verdict even on success.
    for line in (result.stdout or "").splitlines():
        if line.startswith("[humour_pass]"):
            log(f"  {line}")
    if result.returncode != 0:
        log(f"[!] FAILED: {desc}")
        if show_stdout_on_fail and result.stdout:
            for line in result.stdout.splitlines():
                log("    " + line)
        if result.stderr:
            log(f"    stderr: {result.stderr[:500]}")
        return False
    # --repair exits 0 but says so loudly; that line is the signal to look.
    if "ALT REPAIRED" in (result.stdout or ""):
        log("  [~] check_alt reset the hero alt to the neutral one")
    log(f"  ✓ {desc} done")
    return True


# ------------------------------------------------------------ pre-publish gates
#
# Ported from topchallenger-site on 2026-10-05, same rules, same order, same
# contract: BLOCKING, scoped to THIS post's file, run after the hero image and
# before publish. This pipeline had no content guard at all before then. Run
# across the 72 pages already live, check_claims fired on 26 and
# check_model_years on 15, and 11 pages carry a literal [NEEDS_SOURCE] in visible
# copy. Those pages are not touched here; the gates only stop new ones.
#
# What each one adapts for this site is in its own docstring: check_schema
# fails a premises claim (address, geo, opening hours) instead of a missing
# address, check_prose and check_schema also block the partner workshop's
# name, and check_alt's neutral alt names nobody.

def gate_stages(slug):
    post = f"blog/{slug}.html"
    return [
        (["python3", "scripts/check_prose.py", post],
         "pre-publish: no editorial placeholders", True),
        (["python3", "scripts/check_schema.py", post],
         "pre-publish: JSON-LD parses, no placeholders, no premises", True),
        (["python3", "scripts/check_model_years.py", post],
         "pre-publish: no invented model-year or generation split", True),
        (["python3", "scripts/check_claims.py", post], CLAIMS_STAGE, True),
        # Abu Dhabi posts (2026-10-09, ported from topchallenger-site): the city
        # in title, H1, meta description and opening. A no-op for every other slug.
        (["python3", "scripts/check_city.py", post], CITY_STAGE, True),
        # Repairs rather than refuses, as on topchallenger: a wrong alt has a
        # safe alternative, so it never costs the day's post.
        (["python3", "scripts/check_alt.py", "--repair", post],
         "pre-publish: hero alt asserts nothing the picture cannot support", True),
    ]


def run_gates(slug):
    """Every guard in order. The description of the first that blocked, or None."""
    for cmd, desc, show in gate_stages(slug):
        if not run(cmd, desc, show_stdout_on_fail=show):
            return desc
    return None


def claims_flagged(slug):
    """The sentences check_claims blocked on, for the regenerate prompt."""
    import check_claims
    items = check_claims.review_items(ROOT / "blog" / f"{slug}.html")
    return list(dict.fromkeys(sent for _, _, _, sent in items))


def warn_ad_mix(pending_rows):
    """Log a warning when the Abu Dhabi rows are running out. Never fatal."""
    try:
        import ad_city
        msg = ad_city.ad_mix_warning([r.get("keyword", "") for r in pending_rows])
        if msg:
            log(msg)
    except Exception as e:
        log(f"[warn] Abu Dhabi mix check skipped: {e}")


def city_flagged(slug):
    """The Y61/Y63 sentences check_city blocked on, for the regenerate prompt."""
    import check_city
    return list(dict.fromkeys(check_city.model_mentions(ROOT / "blog" / f"{slug}.html")))


def gate_with_one_retry(slug, regenerate):
    """Run the gates; on a check_claims block, regenerate ONCE and gate again.

    `regenerate(env)` re-runs the content stages with GATE_FEEDBACK in env and
    returns the description of a stage that failed, or None.

    The retry is not a softening. The regenerated post goes through every gate
    from the top, a second block of any kind fails the run, and there is no
    second retry. Only check_claims earns one, because its failures are about
    wording ("the owner's manual says...") and a draft told which sentences to
    drop usually drops them. Same logic as topchallenger-site.
    """
    failed = run_gates(slug)
    if failed not in RETRYABLE:
        return failed
    flagged = claims_flagged(slug) if failed == CLAIMS_STAGE else city_flagged(slug)
    log(f"[retry] {failed} blocked {len(flagged)} sentence(s); regenerating once "
        f"with them fed back as claims to remove")
    broke = regenerate({"GATE_FEEDBACK": "\n".join(flagged)})
    if broke:
        return f"{broke} (during the one claims retry)"
    failed = run_gates(slug)
    if failed:
        return f"{failed} (after the one claims retry)"
    log("[retry] the regenerated post passed every gate")
    return None


def requeue_if_stuck(article_id, keyword, failed_at):
    """After REQUEUE_AFTER consecutive failed runs, move the keyword to the back.

    Called after this run's failure is logged, so the streak includes it.
    Best-effort: the run exits 1 either way.
    """
    streak = supabase_log.failure_streak(keyword)
    if streak is None:
        log("[queue] could not read the failure streak; keyword left in place")
        return
    log(f"[queue] '{keyword}' has now failed {streak} consecutive run(s)")
    if streak < supabase_log.REQUEUE_AFTER:
        return
    reason = (f"Moved to the back of the queue {datetime.utcnow():%Y-%m-%d}: "
              f"{streak} consecutive failed runs, the last at: {failed_at}")
    if supabase_log.requeue_to_back(article_id, keyword, reason):
        log(f"[queue] MOVED TO THE BACK: {reason}")
    else:
        log("[queue] [!] tried to move it to the back of the queue and could not; "
            "the next run will pick the same keyword")

def run_refresh_mode(keyword, slug):
    """Re-run pipeline stages for an existing article. Always honors the existing
    slug, even if the keyword would slugify differently. This ensures we update
    the original URL rather than creating a new one."""
    log(f"=== REFRESH MODE: {keyword} ({slug}) ===")

    # Helper: slugify keyword like the other scripts do
    import re
    def slugify(text):
        text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
        return re.sub(r"[\s_-]+", "-", text).strip("-")

    keyword_slug = slugify(keyword)
    slug_differs = keyword_slug != slug
    if slug_differs:
        log(f"  NOTE: keyword slugifies to '{keyword_slug}' but article slug is '{slug}' — will rename outputs")

    # Stage 1: research
    if not run(["python3", "scripts/research.py", keyword], f"research: {keyword}"):
        log(f"=== REFRESH FAILED at: research ==="); return 1

    # Stage 2: generate draft
    if not run(["python3", "scripts/generate.py", keyword], f"regenerate draft"):
        log(f"=== REFRESH FAILED at: regenerate draft ==="); return 1

    # If slug differs, rename the new draft (and its research) to the canonical slug
    if slug_differs:
        for subdir, ext in [("drafts", ".html"), ("research", ".json")]:
            src = ROOT / subdir / f"{keyword_slug}{ext}"
            dst = ROOT / subdir / f"{slug}{ext}"
            if src.exists():
                src.replace(dst)  # overwrites if exists
                log(f"  Renamed {subdir}/{keyword_slug}{ext} → {slug}{ext}")

    # Stage 2b: humour pass on the regenerated draft (never fatal, see humour_pass.py)
    run(["python3", "scripts/humour_pass.py", slug], "humour pass")

    # Stage 3: assemble — pass the ORIGINAL keyword that maps to the article's slug.
    # We need a keyword that slugifies to `slug`. Easiest: use slug-with-spaces as keyword.
    canonical_keyword_for_slug = slug.replace("-", " ")
    if not run(["python3", "scripts/assemble.py", canonical_keyword_for_slug], f"assemble final HTML"):
        log(f"=== REFRESH FAILED at: assemble final HTML ==="); return 1

    # Stage 4: image_gen (uses slug directly)
    if not run(["python3", "scripts/image_gen.py", slug], f"regenerate hero image"):
        log(f"=== REFRESH FAILED at: regenerate hero image ==="); return 1

    # Stage 4b: the same blocking gates as a daily post. A refresh publishes
    # over a live URL, so it is held to the same rules.
    def regenerate(env):
        if not run(["python3", "scripts/generate.py", keyword],
                   "regenerate draft (claims retry)", env=env):
            return "regenerate draft (claims retry)"
        if slug_differs:
            for subdir, ext in [("drafts", ".html"), ("research", ".json")]:
                src = ROOT / subdir / f"{keyword_slug}{ext}"
                if src.exists():
                    src.replace(ROOT / subdir / f"{slug}{ext}")
        run(["python3", "scripts/humour_pass.py", slug], "humour pass (claims retry)")
        if not run(["python3", "scripts/assemble.py", canonical_keyword_for_slug],
                   "re-assemble final HTML (claims retry)"):
            return "re-assemble final HTML (claims retry)"
        return None
    failed_at = gate_with_one_retry(slug, regenerate)
    if failed_at:
        log(f"=== REFRESH FAILED at: {failed_at} ==="); return 1

    # Stage 5: publish (also uses slug-derived keyword)
    if not run(["python3", "scripts/publish.py", canonical_keyword_for_slug], f"publish + sitemap + deploy"):
        log(f"=== REFRESH FAILED at: publish ==="); return 1

    # Read updated HTML and push to Supabase
    try:
        article_path = ROOT / "blog" / f"{slug}.html"
        if article_path.exists():
            content_html = article_path.read_text()
            title_match = re.search(r"<title>(.*?)</title>", content_html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else None

            # Update the article row with new content
            import requests
            SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
            SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
            if SUPABASE_URL and SUPABASE_KEY:
                H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/articles",
                    headers=H,
                    params={"slug": f"eq.{slug}"},
                    json={"content_html": content_html, "title": title},
                )
                log(f"Updated content_html in Supabase for {slug}")
    except Exception as e:
        log(f"[warn] content_html upload failed: {e}")

    log(f"=== REFRESH COMPLETE: {keyword} ===")
    return 0


def main():
    # --dry-run: research, generate, humour, assemble, image and every gate, then
    # stop. No sync, no queue refill, no Supabase write, no publish/commit/push/
    # deploy. It still writes the generated files to this tree, so run it in a
    # scratch copy of the repo, never in a working tree you care about.
    dry_run = "--dry-run" in sys.argv[1:]
    argv = [a for a in sys.argv[1:] if a != "--dry-run"]

    # Check for refresh mode
    if not dry_run and len(argv) >= 3 and argv[0] == "--refresh":
        return run_refresh_mode(argv[1], argv[2])

    log(f"=== PIPELINE RUN START ===" + (" (DRY RUN)" if dry_run else ""))
    if dry_run:
        return dry_run_main()

    # STEP ZERO: make the tree equal origin BEFORE generating anything.
    #
    # Added 2026-09-18. The container is built with COPY . ., so without this it
    # runs against whatever the repo looked like at the last `railway up` — and
    # on 2026-09-18 that snapshot was two months and 53 commits behind origin.
    # Generating a post on top of a stale tree and deploying it is how this site
    # reverted live content more than once.
    #
    # FATAL IN THE CLOUD WITH NO GH_TOKEN. sync_to_origin() raises SystemExit(2)
    # rather than falling through, so the run stops here: nothing is generated,
    # nothing is committed, nothing is deployed, and the live site is untouched.
    # That is the intended failure mode. Until GH_TOKEN and GH_REPO are set on
    # the Railway service there will be no daily post, and that is the correct
    # trade — a skipped post is recoverable, a stale-tree deploy is not.
    sys.path.insert(0, str(ROOT / "scripts"))
    import publish as _publish
    _publish.sync_to_origin()

    # Get next pending keyword from Supabase (source of truth)
    import requests as _req
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")

    if not (SUPABASE_URL and SUPABASE_KEY):
        log("FATAL: missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1

    SH = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

    # Get site_id from domain
    r = _req.get(f"{SUPABASE_URL}/rest/v1/sites", headers=SH,
                 params={"domain": f"eq.{SITE_DOMAIN}", "select": "id"})
    site_rows = r.json()
    if not site_rows:
        log(f"FATAL: site {SITE_DOMAIN} not found in sites table")
        return 1
    site_id = site_rows[0]["id"]

    # Auto-replenish queue if running low. Supabase is the queue; keywords.csv is
    # only a mirror of it and is not an input to anything (2026-09-29).
    r = _req.get(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
                 params={"site_id": f"eq.{site_id}", "status": "eq.pending", "select": "id,keyword"})
    pending_rows = r.json()
    pending_count = len(pending_rows)
    log(f"Pending in queue: {pending_count}")
    warn_ad_mix(pending_rows)

    if pending_count < 5:
        log(f"Queue low. Auto-generating more keywords...")
        kw_result = subprocess.run(
            ["python3", "scripts/keyword_generator.py"],
            capture_output=True, text=True, cwd=ROOT
        )
        # Log the generator's own report, always. "exited 0" is not "added
        # anything": the generator also exits 0 when every candidate is already a
        # Supabase row. This used to print "✓ Keyword queue replenished" on any
        # exit 0, the same misleading line topchallenger replaced on 2026-09-15.
        for line in kw_result.stdout.splitlines():
            log("    [keyword_generator] " + line)
        for line in kw_result.stderr.splitlines()[-20:]:
            log("    [keyword_generator stderr] " + line)
        if kw_result.returncode == 0:
            log("  keyword_generator exited 0 (see its output above for what it added)")
        else:
            log(f"  [!] keyword_generator FAILED (exit {kw_result.returncode})")
        r = _req.get(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
                     params={"site_id": f"eq.{site_id}", "status": "eq.pending", "select": "id"})
        log(f"Pending in queue after replenishment: {len(r.json())} (was {pending_count})")

    # Fetch the next pending article from Supabase, in QUEUE_ORDER
    r = _req.get(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
                 params={"site_id": f"eq.{site_id}", "status": "eq.pending",
                         "select": "id,keyword,slug", "order": QUEUE_ORDER, "limit": "1"})
    pending_articles = r.json()
    if not pending_articles:
        log("No pending keywords. Pipeline idle.")
        # A scheduled run that publishes nothing exits NON-ZERO (2026-09-29), so
        # Railway marks it CRASHED and emails, instead of the run reading as a
        # healthy exit 0. Expect Railway to create a `redeploy` deployment on the
        # next cron tick after a CRASHED run; that is Railway, not a second fault.
        log(f"[!] SCHEDULED RUN PUBLISHED NOTHING: the queue is empty. Exit {IDLE_EXIT} "
            "so Railway flags it.")
        return IDLE_EXIT

    article_row = pending_articles[0]
    keyword = article_row["keyword"]
    slug = article_row.get("slug") or slugify(keyword)
    article_id = article_row["id"]
    log(f"Target keyword: {keyword}")
    log(f"Slug: {slug}")
    log(f"Article ID: {article_id}")
    log(f"Target keyword: {keyword}")
    log(f"Slug: {slug}")

    # (command, description, optional). Optional stages are cosmetic: if one dies the
    # article still ships. The humour pass must never cost us a day's post.
    failed_at = run_stages(keyword, slug)
    if failed_at:
        log(f"=== PIPELINE FAILED at: {failed_at} ===")
        log_run(keyword=keyword, status="failed", error_message=f"Failed at: {failed_at}")
        requeue_if_stuck(article_id, keyword, failed_at)
        return 1

    # Mark this article as published in Supabase (source of truth)
    _req.patch(f"{SUPABASE_URL}/rest/v1/articles", headers=SH,
               params={"id": f"eq.{article_id}"},
               json={"status": "published",
                     "published_at": datetime.utcnow().isoformat() + "Z",
                     "slug": slug})
    log(f"Article marked published in Supabase: {article_id}")

    site_domain = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")
    article_url = f"https://{site_domain}/blog/{slug}.html"

    # Read published HTML to upload to Supabase (non-fatal if it fails)
    content_html = None
    title = None
    try:
        import re
        article_path = Path(__file__).resolve().parent.parent / "blog" / f"{slug}.html"
        if article_path.exists():
            content_html = article_path.read_text()
            title_match = re.search(r"<title>(.*?)</title>", content_html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
    except Exception as e:
        log(f"[warn] could not read published HTML for upload: {e}")

    log_article(keyword=keyword, slug=slug, url=article_url, status="published",
                content_html=content_html, title=title)
    log_run(keyword=keyword, status="success")

    log(f"=== PIPELINE COMPLETE: {keyword} ===")
    return 0

def content_stages(keyword, slug):
    # (command, description, optional). Optional stages are cosmetic: if one dies the
    # article still ships. The humour pass must never cost us a day's post.
    return [
        (["python3", "scripts/research.py", keyword], f"research: {keyword}", False),
        (["python3", "scripts/generate.py", slug], f"generate draft", False),
        (["python3", "scripts/humour_pass.py", slug], f"humour pass", True),
        (["python3", "scripts/assemble.py", slug], f"assemble final HTML", False),
        (["python3", "scripts/image_gen.py", slug], f"generate hero image", False),
    ]


def run_stages(keyword, slug, dry_run=False):
    """content -> gates (one claims retry) -> publish. Description of a failed
    stage, or None. `dry_run` stops after the gates."""
    for cmd, desc, optional in content_stages(keyword, slug):
        if not run(cmd, desc):
            if optional:
                log(f"[i] optional stage failed, continuing without it: {desc}")
                continue
            return desc

    def regenerate(env):
        # research.py's output is still on disk, and the hero image is kept: the
        # re-assembled post points at the same images/blog/<slug>.jpg.
        for cmd, desc, optional in content_stages(keyword, slug)[1:4]:
            if not run(cmd, desc + " (claims retry)", env=env) and not optional:
                return desc + " (claims retry)"
        return None

    failed = gate_with_one_retry(slug, regenerate)
    if failed:
        return failed

    if dry_run:
        log("[dry-run] every gate passed — publish, commit, push and deploy SKIPPED")
        return None

    if not run(["python3", "scripts/publish.py", slug], "publish + sitemap + deploy"):
        return "publish + sitemap + deploy"
    return None


def dry_run_main():
    """Read the queue head and run every stage up to and including the gates.

    Read-only against Supabase: nothing is written, and the refill is NOT run
    even when the queue is low, because it inserts rows and spends DataForSEO
    credit. A block exits 1 like a real run, without logging the failure.
    """
    import requests as _req
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    domain = os.environ.get("SITE_DOMAIN", "patrolgarage.ae")
    if not (url and key):
        log("FATAL: missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return 1
    sh = {"apikey": key, "Authorization": f"Bearer {key}"}
    site_id = _req.get(f"{url}/rest/v1/sites", headers=sh,
                       params={"domain": f"eq.{domain}", "select": "id"}).json()[0]["id"]
    pending = _req.get(f"{url}/rest/v1/articles", headers=sh,
                       params={"site_id": f"eq.{site_id}", "status": "eq.pending",
                               "select": "id,keyword,slug", "order": QUEUE_ORDER}).json()
    warn_ad_mix(pending)
    log(f"[dry-run] pending in queue: {len(pending)}"
        + ("  (a real run would refill first: below 5)" if len(pending) < 5 else ""))
    if not pending:
        log("[dry-run] queue empty — a real run would exit 3")
        return IDLE_EXIT
    row = pending[0]
    keyword, slug = row["keyword"], row.get("slug") or slugify(row["keyword"])
    log(f"[dry-run] target keyword: {keyword}  (slug {slug})")
    failed_at = run_stages(keyword, slug, dry_run=True)
    if failed_at:
        log(f"=== DRY RUN BLOCKED at: {failed_at} ===")
        return 1
    log(f"=== DRY RUN COMPLETE: {keyword} — would publish ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
