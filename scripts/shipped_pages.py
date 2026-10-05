#!/usr/bin/env python3
"""The set of HTML pages that actually reach production.

Ported from topchallenger-site on 2026-10-05 along with the five content guards
that import it. The history below is topchallenger's; the rule is the same here
because this site also deploys to Vercel and also keeps its pipeline files out
of the upload with .vercelignore.

One definition, imported by all the content guards, because a guard that
checks something other than what ships is either failing a correct build or
passing a broken one.

WHAT IS EXCLUDED, AND WHY IT IS TWO THINGS

1. Everything .vercelignore lists. That file is the deploy manifest, so it is
   the authority on what is not published — drafts/, research/, scripts/,
   templates/, CONTENT-MODEL.md and the rest. Reading it rather than restating
   it means a new exclusion only has to be written once.

   drafts/ matters most here. It holds the RAW generated copy, markers and all.
   Correcting it is not the job of a guard: COPY_PINS corrects it at assemble
   time, on the way to blog/, and the draft is meant to stay uncorrected so a
   pin's find-text still matches the text it was written against. A guard
   pointed at drafts/ reports problems that were fixed before anything shipped.

2. .vercel/, which .vercelignore does NOT list and does not need to — it is the
   CLI's own local build directory, not part of the uploaded tree. It is
   .gitignored and untracked, so it exists only on whichever machine last ran a
   build, and it is a SNAPSHOT: on 2026-09-18 the copy on this machine was from
   23 August, holding 18 stale blog pages that predated a month of corrections.

   Left in, it does real damage in both directions. A guard fails on copy that
   was fixed weeks ago and is not live, and on a machine that has never run
   `vercel build` the same guard silently scans 18 fewer pages and passes. The
   two verbatim copies of this helper both had this hole; they passed only
   because those stale pages happened to be clean for their particular checks.

Pages are returned sorted, for stable output across runs.
"""
from pathlib import Path

SITE = Path(__file__).parent.parent

# Build output, not source. See (2) above.
ALWAYS_EXCLUDED = {".vercel"}


def deploy_excluded():
    """Top-level path names kept out of the deploy."""
    out = set(ALWAYS_EXCLUDED)
    ignore = SITE / ".vercelignore"
    if not ignore.exists():
        return out
    for line in ignore.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.rstrip("/").split("/")[0])
    return out


def shipped_pages():
    """Every .html file that reaches production, sorted."""
    excluded = deploy_excluded()
    return sorted(p for p in SITE.rglob("*.html")
                  if "node_modules" not in p.parts
                  and not (set(p.relative_to(SITE).parts) & excluded))
