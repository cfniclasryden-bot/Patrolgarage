#!/usr/bin/env python3
"""seed_ad_queue.py — the Abu Dhabi ownership queue, written as queue_position.

2026-10-09, owner decision: 2 of every 3 runs are Abu Dhabi ownership, cost and
reliability questions, seeded from the questions GSC shows this site getting
Abu Dhabi impressions for (10 Sep - 7 Oct 2026). None of them may overlap
topchallenger.ae's Abu Dhabi fault and repair slots, and none states a price,
figure or interval (generate.py + ad_city.AD_CITY_RULES + the guards see to
the copy). What this script does to the PG queue:

  * merges two pending rows into their Abu Dhabi versions (same row, new
    keyword and slug, a note in editorial_notes);
  * retires "nissan patrol power loss diagnosis", a duplicate of the live
    post nissan-patrol-losing-power;
  * inserts the remaining AD_KEYWORDS that are not already rows;
  * numbers every pending row AD, AD, other, AD, AD, other ... in
    queue_position, which run_pipeline.QUEUE_ORDER reads first. Once the AD
    rows run out the remaining rows follow in their current order.

Refuses to write if any AD keyword fails keyword_generator's Gate 0b
(refill_rule) or shares a topic word with a pending topchallenger.ae row.

    python3 scripts/seed_ad_queue.py            # dry run: prints the plan
    python3 scripts/seed_ad_queue.py --write

Needs SUPABASE_URL and SUPABASE_SERVICE_KEY (the Railway service's).
"""
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ad_city  # noqa: E402

_SRC = (HERE / "keyword_generator.py").read_text(encoding="utf-8")
_ns = {}
exec("import re\n" + _SRC[_SRC.index("TC_TERRITORY = "):_SRC.index("def slugify")], _ns)
refill_rule = _ns["refill_rule"]

# In publishing order. The first two are the merged rows.
AD_KEYWORDS = [
    "is the nissan patrol reliable in abu dhabi",
    "what affects nissan patrol maintenance cost in abu dhabi",
    "nissan patrol long term ownership abu dhabi",
    "how abu dhabi heat affects nissan patrol maintenance",
    "what a daily abu dhabi to dubai commute does to a nissan patrol",
    "what to check on a used nissan patrol in abu dhabi",
    "does abu dhabi humidity cause rust on a nissan patrol",
]
MERGES = {
    "nissan patrol reliability abu dhabi": "is the nissan patrol reliable in abu dhabi",
    "nissan patrol long term ownership": "nissan patrol long term ownership abu dhabi",
}
RETIRE = {
    "nissan patrol power loss diagnosis":
        "Retired 2026-10-09: duplicate of the live post nissan-patrol-losing-power.",
    "nissan patrol exhaust smoke":
        "Retired 2026-10-09 (owner): too close to topchallenger.ae's white smoke exhaust slot.",
}
# Retired before it was ever queued: written as a `retired` row so the refill
# (which dedupes against every status) can never add it back.
RETIRE_UNQUEUED = {
    "nissan patrol running costs abu dhabi":
        "Retired 2026-10-09 (owner): would compete with the maintenance-cost post.",
}

# Words that say nothing about the topic; everything else counts as overlap.
_GENERIC = {"nissan", "patrol", "y62", "abu", "dhabi", "uae", "dubai", "in", "the", "a", "on",
            "to", "is", "of", "does", "what", "how", "for", "my", "it"}


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def topic_words(kw):
    return {w for w in re.findall(r"[a-z0-9]+", kw.lower()) if w not in _GENERIC}


def problems(tc_keywords):
    """Why the AD list may not be written, as a list of strings."""
    out = []
    for kw in AD_KEYWORDS:
        if not ad_city.ad_city_for(kw):
            out.append(f"{kw!r}: does not name Abu Dhabi")
        why = refill_rule(kw)
        if why:
            out.append(f"{kw!r}: Gate 0b: {why}")
        if re.search(r"\b(?:aed|dirhams?|\d)", kw, re.I):
            out.append(f"{kw!r}: carries a figure")
        for tc in tc_keywords:
            shared = topic_words(kw) & topic_words(tc)
            if shared:
                out.append(f"{kw!r}: shares {sorted(shared)} with topchallenger.ae's {tc!r}")
    return out


def order(rows):
    """Pending rows in the AD, AD, other pattern. rows: in current queue order."""
    ad = sorted((r for r in rows if ad_city.ad_city_for(r["keyword"])),
                key=lambda r: AD_KEYWORDS.index(r["keyword"]) if r["keyword"] in AD_KEYWORDS else 99)
    other = [r for r in rows if not ad_city.ad_city_for(r["keyword"])]
    out = []
    while ad or other:
        for _ in range(2):
            if ad:
                out.append(ad.pop(0))
        if other:
            out.append(other.pop(0))
    return out


def main():
    write = "--write" in sys.argv[1:]
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        sys.exit("SUPABASE_URL / SUPABASE_SERVICE_KEY not set")
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
         "Prefer": "return=representation"}

    def site(domain):
        return requests.get(f"{url}/rest/v1/sites", headers=h,
                            params={"domain": f"eq.{domain}", "select": "id"}).json()[0]["id"]

    def pending(site_id):
        return requests.get(f"{url}/rest/v1/articles", headers=h, params={
            "site_id": f"eq.{site_id}", "status": "eq.pending",
            "select": "id,keyword,slug,queue_position,created_at",
            "order": "queue_position.asc.nullslast,created_at.asc"}).json()

    pg, tc = site("patrolgarage.ae"), site("topchallenger.ae")
    tc_kws = [r["keyword"] for r in pending(tc)]
    bad = problems(tc_kws)
    if bad:
        print("[!] refusing: the Abu Dhabi list breaks a rule")
        for b in bad:
            print("    -", b)
        return 1
    print(f"[+] {len(AD_KEYWORDS)} Abu Dhabi keywords pass Gate 0b, carry no figure and share "
          f"no topic word with topchallenger.ae's {len(tc_kws)} pending rows")

    rows = pending(pg)
    all_kw = {r["keyword"] for r in requests.get(f"{url}/rest/v1/articles", headers=h, params={
        "site_id": f"eq.{pg}", "select": "keyword"}).json()}
    by_kw = {r["keyword"]: r for r in rows}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for old, new in MERGES.items():
        r = by_kw.get(old)
        if not r:
            continue
        print(f"[merge] {old!r} -> {new!r}")
        if write:
            requests.patch(f"{url}/rest/v1/articles", headers=h, params={"id": f"eq.{r['id']}"},
                           json={"keyword": new, "slug": slugify(new),
                                 "editorial_notes": f"Merged {now}: was {old!r}; Abu Dhabi version."}
                           ).raise_for_status()
        r["keyword"], r["slug"] = new, slugify(new)
        all_kw.add(new)
    for kw, note in RETIRE.items():
        r = by_kw.get(kw)
        if not r:
            continue
        print(f"[retire] {kw!r}: {note}")
        if write:
            requests.patch(f"{url}/rest/v1/articles", headers=h, params={"id": f"eq.{r['id']}"},
                           json={"status": "retired", "queue_position": None,
                                 "editorial_notes": note}).raise_for_status()
        rows = [x for x in rows if x["id"] != r["id"]]
    for kw, note in RETIRE_UNQUEUED.items():
        if kw in all_kw:
            r = by_kw.get(kw)
            if r:
                print(f"[retire] {kw!r}: {note}")
                if write:
                    requests.patch(f"{url}/rest/v1/articles", headers=h, params={"id": f"eq.{r['id']}"},
                                   json={"status": "retired", "queue_position": None,
                                         "editorial_notes": note}).raise_for_status()
                rows = [x for x in rows if x["id"] != r["id"]]
            continue
        print(f"[retire, never queued] {kw!r}: {note}")
        if write:
            requests.post(f"{url}/rest/v1/articles", headers=h, json={
                "site_id": pg, "keyword": kw, "slug": slugify(kw), "status": "retired",
                "editorial_notes": note}).raise_for_status()
    for kw in AD_KEYWORDS:
        if kw in all_kw:
            continue
        print(f"[insert] {kw!r}")
        row = {"keyword": kw, "slug": slugify(kw), "id": None}
        if write:
            resp = requests.post(f"{url}/rest/v1/articles", headers=h, json={
                "site_id": pg, "keyword": kw, "slug": slugify(kw), "status": "pending",
                "editorial_notes": f"Abu Dhabi ownership seed {now} (owner decision)."})
            resp.raise_for_status()
            row["id"] = resp.json()[0]["id"]
        rows.append(row)

    planned = order(rows)
    print("\n[order] queue_position, keyword")
    for i, r in enumerate(planned, 1):
        tag = "AD" if ad_city.ad_city_for(r["keyword"]) else "  "
        print(f"  {i:>2}  {tag}  {r['keyword']}")
        if write:
            requests.patch(f"{url}/rest/v1/articles", headers=h, params={"id": f"eq.{r['id']}"},
                           json={"queue_position": i}).raise_for_status()
    if not write:
        print("\n[dry run] nothing written; --write to apply")
        return 0

    check = pending(pg)
    got = [r["keyword"] for r in check]
    want = [r["keyword"] for r in planned]
    if got[:len(want)] != want:
        print("[!] read-back order differs from the plan")
        return 1
    print(f"\n[+] read back {len(check)} pending rows in the planned order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
