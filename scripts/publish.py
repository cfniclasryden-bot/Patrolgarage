#!/usr/bin/env python3
"""publish.py — update sitemap, commit, deploy to Netlify"""

import sys
import os
import re
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"
SITEMAP = PROJECT_ROOT / "sitemap.xml"
SITE_URL = "https://patrolgarage.ae"

# Fallback hero, used when a referenced image is missing locally AND gone from live.
# This file is committed to the repo and shipped by every deploy.
FALLBACK_IMAGE = "images/nissan-patrol-y62-dubai-desert.jpg"

IMG_REF_RE = re.compile(
    r'(?:src|href|content)="([^"]*\.(?:jpg|jpeg|png|webp|avif|gif))"',
    re.IGNORECASE,
)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def update_sitemap():
    urls = [
        ("/", "1.0", "weekly"),
        ("/services.html", "0.9", "monthly"),
        ("/y62-garage-dubai.html", "0.9", "monthly"),
        ("/services/y62-major-service-dubai.html", "0.9", "monthly"),
        ("/services/y62-gearbox-transmission-dubai.html", "0.9", "monthly"),
        ("/services/nissan-patrol-v8-engine.html", "0.9", "monthly"),
        ("/about.html", "0.8", "monthly"),
        ("/contact.html", "0.9", "monthly"),
        ("/blog/", "0.8", "weekly"),
    ]
    blog_files = sorted([f for f in BLOG_DIR.glob("*.html") if f.name != "index.html"])
    for f in blog_files:
        urls.append((f"/blog/{f.name}", "0.7", "monthly"))

    # Paginated listing pages (/blog/page/2/ ...). Page count comes from the same
    # constant journal_update uses, so the two can never drift.
    import journal_update
    total_pages = max(1, -(-len(blog_files) // journal_update.PER_PAGE))
    for n in range(2, total_pages + 1):
        urls.append((f"/blog/page/{n}/", "0.5", "weekly"))

    # lastmod must be the date the page ACTUALLY changed, per URL.
    #
    # This used to stamp datetime.now() on every URL on every run, and the cron
    # runs daily — so the sitemap asserted that all ~55 pages changed that
    # morning, including posts untouched for months. A lastmod that is
    # demonstrably wrong carries no information, and Google's documented
    # response is to disregard it. Measured 2026-08-19: GSC had the sitemap as
    # downloaded ONCE (2026-05-11) and never re-fetched, still listing the 21
    # URLs it saw that day, while 31 URLs added afterwards sat at "URL is
    # unknown to Google" — including /y62-garage-dubai.html and all three
    # /services/ pages. Nothing else about the sitemap was wrong: valid XML,
    # correct host, every URL 200, zero errors, zero warnings.
    #
    # mtime is the right source because this site already treats it as content:
    # journal_update.py derives each post's displayed date AND the listing sort
    # order from it. Anything that corrupts mtime now breaks the listing and the
    # sitemap together, instead of leaving them silently disagreeing.
    def _mtime(path):
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")

    _newest = max((f.stat().st_mtime for f in blog_files), default=None)
    newest_date = (datetime.fromtimestamp(_newest).strftime("%Y-%m-%d")
                   if _newest else datetime.now().strftime("%Y-%m-%d"))

    def lastmod_for(url_path):
        # "/" is index.html; the other trailing-slash URLs (/blog/,
        # /blog/page/N/) are generated listings with no file of their own, and
        # they change exactly when the newest post does.
        if url_path == "/":
            f = PROJECT_ROOT / "index.html"
        elif url_path.endswith("/"):
            return newest_date
        else:
            f = PROJECT_ROOT / url_path.lstrip("/")
        try:
            return _mtime(f)
        except OSError:
            return newest_date

    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority, freq in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{SITE_URL}{path}</loc>")
        parts.append(f"    <lastmod>{lastmod_for(path)}</lastmod>")
        parts.append(f"    <changefreq>{freq}</changefreq>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")

    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"[+] Sitemap updated: {len(urls)} URLs")


def _resolve_ref(html_file, ref):
    """Map an image ref to the local path it will be served from, or None if external.

    Returns (local_path, kind) where kind is 'abs' (our own absolute URL),
    'root' (/images/...) or 'rel' (../images/...).
    """
    if ref.startswith(("http://", "https://")):
        if "patrolgarage.ae/" not in ref:
            return None, None  # third-party image, not ours to guarantee
        return PROJECT_ROOT / ref.split("patrolgarage.ae/", 1)[1], "abs"
    if ref.startswith("//"):
        return None, None
    if ref.startswith("/"):
        return PROJECT_ROOT / ref.lstrip("/"), "root"
    return (html_file.parent / ref).resolve(), "rel"


def _fallback_ref(kind, html_file):
    """The fallback image expressed in the same reference style as the broken ref."""
    if kind == "abs":
        return f"{SITE_URL}/{FALLBACK_IMAGE}"
    if kind == "root":
        return f"/{FALLBACK_IMAGE}"
    depth = len((html_file.parent).relative_to(PROJECT_ROOT).parts)
    return "../" * depth + FALLBACK_IMAGE


def _fetch_from_live(local_path):
    """Try to recover a missing image from the live site. Returns True on success.

    This is what makes a deploy self-healing: a working tree that is missing
    images (e.g. the Mac copy after the container generated a hero) pulls them
    back down instead of overwriting live with holes.
    """
    rel = local_path.relative_to(PROJECT_ROOT).as_posix()
    url = f"{SITE_URL}/{rel}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            if resp.status != 200:
                return False
            data = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False
    if not data:
        return False
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)
    print(f"    recovered from live: {rel} ({len(data)//1024} KB)")
    return True


# Hand-authored root pages. The container must never be the source of truth for
# these: it only legitimately mutates index.html's journal grid, which
# journal_update.py regenerates immediately after this runs.
STATIC_PAGES = [
    "index.html", "services.html", "about.html", "contact.html",
    "y62-garage-dubai.html",
    # Hand-authored service pages. Same revert trap applies to them as to the
    # root pages: the container would otherwise redeploy its own stale copies.
    "services/y62-major-service-dubai.html",
    "services/y62-gearbox-transmission-dubai.html",
    "services/nissan-patrol-v8-engine.html",
]


def ensure_static_pages():
    """Adopt the LIVE copy of any root static page the container has diverged from.

    THE BUG THIS FIXES (two silent regressions before it existed):

        Mac edit -> netlify deploy      -> live is correct,
                                           container still holds the OLD file
        05:00    -> container deploys `--dir .` -> ships the OLD file
                                           -> the human edit is silently reverted

    publish.py commits blog/, images/, sitemap.xml and scripts/ but never these
    pages, and it neither pulls nor pushes, so git could not help: the container's
    FILE was stale regardless of what it committed. Netlify deploys are atomic and
    whole-directory, so the container cannot deploy "just the blog" either.

    Live is the most recent human-published state, so live wins. The daily post
    still ships, and the divergence is logged loudly rather than passing silently.

    LIVE HTML IS NOT SOURCE HTML. Netlify rewrites some markup as it serves. The
    one transform on this site (verified 2026-08-13 by diffing all five pages) is
    the form tag on contact.html:

        source:  <form name="contact" method="POST" data-netlify="true" ...>
        served:  <form method='POST' name='contact'>

    Netlify detects forms at DEPLOY time by scanning for data-netlify="true", so
    naively writing the served HTML back to disk would strip that attribute and
    silently break the contact form on the next deploy. So form tags are excluded
    from the comparison and the LOCAL form tag is preserved when adopting.

    Known limitation, logged when it applies: if someone runs `railway up` WITHOUT
    a Netlify deploy, the container is legitimately newer than live and this would
    discard that change. In practice those two always happen together.
    """
    print("[+] Checking root pages against live...")
    form_rx = re.compile(rb"<form\b[^>]*>", re.I)
    diverged, adopted = [], []
    for name in STATIC_PAGES:
        local_path = PROJECT_ROOT / name
        url = f"{SITE_URL}/{name}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                if resp.status != 200:
                    continue
                live = resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            print(f"    [!] could not fetch {name} from live ({e}); leaving local copy")
            continue

        if not live:
            continue
        if not local_path.exists():
            local_path.write_bytes(live)
            adopted.append(f"{name} (missing locally)")
            continue

        local = local_path.read_bytes()
        # Compare with form tags neutralised, so Netlify's serve-time rewrite is
        # not mistaken for a stale container.
        if form_rx.sub(b"<form>", local) == form_rx.sub(b"<form>", live):
            continue

        # Genuine divergence. Adopt live, but keep our own form tags so the
        # data-netlify attributes survive.
        local_forms = form_rx.findall(local)
        merged = live
        if local_forms:
            i = iter(local_forms)
            merged = form_rx.sub(lambda m: next(i, m.group(0)), live)

        # Refuse the adoption if it would drop a Netlify form marker.
        if local.count(b"data-netlify") > merged.count(b"data-netlify"):
            print(f"    [!] {name}: adopting live would drop a data-netlify marker; "
                  f"keeping the local copy instead")
            diverged.append(name + " (NOT adopted, form marker at risk)")
            continue

        diverged.append(name)
        local_path.write_bytes(merged)
        adopted.append(f"{name} ({len(local)} -> {len(merged)} bytes)")

    if not diverged and not adopted:
        print("    all root pages match live")
        return

    # Loud on purpose. A silent revert is what caused the regressions; a silent
    # self-heal would just hide the same divergence in the other direction.
    print("")
    print("    " + "=" * 66)
    print("    [!] CONTAINER WAS STALE — root pages differed from live")
    for line in adopted:
        print(f"    [!]   adopted from live: {line}")
    print("    [!] The live version won. If one of these was an intentional")
    print("    [!] container-side change, it has just been discarded — deploy it")
    print("    [!] from the Mac (netlify deploy) and then run `railway up`.")
    print("    " + "=" * 66)
    print("")


def ensure_images():
    """Guarantee every image referenced by the site exists in the deploy tree.

    Missing images are first recovered from the live site; anything still missing
    has its references rewritten to the fallback hero. A deploy can therefore
    never ship a 404 hero, from the Railway container or from a local checkout.
    """
    print("[+] Verifying images referenced by the site...")
    html_files = sorted(PROJECT_ROOT.glob("*.html")) + sorted(BLOG_DIR.rglob("*.html"))

    recovered = 0
    rewritten = 0
    checked = 0

    for html_file in html_files:
        html = html_file.read_text(encoding="utf-8")
        original = html

        for ref in sorted(set(IMG_REF_RE.findall(html))):
            local_path, kind = _resolve_ref(html_file, ref)
            if local_path is None:
                continue
            checked += 1
            if local_path.exists():
                continue

            if _fetch_from_live(local_path):
                recovered += 1
                continue

            replacement = _fallback_ref(kind, html_file)
            html = html.replace(f'"{ref}"', f'"{replacement}"')
            rewritten += 1
            print(f"    [!] {html_file.name}: {ref} missing and not on live "
                  f"— fell back to {replacement}")

        if html != original:
            html_file.write_text(html, encoding="utf-8")

    print(f"    {checked} refs checked, {recovered} recovered, {rewritten} rewritten to fallback")
    return recovered, rewritten


def run(cmd, cwd=PROJECT_ROOT, capture=True):
    # Hide auth token in printed command
    safe_cmd = []
    skip_next = False
    for arg in cmd:
        if skip_next:
            safe_cmd.append("***")
            skip_next = False
        elif arg == "--auth":
            safe_cmd.append(arg)
            skip_next = True
        else:
            safe_cmd.append(arg)
    print(f"    $ {' '.join(safe_cmd)}")

    if capture:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"    {result.stdout.strip()[:500]}")
        if result.returncode != 0 and result.stderr.strip():
            print(f"    [err] {result.stderr.strip()[:300]}")
        return result.returncode == 0
    else:
        result = subprocess.run(cmd, cwd=cwd)
        return result.returncode == 0


def publish(keyword=None):
    # Runs BEFORE journal_update, because adopting a live page would otherwise
    # discard the journal grid that journal_update owns and regenerates.
    ensure_static_pages()

    # Runs before the journal index and git so recovered images get committed
    # and the regenerated index picks up any fallback rewrites.
    ensure_images()

    print("[+] Updating sitemap...")
    update_sitemap()

    # Regenerated every run for the same reason as the sitemap: the cron adds
    # posts twice a week, so a hand-written llms.txt goes stale immediately.
    print("[+] Regenerating llms.txt...")
    llms_result = subprocess.run(
        ["python3", "scripts/gen_llms_txt.py"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if llms_result.returncode == 0:
        print(f"    {llms_result.stdout.strip()}")
    else:
        # Never fatal: llms.txt going stale must not block a publish.
        print(f"    [!] llms.txt generation failed: {llms_result.stderr[:300]}")

    print("[+] Regenerating journal index...")
    journal_result = subprocess.run(
        ["python3", "scripts/journal_update.py"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if journal_result.returncode == 0:
        print("    Journal index updated")
        # stdout is otherwise swallowed on success, which would hide the
        # "fell back to mtime" warning journal_update emits when a post has no
        # JSON-LD datePublished — the exact condition that silently re-dated the
        # listing before. Forward just those lines.
        for line in journal_result.stdout.splitlines():
            if line.startswith("[!]"):
                print(f"    {line}")
    else:
        print(f"    [!] Journal update failed: {journal_result.stderr[:300]}")

    git_check = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=PROJECT_ROOT, capture_output=True, text=True
    )
    if git_check.returncode == 0:
        print("\n[+] Committing to git...")
        msg = f"Auto-publish: {keyword}" if keyword else f"Auto-publish {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        # images/ must be included: hero images are generated at pipeline time and
        # are otherwise never carried into git, so any other checkout deploys without them.
        # Root pages are included so the container's commit reflects what it
        # actually deployed (including anything ensure_static_pages adopted from
        # live). Note this alone does NOT prevent the stale-revert bug — publish.py
        # never pulls or pushes, so the commit is read by nobody; ensure_static_pages
        # is what actually fixes it.
        run(["git", "add", "blog/", "images/", "sitemap.xml", "llms.txt", "scripts/",
             *STATIC_PAGES])
        run(["git", "commit", "-m", msg])

    print("\n[+] Deploying to Netlify...")

    # Build deploy command with env vars if available (for Railway)
    auth_token = os.environ.get("NETLIFY_AUTH_TOKEN")
    site_id = os.environ.get("NETLIFY_SITE_ID")

    cmd = ["netlify", "deploy", "--prod", "--dir", "."]
    if auth_token:
        cmd.extend(["--auth", auth_token])
    if site_id:
        cmd.extend(["--site", site_id])

    success = run(cmd, capture=False)

    if success:
        print("\n[+] DEPLOY SUCCESSFUL")
        if keyword:
            slug = slugify(keyword)
            print(f"    Live: {SITE_URL}/blog/{slug}.html")
    else:
        print("\n[!] Deploy failed. Run manually: netlify deploy --prod")


if __name__ == "__main__":
    keyword = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    publish(keyword)
