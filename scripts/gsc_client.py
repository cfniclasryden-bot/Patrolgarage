#!/usr/bin/env python3
"""Google Search Console API client. No third-party SaaS.

*** THIS IS THE ONLY SOURCE OF TRAFFIC DATA FOR THIS SITE. ***

Do NOT call the SEO Gets MCP. There is no subscription on that account, so
every call returns "you need an SEO Gets subscription to use the MCP" — it has
never once returned data, and reaching for it only stalls the question. GSC is
wired directly here instead. Anything you would have asked SEO Gets (clicks,
impressions, position, per-page or per-query performance) comes from query()
below, which talks to the Search Console API itself.

    import sys; sys.path.insert(0, "scripts")
    import gsc_client as g
    g.query(["query"], start_date="2026-05-12", end_date="2026-08-10")
    g.query(["page"],  start_date=..., end_date=...)   # dimensions: date,
    #     query, page, country, device — as GSC defines them, not SEO Gets'.

GSC keeps 16 months. There is no "Super Site" long-history tier here, so do not
ask for more and expect it back.

AUTH: OAuth refresh token, because this Google org enforces
iam.disableServiceAccountKeyCreation and no service-account key can be issued.
Run scripts/gsc_auth.py once to authorise in a browser; it prints GSC_OAUTH_JSON.
After that this is fully headless, which is what the Railway cron needs.

Credentials, in order of precedence:
  1. GSC_OAUTH_JSON            — {"client_id","client_secret","refresh_token"} as
                                 ONE env var. This is what Railway gets; no file
                                 on disk. Produced by scripts/gsc_auth.py.
  2. GSC_OAUTH_CLIENT_ID / GSC_OAUTH_CLIENT_SECRET / GSC_OAUTH_REFRESH_TOKEN
                               — the same three as separate vars.
  3. .gsc-oauth.json           — local convenience file (gitignored, chmod 600),
                                 written by `gsc_auth.py --write-env`.
  4. GSC_SERVICE_ACCOUNT_JSON  — whole service-account JSON as one env var.
  5. GSC_SERVICE_ACCOUNT_FILE  — path to a service-account key file.
                                 (4 and 5 are kept for the day the org policy
                                 changes; neither works under the current policy.)

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


OAUTH_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          ".gsc-oauth.json")


def _oauth_config():
    """Return (client_id, client_secret, refresh_token) or None."""
    raw = os.environ.get("GSC_OAUTH_JSON")
    if raw:
        d = json.loads(raw)
    elif os.environ.get("GSC_OAUTH_REFRESH_TOKEN"):
        d = {"client_id": os.environ.get("GSC_OAUTH_CLIENT_ID"),
             "client_secret": os.environ.get("GSC_OAUTH_CLIENT_SECRET"),
             "refresh_token": os.environ.get("GSC_OAUTH_REFRESH_TOKEN")}
    elif os.path.exists(OAUTH_FILE):
        with open(OAUTH_FILE) as fh:
            d = json.load(fh)
    else:
        return None
    missing = [k for k in ("client_id", "client_secret", "refresh_token") if not d.get(k)]
    if missing:
        raise GSCError(f"OAuth config is missing: {', '.join(missing)}. "
                       "Re-run scripts/gsc_auth.py.")
    return d["client_id"], d["client_secret"], d["refresh_token"]


def _oauth_token(cfg):
    """Mint a short-lived access token from the long-lived refresh token."""
    client_id, client_secret, refresh_token = cfg
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    })
    if r.status_code == 400 and "invalid_grant" in r.text:
        raise GSCError(
            "invalid_grant: the refresh token is no longer valid. The usual cause "
            "is the OAuth consent screen being User type 'External' and still in "
            "'Testing', which expires refresh tokens after 7 DAYS. Set it to "
            "'Internal' or publish to 'In production', then re-run "
            "scripts/gsc_auth.py. (It can also mean access was revoked.)"
        )
    if not r.ok:
        raise GSCError(f"token refresh failed: {r.status_code} {r.text[:300]}")
    return r.json()["access_token"]


def _credentials():
    try:
        from google.oauth2 import service_account
    except ImportError as e:
        raise GSCError(
            "google-auth is not installed. It is in requirements.txt — run "
            "`pip install -r requirements.txt` (and `railway up` so the "
            "container gets it)."
        ) from e

    def _check_shape(info, where):
        """Google Cloud offers 'OAuth client ID' and 'Service account' next to each
        other under Create credentials, and the OAuth one is the easy wrong turn.
        Its JSON looks like {"web": {...}} or {"installed": {...}} and has no
        private key, so say so plainly instead of failing deeper in google-auth."""
        if info.get("type") == "service_account":
            return
        if "web" in info or "installed" in info:
            raise GSCError(
                f"{where} is an OAuth CLIENT credential, not a service account. "
                "In Google Cloud: APIs & Services -> Credentials -> Create "
                "credentials -> **Service account** (not 'OAuth client ID'), then "
                "open it -> Keys -> Add key -> Create new key -> JSON. The right "
                'file starts with {"type": "service_account", ...}.'
            )
        raise GSCError(
            f'{where} is not a service-account key (no "type": "service_account"). '
            "See docs/GSC-SETUP.md steps 2-3."
        )

    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if raw:
        info = json.loads(raw)
        _check_shape(info, "GSC_SERVICE_ACCOUNT_JSON")
        return service_account.Credentials.from_service_account_info(info, scopes=[SCOPE])

    path = os.environ.get("GSC_SERVICE_ACCOUNT_FILE")
    if path:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            raise GSCError(f"GSC_SERVICE_ACCOUNT_FILE points at {path}, which does not exist.")
        with open(path) as fh:
            _check_shape(json.load(fh), os.path.basename(path))
        return service_account.Credentials.from_service_account_file(path, scopes=[SCOPE])

    raise GSCError(
        "No GSC credentials. Run `python3 scripts/gsc_auth.py` once to authorise "
        "in a browser, then export the GSC_OAUTH_JSON it prints. "
        "See docs/GSC-SETUP.md."
    )


def _token():
    # OAuth first: it is the only path that works under this org's
    # iam.disableServiceAccountKeyCreation policy.
    cfg = _oauth_config()
    if cfg:
        return _oauth_token(cfg)
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
