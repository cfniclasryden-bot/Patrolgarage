#!/usr/bin/env python3
"""DataForSEO search-volume validation for the keyword queue.

WHY THIS EXISTS
The daily pipeline published 25 posts between 2026-07-19 and 2026-08-12 that
earned, between them, ZERO impressions — while the 19 launch posts had already
earned 1,171 impressions by the same age. The posts were fine; the keywords had
no demand. Across all 24 component topics the old queue targeted, GSC recorded
2 impressions in 90 days.

The cause was structural: keyword_generator.py asked an LLM for keywords and
inserted whatever came back. Nothing ever checked whether anyone searches them.

This module is the gate. Every keyword must clear it before it can reach the
queue.

FAIL CLOSED. If DataForSEO is unreachable, unconfigured, or returns something
unparseable, this raises — it never returns "assume it's fine". An open failure
mode would silently restore the exact bug being fixed here: at one post a day,
a validator that degrades to a pass-through refills the queue with dead
keywords within weeks and nobody notices until the next GSC review.

Credentials (both required):
    DATAFORSEO_LOGIN
    DATAFORSEO_PASSWORD
Get them from https://app.dataforseo.com/api-access

Config:
    DATAFORSEO_LOCATION_CODE   default 2784 (United Arab Emirates)
    DATAFORSEO_LANGUAGE_CODE   default "en"
    MIN_SEARCH_VOLUME          default 10 (monthly searches; below this a post
                               cannot earn enough to be worth a day's run)

Self-test:
    python3 scripts/keyword_volume.py "nissan patrol service cost dubai" ...
"""
import os
import re
import sys
import json

import requests

API = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
LOCATIONS_API = "https://api.dataforseo.com/v3/keywords_data/google_ads/locations"

DEFAULT_LOCATION = int(os.environ.get("DATAFORSEO_LOCATION_CODE", "2784"))  # UAE
LANGUAGE = os.environ.get("DATAFORSEO_LANGUAGE_CODE", "en")
MIN_VOLUME = int(os.environ.get("MIN_SEARCH_VOLUME", "10"))

# DataForSEO's own constraints on the endpoint (documented):
MAX_KEYWORDS_PER_REQUEST = 1000
MAX_KEYWORD_CHARS = 80
MAX_KEYWORD_WORDS = 10


class VolumeError(RuntimeError):
    """Raised for any condition that leaves volume unverified. Never swallow
    this into a default-allow — see the FAIL CLOSED note above."""


# --- banned patterns ------------------------------------------------------
#
# Individual small components. Every one of these shipped a post that earned
# zero impressions, and the pattern generalises: a Patrol owner in Dubai does
# not search "<small part> replacement cost" — they search for the symptom, the
# service, or the workshop. Volume checking alone would catch most of these,
# but a keyword tool will occasionally report phantom volume on a long-tail
# string that no real person types, so these are banned outright.
#
# Deliberately NOT banned: major assemblies that DO earn — differential
# (45 impressions), gearbox/transmission (184), suspension, engine, AC. The
# ban is on parts, not on systems.
BANNED_PATTERNS = [
    r"\babs sensor\b",
    r"\b(oxygen|o2) sensor\b",
    r"\bthrottle body\b",
    r"\bcv joint\b",
    r"\bcrankshaft position sensor\b",
    r"\bcoolant temperature sensor\b",
    r"\bcamshaft (position )?sensor\b",
    r"\bfuel pressure regulator\b",
    r"\bfuel injector\b",
    r"\bspark plug\b",
    r"\bwater pump\b",
    r"\bvalve cover\b",
    r"\bengine mount\b",
    r"\bstarter motor\b",
    r"\bdriveshaft\b",
    r"\bbrake light\b",
    r"\bdashcam\b",
    r"\btow bar\b",
    r"\bsnorkel\b",
    r"\b(paint protection|ppf)\b",
    r"\bintercooler\b",
    r"\bair ?bag\b",
    # lift kits / height modification: the workshop does not offer these
    # (owner decision 2026-08-13) — a post that ranks for them draws the wrong
    # enquiry, so they must not enter the queue even at real volume.
    # Bare "lift", not just "lift kit". A generator preview proposed "nissan
    # patrol body lift" and it passed every gate; a qualifier-aware pattern
    # then still missed "2 inch lift", because the qualifier sits BEFORE the
    # word. In a Patrol keyword list "lift" always means raising the car, which
    # is not a service here, so match the word itself and stop playing
    # whack-a-mole with the qualifiers.
    r"\blift\b",
    # Component compounds from the dead cohort. These carry real generic
    # volume ("head gasket" 480/mo, "rear differential" 170) but it is all-car
    # volume a Patrol-only site cannot capture, and every post built on them
    # earned zero. Note "differential" alone is NOT banned — the differential
    # repair post earns 45 impressions; only the component compound is.
    r"\bhead gasket\b",
    r"\brear differential\b",
    r"\bdifferential seal\b",
    r"\boil cooler\b",
    r"\bbrake caliper\b",
    r"\bexhaust manifold\b",
    r"\bfuel tank\b",
    r"\bsuspension arm\b",
    r"\bty?re rotation\b",
    r"\btransfer case\b",
    r"\bcatalytic converter\b",
]
_BANNED = [re.compile(p, re.I) for p in BANNED_PATTERNS]


def banned_reason(keyword):
    """Return the matched banned pattern, or None."""
    for rx in _BANNED:
        if rx.search(keyword):
            return rx.pattern
    return None


# --- shape checks ---------------------------------------------------------

def shape_reason(keyword):
    """Return why the keyword is unusable as-is, or None. These mirror
    DataForSEO's documented limits — a request containing an over-long keyword
    fails the whole batch, so screen before sending."""
    k = keyword.strip()
    if not k:
        return "empty"
    if len(k) > MAX_KEYWORD_CHARS:
        return f"over {MAX_KEYWORD_CHARS} chars ({len(k)})"
    if len(k.split()) > MAX_KEYWORD_WORDS:
        return f"over {MAX_KEYWORD_WORDS} words ({len(k.split())})"
    return None


# --- DataForSEO -----------------------------------------------------------

def _auth():
    login = os.environ.get("DATAFORSEO_LOGIN", "").strip()
    password = os.environ.get("DATAFORSEO_PASSWORD", "").strip()
    if not login or not password:
        raise VolumeError(
            "DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD are not set. Volume "
            "cannot be verified, so no keyword may be added — this gate fails "
            "closed by design. Set both in the Railway env for "
            "patrolgarage-pipeline (and locally to run the self-test)."
        )
    return (login, password)


def verify_location_code(code=DEFAULT_LOCATION):
    """Confirm the location code really is the one we think it is.

    A wrong constant here is the quietest possible failure: every lookup
    succeeds, every volume is real, and the whole queue is validated against
    the wrong country. Cheap to check, so check."""
    r = requests.get(LOCATIONS_API, auth=_auth(), timeout=60)
    if not r.ok:
        raise VolumeError(f"locations lookup failed: {r.status_code} {r.text[:300]}")
    for row in (r.json().get("tasks") or [{}])[0].get("result") or []:
        if row.get("location_code") == code:
            return row.get("location_name")
    raise VolumeError(f"location_code {code} not found in DataForSEO's location list")


def search_volumes(keywords, location_code=DEFAULT_LOCATION, language=LANGUAGE):
    """Return {keyword_lower: search_volume|None} for every keyword sent.

    None means DataForSEO returned the keyword with a null volume — which it
    does for terms with no measurable demand. Callers must treat None as zero,
    not as unknown-so-allow."""
    kws = [k.strip().lower() for k in keywords if k and k.strip()]
    if not kws:
        return {}
    if len(kws) > MAX_KEYWORDS_PER_REQUEST:
        raise VolumeError(f"{len(kws)} keywords exceeds the {MAX_KEYWORDS_PER_REQUEST} limit")

    body = [{"keywords": kws, "location_code": location_code, "language_code": language}]
    r = requests.post(API, auth=_auth(), json=body, timeout=120)
    if r.status_code == 401:
        raise VolumeError("DataForSEO rejected the credentials (401)")
    if not r.ok:
        raise VolumeError(f"DataForSEO HTTP {r.status_code}: {r.text[:300]}")

    try:
        payload = r.json()
    except ValueError as e:
        raise VolumeError(f"DataForSEO returned non-JSON: {r.text[:200]}") from e

    if payload.get("status_code") != 20000:
        raise VolumeError(
            f"DataForSEO status {payload.get('status_code')}: "
            f"{payload.get('status_message')}"
        )
    tasks = payload.get("tasks") or []
    if not tasks:
        raise VolumeError("DataForSEO returned no tasks")
    task = tasks[0]
    if task.get("status_code") != 20000:
        raise VolumeError(
            f"DataForSEO task {task.get('status_code')}: {task.get('status_message')}"
        )

    out = {}
    for item in task.get("result") or []:
        kw = (item.get("keyword") or "").strip().lower()
        if kw:
            out[kw] = item.get("search_volume")

    # A keyword the API silently dropped is NOT verified. Record it as None so
    # the caller rejects it rather than assuming it passed.
    for k in kws:
        out.setdefault(k, None)
    return out


def validate(keywords, min_volume=MIN_VOLUME, location_code=DEFAULT_LOCATION):
    """Screen keywords, then verify volume. Returns (accepted, rejected).

    accepted: [(keyword, volume), ...] sorted by volume desc
    rejected: [(keyword, reason), ...]

    Raises VolumeError if volume could not be established — callers must let
    that propagate and add nothing."""
    rejected = []
    candidates = []
    for k in keywords:
        k = k.strip().lower()
        why = shape_reason(k) or (
            f"banned pattern {banned_reason(k)}" if banned_reason(k) else None
        )
        if why:
            rejected.append((k, why))
        else:
            candidates.append(k)

    if not candidates:
        return [], rejected

    volumes = search_volumes(candidates, location_code=location_code)

    accepted = []
    for k in candidates:
        v = volumes.get(k)
        if v is None:
            rejected.append((k, "no volume data returned (treated as zero)"))
        elif v == 0:
            rejected.append((k, "zero search volume"))
        elif v < min_volume:
            rejected.append((k, f"volume {v} below minimum {min_volume}"))
        else:
            accepted.append((k, v))

    accepted.sort(key=lambda t: -t[1])
    return accepted, rejected


def main():
    args = [a for a in sys.argv[1:] if a.strip()]
    if not args:
        print(__doc__)
        return 1
    try:
        name = verify_location_code()
        print(f"[dfs] location {DEFAULT_LOCATION} = {name}; min volume {MIN_VOLUME}\n")
        accepted, rejected = validate(args)
    except VolumeError as e:
        print(f"[dfs] {e}")
        return 1
    print(f"ACCEPTED ({len(accepted)}):")
    for k, v in accepted:
        print(f"  {v:>6}/mo  {k}")
    print(f"\nREJECTED ({len(rejected)}):")
    for k, why in rejected:
        print(f"         {k}  — {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
