#!/usr/bin/env python3
"""Translate _redirects and _headers into vercel.json.

Generated, not hand-written, so the Netlify and Vercel rule sets cannot drift
while both platforms are live during the migration.

TRANSLATION NOTES

  * Redirects use `statusCode`, not `permanent`. `permanent: true` emits 308;
    every Netlify rule here is a 301. Both are permanent redirects, but the
    acceptance test for this migration is byte parity against
    URL-BASELINE-PRE-MIGRATION.json, so the code is matched exactly.

  * The `!` force flag has no Vercel equivalent and needs none. Netlify skips a
    non-forced redirect when the path resolves to a real file, which is why 53
    of these carry `301!`. Vercel evaluates `redirects` BEFORE the filesystem,
    so forcing is implicit and `301` vs `301!` collapses to the same thing.

  * cleanUrls stays FALSE. True would 308 all 56 canonical .html URLs to their
    extensionless form and invert the canonical strategy site-wide.

  * trailingSlash is deliberately OMITTED, not set false. Three canonical URLs
    are directory-style with a trailing slash (/, /blog/, /blog/page/2/), and
    `trailingSlash: false` would strip it and break them. Omitting leaves
    Vercel's as-authored behaviour, which is what Netlify does today.

  * Netlify's host-level rules become `has: [{type: "host"}]`. Vercel handles
    http -> https itself, so only the www -> apex rule needs expressing, and it
    collapses Netlify's two-hop http://www chain into one.

Usage:
    python3 scripts/gen_vercel_json.py            # write vercel.json
    python3 scripts/gen_vercel_json.py --check    # exit 1 if out of date
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "vercel.json"


def parse_redirects():
    host_rules, path_rules = [], []
    for raw in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        src, dst, status = parts[0], parts[1], parts[2]
        code = int(status.rstrip("!"))
        if src.startswith("http"):
            m = re.match(r"https?://([^/]+)(/.*)$", src)
            if not m:
                continue
            host, path = m.group(1), m.group(2)
            # http:// and https:// of the same host collapse: Vercel forces https
            if any(h["has"][0]["value"] == host for h in host_rules):
                continue
            host_rules.append({
                "source": path.replace("/*", "/(.*)"),
                "has": [{"type": "host", "value": host}],
                "destination": dst.replace(":splat", "$1"),
                # statusCode, NOT permanent. "permanent": true emits 308, and
                # the whole Netlify set is 301. 308 and 301 are both permanent
                # and Google treats them alike, but parity against the captured
                # baseline is the acceptance test for this migration, so match
                # the code exactly rather than argue it does not matter.
                "statusCode": code,
            })
        else:
            path_rules.append({
                "source": src.replace("/*", "/:path*"),
                "destination": dst,
                "statusCode": code,
            })
    return host_rules, path_rules


def parse_headers():
    out, cur = [], None
    for raw in (ROOT / "_headers").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            cur = {"source": raw.strip().replace("/*", "/(.*)"), "headers": []}
            out.append(cur)
        elif cur is not None and ":" in raw:
            k, v = raw.strip().split(":", 1)
            cur["headers"].append({"key": k.strip(), "value": v.strip()})
    return out


def build():
    host_rules, path_rules = parse_redirects()
    return {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "framework": None,
        "cleanUrls": False,
        "redirects": host_rules + path_rules,
        "headers": parse_headers(),
    }


def main():
    new = json.dumps(build(), indent=2) + "\n"
    if "--check" in sys.argv:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != new:
            print("[!] vercel.json is out of date — run scripts/gen_vercel_json.py")
            return 1
        print("[OK] vercel.json is up to date")
        return 0
    OUT.write_text(new, encoding="utf-8")
    cfg = build()
    print(f"[OK] vercel.json: {len(cfg['redirects'])} redirect(s), "
          f"{len(cfg['headers'])} header rule(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
