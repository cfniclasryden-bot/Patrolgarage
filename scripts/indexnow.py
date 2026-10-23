#!/usr/bin/env python3
"""IndexNow: tell Bing which pages a deploy changed, and only those.

    python3 scripts/indexnow.py --since <rev>         # ping pages changed since <rev> (manual deploys)
    python3 scripts/indexnow.py --commit <rev>        # ping pages changed by one commit
    python3 scripts/indexnow.py --since <rev> --dry-run   # list the URLs, send nothing
    python3 scripts/indexnow.py --check-key           # is the live key file correct?

publish.py calls deploy_base() at the start of publish() and ping_deploy() at the
end of a successful deploy_site(), so every cron post and every scripted publish pings by itself.
A hand deploy (`vercel deploy --prod --archive=tgz`) does not; run --since with the commit that
was live before it.

WHAT COUNTS AS CHANGED
  The git diff between the commit that was LIVE before this deploy and the commit
  being deployed. The live commit comes from the latest READY production
  deployment's githubCommitSha (Vercel API, same call as check_deploy_drift.py).
  If that can't be read, the fallback is HEAD at the start of the run, which in
  the container is origin/main, which is what the cron last deployed.

  A changed .html file becomes a URL only if that URL is in the sitemap being
  deployed, so templates, drafts and stray HTML never get pinged. A deleted page
  is pinged if it was in the previous sitemap: IndexNow is also how an engine
  learns a URL is gone. Images, CSS, the sitemap itself and pipeline files are
  never pinged.

NEVER FATAL. A failed ping is logged and the publish carries on: the post is
already live, and Bing still finds it through the sitemap.

The key is public by design: it is served at KEY_LOCATION so the engine can check
the ping really comes from the site owner. Set INDEXNOW_DISABLED=1 to switch
pinging off without a code change.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent

HOST = "patrolgarage.ae"
KEY = "95a4a6f9deb8cf9a7b005b9a3692159c"
KEY_FILE = ROOT / f"{KEY}.txt"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://www.bing.com/indexnow"
CLEAN_URLS = False       # vercel.json cleanUrls: false: pages keep .html, directory indexes end in /
MAX_URLS = 10000         # IndexNow's per-request limit


def log(msg):
    print(f"[indexnow] {msg}", flush=True)


def _git(args, root=ROOT, check=True):
    r = subprocess.run(["git"] + args, cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:200]}")
    return r.stdout


# ------------------------------------------------------------------ mapping
def path_to_url(path):
    """Repo-relative file path -> public URL, or None if it is not a page."""
    p = path.replace("\\", "/").lstrip("./")
    if not p.endswith(".html"):
        return None
    if p == "index.html":
        return f"https://{HOST}/"
    if p.endswith("/index.html"):
        d = p[: -len("/index.html")]
        return f"https://{HOST}/{d}" + ("" if CLEAN_URLS else "/")
    return f"https://{HOST}/{p[:-5] if CLEAN_URLS else p}"


def sitemap_urls(xml):
    return set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml or ""))


def changed_urls(base, head="HEAD", root=ROOT):
    """URLs of pages that differ between two commits, in diff order."""
    if not base:
        return []
    out = _git(["diff", "--name-status", "-M", base, head], root=root)
    now = sitemap_urls(_git(["show", f"{head}:sitemap.xml"], root=root, check=False))
    before = sitemap_urls(_git(["show", f"{base}:sitemap.xml"], root=root, check=False))
    urls = []
    for line in out.splitlines():
        parts = line.split("\t")
        status = parts[0][:1]
        if status == "R" and len(parts) == 3:
            pairs = [(parts[1], "D"), (parts[2], "A")]
        else:
            pairs = [(parts[-1], status)]
        for path, st in pairs:
            url = path_to_url(path)
            if not url:
                continue
            if (st == "D" and url in before) or (st != "D" and url in now):
                if url not in urls:
                    urls.append(url)
    return urls


# ------------------------------------------------------------------ live commit
def _vercel_ids():
    project = os.environ.get("VERCEL_PROJECT_ID", "").strip()
    team = os.environ.get("VERCEL_ORG_ID", "").strip()
    pj = ROOT / ".vercel" / "project.json"
    if (not project or not team) and pj.exists():
        d = json.loads(pj.read_text())
        project, team = project or d.get("projectId", ""), team or d.get("orgId", "")
    return project, team


def live_commit():
    """githubCommitSha of the latest READY production deployment, or None."""
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    project, team = _vercel_ids()
    if not (token and project and team):
        return None
    url = (f"https://api.vercel.com/v6/deployments?projectId={project}&teamId={team}"
           f"&limit=1&target=production&state=READY")
    try:
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=20) as r:
            deps = json.load(r).get("deployments") or []
        sha = ((deps[0].get("meta") or {}).get("githubCommitSha") if deps else None) or None
    except Exception as e:
        log(f"live commit unreadable ({type(e).__name__}); using the run's start commit")
        return None
    if sha and _git(["cat-file", "-t", sha], check=False).strip() != "commit":
        log(f"live commit {sha[:12]} is not in this clone; using the run's start commit")
        return None
    return sha


def deploy_base():
    """Call BEFORE committing and deploying. The commit to diff the deploy against."""
    try:
        sha = live_commit()
        if sha:
            return sha
        return _git(["rev-parse", "HEAD"]).strip() or None
    except Exception as e:
        log(f"no base commit ({type(e).__name__}); this deploy will not ping")
        return None


# ------------------------------------------------------------------ ping
def ping(urls, endpoint=ENDPOINT, timeout=30):
    """Send the URLs. Returns (ok, detail). Never raises."""
    urls = [u for u in dict.fromkeys(urls) if u.startswith(f"https://{HOST}/")]
    if not urls:
        return True, "nothing changed — no ping sent"
    if os.environ.get("INDEXNOW_DISABLED", "").strip() not in ("", "0", "false"):
        return True, f"INDEXNOW_DISABLED set — {len(urls)} URL(s) not sent"
    sent, details = 0, []
    for i in range(0, len(urls), MAX_URLS):
        chunk = urls[i:i + MAX_URLS]
        body = {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": chunk}
        try:
            r = requests.post(endpoint, json=body, timeout=timeout,
                              headers={"Content-Type": "application/json; charset=utf-8"})
        except Exception as e:
            return False, f"request failed: {type(e).__name__}: {str(e)[:150]}"
        # 200 = accepted. 202 = accepted, key validation still pending (normal on
        # the first pings). Anything else is a refusal worth reading.
        if r.status_code not in (200, 202):
            return False, f"HTTP {r.status_code}: {r.text[:200].strip()}"
        sent += len(chunk)
        details.append(str(r.status_code))
    return True, f"{sent} URL(s) accepted (HTTP {', '.join(details)})"


def ping_deploy(base, head="HEAD"):
    """Call AFTER a successful deploy. Logs and never raises."""
    try:
        if not base:
            log("no base commit — skipped")
            return False
        urls = changed_urls(base, head)
        log(f"{len(urls)} changed page(s) since {base[:12]}" + (": " + ", ".join(urls[:10]) if urls else ""))
        ok, detail = ping(urls)
        log(("" if ok else "WARN: ") + detail)
        return ok
    except Exception as e:
        log(f"WARN: skipped ({type(e).__name__}: {str(e)[:150]}) — the deploy is unaffected")
        return False


def check_key():
    try:
        r = requests.get(KEY_LOCATION, timeout=20)
    except Exception as e:
        return False, f"{KEY_LOCATION}: {type(e).__name__}"
    ok = r.status_code == 200 and r.text.strip() == KEY
    return ok, f"{KEY_LOCATION}: HTTP {r.status_code}, content {'matches' if ok else 'does NOT match'} the key"


def main():
    ap = argparse.ArgumentParser(description="Ping IndexNow with pages changed between commits.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--since", help="ping pages changed between this commit and HEAD")
    g.add_argument("--commit", help="ping pages changed by this one commit")
    g.add_argument("--check-key", action="store_true", help="check the live key file")
    ap.add_argument("--dry-run", action="store_true", help="list the URLs, send nothing")
    a = ap.parse_args()
    if a.check_key:
        ok, detail = check_key()
        print(detail)
        return 0 if ok else 1
    base, head = (a.since, "HEAD") if a.since else (f"{a.commit}~1", a.commit)
    urls = changed_urls(base, head)
    print(f"{len(urls)} changed page(s):")
    for u in urls:
        print(f"  {u}")
    if a.dry_run:
        return 0
    ok, detail = ping(urls)
    print(detail)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
