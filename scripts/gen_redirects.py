#!/usr/bin/env python3
"""Regenerate the managed block of _redirects: clean blog URL -> .html.

Background. Netlify serves blog/<slug>.html at BOTH /blog/<slug>.html and
/blog/<slug>, each with a 200 and no redirect. journal_update.py used to link
the extensionless form while canonical, og:url, schema mainEntityOfPage, the
sitemap and every in-body link used .html, so Google indexed both and split
impressions across 13 posts. The site now agrees on .html everywhere; this file
makes the clean form 301 to it so the duplicate is retired rather than left to
compete.

Why one explicit rule per slug, and not a wildcard:

  * Netlify's :placeholder matches any characters within a path segment,
    INCLUDING dots. So `/blog/:slug  /blog/:slug.html  301` also matches
    /blog/foo.html and sends it to /blog/foo.html.html — a 404, on every post.
  * Splats must be terminal, so `/blog/*.html` cannot express "only the ones
    without an extension".
  * The rule must be forced (`301!`), because Netlify skips a non-forced
    redirect when the path resolves to a real asset — and /blog/<slug> DOES
    resolve, via Netlify's pretty-URL fallback to <slug>.html. Forcing it is
    what makes the redirect fire at all, and forcing a wildcard is exactly what
    would make the loop above real.

Enumerating is verbose but cannot loop: the source path never carries .html.

Hand-written rules above the managed markers are preserved.

Usage:
    python3 scripts/gen_redirects.py            # rewrite the managed block
    python3 scripts/gen_redirects.py --check    # exit 1 if out of date
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDIRECTS = ROOT / "_redirects"
BLOG = ROOT / "blog"

BEGIN = "# BEGIN managed: extensionless blog URLs -> .html (gen_redirects.py)"
END = "# END managed"


def slugs():
    return sorted(
        p.stem for p in BLOG.glob("*.html") if p.name != "index.html"
    )


def build_block():
    lines = [
        BEGIN,
        "# Generated — do not hand-edit. Run scripts/gen_redirects.py after adding posts.",
        "# One explicit rule per post: a wildcard would also match /blog/<slug>.html",
        "# and redirect it to <slug>.html.html. See the module docstring.",
    ]
    width = max((len(s) for s in slugs()), default=0) + len("/blog/") + 2
    for s in slugs():
        src = f"/blog/{s}"
        lines.append(f"{src:<{width}} /blog/{s}.html  301!")
    lines.append(END)
    return "\n".join(lines)


def current_text():
    return REDIRECTS.read_text(encoding="utf-8") if REDIRECTS.exists() else ""


def render(existing, block):
    if BEGIN in existing and END in existing:
        head = existing.split(BEGIN)[0].rstrip("\n")
        tail = existing.split(END, 1)[1].lstrip("\n")
        parts = [head, "", block]
        if tail.strip():
            parts += ["", tail.rstrip("\n")]
        return "\n".join(parts) + "\n"
    return existing.rstrip("\n") + "\n\n" + block + "\n"


def main():
    existing = current_text()
    new = render(existing, build_block())

    if "--check" in sys.argv:
        if new != existing:
            print("[!] _redirects is out of date — run scripts/gen_redirects.py")
            return 1
        print("[OK] _redirects is up to date")
        return 0

    REDIRECTS.write_text(new, encoding="utf-8")
    print(f"[OK] _redirects: {len(slugs())} blog redirect(s) written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
