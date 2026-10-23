#!/usr/bin/env python3
"""Bing Webmaster Tools API client. Sibling of gsc_client.py.

    import sys; sys.path.insert(0, "scripts")
    import bing_client as b
    b.query_stats("topchallenger.ae", days=30)      # clicks, impressions, position by query
    b.page_stats("patrolgarage.ae", days=30)        # the same by page
    b.query_pages("topchallenger.ae", "y62 garage") # pages for one query
    b.page_queries("topchallenger.ae", "https://topchallenger.ae/abu-dhabi")
    b.traffic("topchallenger.ae", days=30)          # site totals by day
    b.crawl_stats("patrolgarage.ae")                # crawled pages, errors, by day
    b.crawl_issues("patrolgarage.ae")
    b.url_info("topchallenger.ae", "https://topchallenger.ae/")   # index details, one URL
    b.submission_quota("topchallenger.ae")
    b.submit_urls("topchallenger.ae", [...])        # WRITES: spends daily quota. Not called by the self-test.

Self-test, read-only:
    python3 scripts/bing_client.py                  # both sites, last 30 days
    python3 scripts/bing_client.py topchallenger.ae 90

Every account-wide site is listed by sites(). Both topchallenger.ae and
patrolgarage.ae were added to this account (Owner role) and had their sitemaps
submitted on 2026-10-23, so every stats call returned zero rows that day. Bing
fills them in over the following days. An empty list means "no data yet", not
an error; errors raise BingError.

AUTH: one API key for the whole Bing Webmaster account (Settings -> API access).
Precedence:
  1. BING_WEBMASTER_API_KEY   env var (what a Railway service would get)
  2. .bing-api.json           {"api_key": "..."} at the repo root, gitignored, chmod 600
The key travels as the `apikey` query parameter, so it is scrubbed from every
error message this module raises. Never print a request URL.

AI PERFORMANCE (Copilot / AI-summary citations) is NOT in the API. The report
launched in Bing Webmaster Tools in Feb 2026 as a CSV export only; Microsoft said
API support is on the backlog with no date. The documented IWebmasterApi has no
such method. Export it by hand from the web UI.

Positions: Bing reports AvgImpressionPosition and AvgClickPosition per row. Their
scale was not checked against the web UI when this was written (there was no
data yet); compare one query with the UI before trusting a number.
"""
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://ssl.bing.com/webmaster/api.svc/json/"
ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / ".bing-api.json"
SITES = ("topchallenger.ae", "patrolgarage.ae")


class BingError(RuntimeError):
    pass


def _key():
    k = os.environ.get("BING_WEBMASTER_API_KEY")
    if not k and KEY_FILE.exists():
        k = json.loads(KEY_FILE.read_text()).get("api_key")
    if not k:
        raise BingError("No Bing key: set BING_WEBMASTER_API_KEY or create .bing-api.json "
                        '({"api_key": "..."}, chmod 600, gitignored).')
    return k


def _scrub(text, key):
    return re.sub(r"apikey=[^&\s'\"]+", "apikey=***", str(text)).replace(key, "***")


def _call(method, http="GET", params=None, body=None):
    key = _key()
    p = dict(params or {}, apikey=key)
    try:
        if http == "GET":
            r = requests.get(API + method, params=p, timeout=60)
        else:
            r = requests.post(API + method, params={"apikey": key}, json=body, timeout=60)
    except requests.RequestException as e:
        raise BingError(f"{method}: {type(e).__name__}: {_scrub(e, key)}") from None
    if r.status_code != 200:
        raise BingError(f"{method}: HTTP {r.status_code}: {_scrub(r.text[:400], key)}")
    try:
        return r.json().get("d")
    except ValueError:
        raise BingError(f"{method}: non-JSON reply: {_scrub(r.text[:200], key)}") from None


def site_url(site):
    """'topchallenger.ae' or 'https://topchallenger.ae' -> 'https://topchallenger.ae/'."""
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    return s.rstrip("/") + "/"


def _date(v):
    """Bing's '/Date(1792730806000)/' or '/Date(1792730806000-0700)/' -> date."""
    m = re.match(r"/Date\((-?\d+)", v or "")
    return datetime.fromtimestamp(int(m.group(1)) / 1000, timezone.utc).date() if m else None


def _since(rows, days):
    if not days:
        return rows
    cutoff = date.today() - timedelta(days=days)
    return [r for r in rows if r.get("date") and r["date"] >= cutoff]


def _stats_rows(raw, label):
    out = []
    for x in raw or []:
        out.append({label: x.get("Query"), "date": _date(x.get("Date")),
                    "clicks": x.get("Clicks", 0), "impressions": x.get("Impressions", 0),
                    "avg_impression_position": x.get("AvgImpressionPosition"),
                    "avg_click_position": x.get("AvgClickPosition")})
    return out


# ------------------------------------------------------------------ read
def sites():
    return [{"url": s["Url"], "verified": s["IsVerified"]} for s in _call("GetUserSites") or []]


def query_stats(site, days=30):
    """One row per query per period Bing returns, filtered to the last `days`."""
    return _since(_stats_rows(_call("GetQueryStats", params={"siteUrl": site_url(site)}), "query"), days)


def page_stats(site, days=30):
    return _since(_stats_rows(_call("GetPageStats", params={"siteUrl": site_url(site)}), "page"), days)


def query_pages(site, query, days=None):
    raw = _call("GetQueryPageStats", params={"siteUrl": site_url(site), "query": query})
    return _since(_stats_rows(raw, "page"), days)


def page_queries(site, page, days=None):
    raw = _call("GetPageQueryStats", params={"siteUrl": site_url(site), "page": page})
    return _since(_stats_rows(raw, "query"), days)


def traffic(site, days=30):
    """Site totals by day (GetRankAndTrafficStats)."""
    rows = [{"date": _date(x.get("Date")), "clicks": x.get("Clicks", 0), "impressions": x.get("Impressions", 0)}
            for x in _call("GetRankAndTrafficStats", params={"siteUrl": site_url(site)}) or []]
    return _since(rows, days)


def crawl_stats(site, days=None):
    rows = []
    for x in _call("GetCrawlStats", params={"siteUrl": site_url(site)}) or []:
        r = {k: v for k, v in x.items() if k != "__type"}
        r["date"] = _date(x.get("Date"))
        rows.append(r)
    return _since(rows, days)


def crawl_issues(site):
    return [{k: v for k, v in x.items() if k != "__type"}
            for x in _call("GetCrawlIssues", params={"siteUrl": site_url(site)}) or []]


def url_info(site, url):
    x = _call("GetUrlInfo", params={"siteUrl": site_url(site), "url": url}) or {}
    return {"url": x.get("Url"), "discovered": _date(x.get("DiscoveryDate")),
            "last_crawled": _date(x.get("LastCrawledDate")), "http_status": x.get("HttpStatus"),
            "document_size": x.get("DocumentSize"), "anchor_count": x.get("AnchorCount"),
            "is_page": x.get("IsPage")}


def url_traffic(site, url):
    return _call("GetUrlTrafficInfo", params={"siteUrl": site_url(site), "url": url})


def sitemaps(site):
    return [{"url": x.get("Url"), "status": x.get("Status"), "urls": x.get("UrlCount"),
             "submitted": _date(x.get("Submitted")), "last_crawled": _date(x.get("LastCrawled"))}
            for x in _call("GetFeeds", params={"siteUrl": site_url(site)}) or []]


def submission_quota(site):
    x = _call("GetUrlSubmissionQuota", params={"siteUrl": site_url(site)}) or {}
    return {"daily": x.get("DailyQuota"), "monthly": x.get("MonthlyQuota")}


# ------------------------------------------------------------------ write
def submit_urls(site, urls):
    """Submit up to the daily quota of URLs for crawling. WRITES and spends quota."""
    urls = list(dict.fromkeys(urls))
    if not urls:
        return 0
    _call("SubmitUrlBatch", http="POST", body={"siteUrl": site_url(site), "urlList": urls})
    return len(urls)


# ------------------------------------------------------------------ helpers
def totals_by(rows, field):
    """Sum clicks/impressions per query or page; impression-weighted mean position."""
    acc = {}
    for r in rows:
        a = acc.setdefault(r[field], {"clicks": 0, "impressions": 0, "_pos": 0.0, "_w": 0})
        a["clicks"] += r["clicks"]
        a["impressions"] += r["impressions"]
        if r.get("avg_impression_position") is not None and r["impressions"]:
            a["_pos"] += r["avg_impression_position"] * r["impressions"]
            a["_w"] += r["impressions"]
    out = []
    for k, a in acc.items():
        out.append({field: k, "clicks": a["clicks"], "impressions": a["impressions"],
                    "position": round(a["_pos"] / a["_w"], 1) if a["_w"] else None})
    return sorted(out, key=lambda r: (-r["clicks"], -r["impressions"]))


def _selftest(site_list, days):
    print(f"Bing Webmaster Tools, last {days} days (read-only)\n")
    for s in site_list:
        q = query_stats(s, days)
        t = totals_by(q, "query")
        clicks, impr = sum(r["clicks"] for r in t), sum(r["impressions"] for r in t)
        feeds = sitemaps(s)
        info = url_info(s, site_url(s))
        print(f"{s}: {len(t)} queries, {clicks} clicks, {impr} impressions | "
              f"sitemap {feeds[0]['status'] if feeds else 'none'} ({feeds[0]['urls'] if feeds else 0} URLs, "
              f"submitted {feeds[0]['submitted'] if feeds else '-'}) | homepage last crawled {info['last_crawled']}")
        if t:
            print(f"  {'query':<50} {'clicks':>6} {'impr':>7} {'pos':>6}")
            for r in t[:10]:
                print(f"  {r['query'][:50]:<50} {r['clicks']:>6} {r['impressions']:>7} {str(r['position']):>6}")
        else:
            print("  (no query rows yet)")
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    days = int(args[-1]) if args and args[-1].isdigit() else 30
    names = [a for a in args if not a.isdigit()] or list(SITES)
    try:
        _selftest(names, days)
    except BingError as e:
        sys.exit(f"[bing] {e}")
