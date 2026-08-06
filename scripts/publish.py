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
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [
        ("/", "1.0", "weekly"),
        ("/services.html", "0.9", "monthly"),
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

    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority, freq in urls:
        parts.append("  <url>")
        parts.append(f"    <loc>{SITE_URL}{path}</loc>")
        parts.append(f"    <lastmod>{today}</lastmod>")
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
    # Runs before the journal index and git so recovered images get committed
    # and the regenerated index picks up any fallback rewrites.
    ensure_images()

    print("[+] Updating sitemap...")
    update_sitemap()

    print("[+] Regenerating journal index...")
    journal_result = subprocess.run(
        ["python3", "scripts/journal_update.py"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if journal_result.returncode == 0:
        print("    Journal index updated")
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
        run(["git", "add", "blog/", "images/", "sitemap.xml", "scripts/"])
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
