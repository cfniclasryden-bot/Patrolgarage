#!/usr/bin/env python3
"""Blocking gate for the editorial bans in copy_rules.EDITORIAL_RULES (2026-11-20).

Identical in topchallenger-site and patrolgarage.

    python3 scripts/check_editorial.py blog/<slug>.html      # pipeline gate, one post
    python3 scripts/check_editorial.py                       # every shipped page
    python3 scripts/check_editorial.py --write-baseline      # freeze legacy hits (once)

A finding blocks (exit 2) unless the exact (scope, rule, sentence) is recorded
for that page in scripts/editorial_baseline.json. The baseline is the legacy
copy as it stood on 2026-11-20, frozen so that the rule can block NEW copy from
day one without first rewriting every old page. A new post has no baseline
entry, so any hit blocks it. Fix a legacy page and its entries simply stop
matching; prune them with --write-baseline only after a fix, never to let a new
sentence through.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import copy_rules  # noqa: E402

BASELINE = ROOT / "scripts" / "editorial_baseline.json"


def key(scope, rule, sent):
    return f"{scope}|{rule}|{sent}"


def load_baseline():
    try:
        return json.loads(BASELINE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def findings(path):
    return copy_rules.editorial_findings(Path(path).read_text(encoding="utf-8"))


def rel(path):
    p = Path(path).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def new_findings(path, baseline=None):
    baseline = load_baseline() if baseline is None else baseline
    allowed = set(baseline.get(rel(path), []))
    return [f for f in findings(path) if key(f[0], f[1], f[3]) not in allowed]


def all_pages():
    import shipped_pages
    return list(shipped_pages.shipped_pages())


def main(argv):
    if "--write-baseline" in argv:
        data = {}
        for p in all_pages():
            hits = sorted({key(s, r, t) for s, r, _m, t in findings(p)})
            if hits:
                data[rel(p)] = hits
        BASELINE.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"[baseline] {sum(len(v) for v in data.values())} legacy finding(s) on "
              f"{len(data)} page(s) frozen in {BASELINE.name}")
        return 0
    paths = [a for a in argv if not a.startswith("--")] or all_pages()
    baseline = load_baseline()
    bad = 0
    for p in paths:
        for scope, rule, hit, sent in new_findings(p, baseline):
            bad += 1
            print(f"  BLOCK {rel(p)} [{scope}] {rule} {hit!r}: {sent[:160]}")
    if bad:
        print(f"[!] check_editorial: {bad} banned word(s) or unconfirmed service(s). "
              "Reword; see copy_rules.EDITORIAL_RULES.")
        return 2
    print(f"[OK] check_editorial: {len(paths)} page(s), no new banned wording")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
