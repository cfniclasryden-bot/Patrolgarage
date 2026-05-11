#!/usr/bin/env python3
"""publish.py — update sitemap, commit, deploy to Netlify"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"
SITEMAP = PROJECT_ROOT / "sitemap.xml"
SITE_URL = "https://patrolgarage.ae"


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


def run(cmd, cwd=PROJECT_ROOT, capture=True):
    print(f"    $ {' '.join(cmd)}")
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
    print("[+] Updating sitemap...")
    update_sitemap()

    git_check = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=PROJECT_ROOT, capture_output=True, text=True
    )
    if git_check.returncode == 0:
        print("\n[+] Committing to git...")
        msg = f"Auto-publish: {keyword}" if keyword else f"Auto-publish {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        run(["git", "add", "blog/", "sitemap.xml", "scripts/"])
        run(["git", "commit", "-m", msg])

    print("\n[+] Deploying to Netlify...")
    success = run(["netlify", "deploy", "--prod", "--dir", "."], capture=False)

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
