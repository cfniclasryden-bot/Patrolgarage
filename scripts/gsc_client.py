#!/usr/bin/env python3
"""Google Search Console API client, service-account auth. No third-party SaaS.

Replaces the SEO Gets MCP dependency, which has been subscription-blocked and
has therefore blocked every data question about this site.

Credentials, in order of precedence:
  1. GSC_SERVICE_ACCOUNT_JSON  — the whole service-account JSON as one env var
                                 (this is what Railway gets; no file on disk)
  2. GSC_SERVICE_ACCOUNT_FILE  — path to the JSON key file (handy locally)

Property is GSC_PROPERTY, default "sc-domain:patrolgarage.ae". If the property
was verified by URL prefix rather than as a domain property, set it to
"https://patrolgarage.ae/" instead — the API treats those as different
properties and returns 403 for the wrong one.

Setup is documented in docs/GSC-SETUP.md.

Self-test:
    python3 scripts/gsc_client.py            # prints top queries, last 28 days
"""
import json
import os
import sys
from datetime import date, timedelta

import requests

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"

DEFAULT_PROPERTY = os.environ.get("GSC_PROPERTY", "sc-domain:patrolgarage.ae")


class GSCError(RuntimeError):
    pass


def _credentials():
    try:
        from google.oauth2 import service_account
    except ImportError as e:
        raise GSCError(
            "google-auth is not installed. It is in requirements.txt — run "
            "`pip install -r requirements.txt` (and `railway up` so the "
            "container gets it)."
        ) from e

    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if raw:
        info = json.loads(raw)
        return service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])

    path = os.environ.get("GSC_SERVICE_ACCOUNT_FILE")
    if path and os.path.exists(path):
        return service_account.Credentials.from_service_account_file(path, scopes=[SCOPE])

    raise GSCError(
        "No GSC credentials. Set GSC_SERVICE_ACCOUNT_JSON (whole JSON blob) or "
        "GSC_SERVICE_ACCOUNT_FILE (path to the key). See docs/GSC-SETUP.md."
    )


def _token():
    from google.auth.transport.requests import Request
    creds = _credentials()
    creds.refresh(Request())
    return creds.token


def query(dimensions, start_date=None, end_date=None, row_limit=25000,
          filters=None, property_uri=None):
    """Run a Search Analytics query. Returns a list of dicts with the requested
    dimensions plus clicks / impressions / ctr / position."""
    end_date = end_date or (date.today() - timedelta(days=3)).isoformat()
    start_date = start_date or (date.today() - timedelta(days=31)).isoformat()
    site = requests.utils.quote(property_uri or DEFAULT_PROPERTY, safe="")

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "dataState": "final",
    }
    if filters:
        body["dimensionFilterGroups"] = [{"filters": filters}]

    r = requests.post(API.format(site=site), json=body, timeout=60,
                      headers={"Authorization": f"Bearer {_token()}"})
    if r.status_code == 403:
        raise GSCError(
            f"403 for property '{property_uri or DEFAULT_PROPERTY}'. Either the "
            "service account is not added as a user in Search Console, or the "
            "property string is the wrong type (sc-domain: vs https://). See "
            "docs/GSC-SETUP.md step 4."
        )
    if not r.ok:
        raise GSCError(f"GSC API {r.status_code}: {r.text[:400]}")

    out = []
    for row in r.json().get("rows", []):
        rec = dict(zip(dimensions, row.get("keys", [])))
        rec.update({"clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0.0),
                    "position": row.get("position", 0.0)})
        out.append(rec)
    return out


def main():
    try:
        rows = query(["query"], row_limit=15)
    except GSCError as e:
        print(f"[gsc] {e}")
        return 1
    print(f"[gsc] OK — {len(rows)} rows from {DEFAULT_PROPERTY}\n")
    print(f"  {'query':<44} {'clicks':>7} {'impr':>7} {'pos':>6}")
    for r in rows:
        print(f"  {r['query'][:42]:<44} {r['clicks']:>7} {r['impressions']:>7} {r['position']:>6.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
