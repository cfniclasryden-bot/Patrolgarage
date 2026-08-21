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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDIRECTS = ROOT / "_redirects"
BLOG = ROOT / "blog"

BEGIN = "# BEGIN managed: extensionless URLs -> .html (gen_redirects.py)"
END = "# END managed"

# The marker text changed on 2026-08-21 when this went site-wide. render() also
# strips the old marker, otherwise the previous block would survive underneath
# the new one and the file would carry every blog rule twice.
OLD_BEGIN = "# BEGIN managed: extensionless blog URLs -> .html (gen_redirects.py)"


def pages():
    """Every URL path that needs an extensionless -> .html redirect.

    Site-wide as of 2026-08-21, not blog-only. The blog got these rules on
    2026-08-12; the root and /services pages never did, so Netlify's implicit
    extensionless fallback kept serving them at 200 with a canonical pointing
    at the .html form. Measured on the live site before this change: 46
    extensionless URLs 301'd correctly and 7 served a 200 duplicate —
    /about, /contact, /services, /y62-garage-dubai and three /services/ pages.

    index.html is excluded everywhere: those are directory URLs (/, /blog/,
    /blog/page/2/) whose canonical carries the trailing slash. They have no
    extensionless form to redirect, and a rule for them would loop.
    """
    out = []
    for f in sorted(ROOT.glob("*.html")):
        if f.name != "index.html":
            out.append("/" + f.stem)
    for sub in ("services", "blog"):
        d = ROOT / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.html")):
            if f.name != "index.html":
                out.append(f"/{sub}/{f.stem}")
    return out


def build_block():
    lines = [
        BEGIN,
        "# Generated — do not hand-edit. Run scripts/gen_redirects.py after adding pages.",
        "# One explicit rule per page: a wildcard would also match /<path>.html",
        "# and redirect it to <path>.html.html. See the module docstring.",
    ]
    paths = pages()
    width = max((len(p) for p in paths), default=0) + 2
    for src in paths:
        lines.append(f"{src:<{width}} {src}.html  301!")
    lines.append(END)
    return "\n".join(lines)


def current_text():
    return REDIRECTS.read_text(encoding="utf-8") if REDIRECTS.exists() else ""


def render(existing, block):
    if OLD_BEGIN in existing and END in existing and BEGIN not in existing:
        head = existing.split(OLD_BEGIN)[0].rstrip("\n")
        tail = existing.split(END, 1)[1].lstrip("\n")
        existing = (head + "\n\n" + BEGIN + "\n" + END +
                    ("\n\n" + tail.rstrip("\n") if tail.strip() else "")) + "\n"
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
        # vercel.json is derived from _redirects, so an up-to-date _redirects
        # with a stale vercel.json is exactly the drift this chain prevents.
        gen = Path(__file__).with_name("gen_vercel_json.py")
        if gen.exists():
            r = subprocess.run([sys.executable, str(gen), "--check"],
                               capture_output=True, text=True)
            print("    " + (r.stdout or "").strip())
            return r.returncode
        return 0

    REDIRECTS.write_text(new, encoding="utf-8")
    print(f"[OK] _redirects: {len(pages())} extensionless redirect(s) written")
    return _sync_vercel()


def _sync_vercel():
    """Regenerate vercel.json from the _redirects we just wrote.

    Both platforms are live during the migration and _redirects is the single
    source of truth for both. If these two files drift, the symptom is a URL
    that redirects correctly on one host and 404s on the other, discovered only
    after DNS moves. Chaining them here makes drift impossible by construction:
    there is no way to add a post, regenerate _redirects, and forget vercel.json.

    Non-fatal by design. A publish must not fail because the Vercel config could
    not be rewritten — the deploy that follows would still ship a correct site on
    Netlify. It logs loudly instead.
    """
    gen = Path(__file__).with_name("gen_vercel_json.py")
    if not gen.exists():
        print("[!] gen_vercel_json.py missing — vercel.json NOT regenerated")
        return 0
    r = subprocess.run([sys.executable, str(gen)], capture_output=True, text=True)
    for line in (r.stdout or "").splitlines():
        print("    " + line)
    if r.returncode != 0:
        print(f"[!] gen_vercel_json.py failed ({r.returncode}) — vercel.json may be "
              f"out of date with _redirects:\n{(r.stderr or '')[:300]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
