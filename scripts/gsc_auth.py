#!/usr/bin/env python3
"""One-time OAuth authorisation for Search Console. Prints the env vars to store.

Why OAuth and not a service account: this Google org enforces
iam.disableServiceAccountKeyCreation, so no service-account key can be issued.
OAuth with a long-lived refresh token is the supported alternative and works
headlessly afterwards, which is what the Railway cron needs.

Flow: opens a browser once, catches the redirect on a loopback port, exchanges
the code for a refresh token, and prints the three values to store. Nothing is
written to disk unless you pass --write-env.

Only needs `requests` plus the standard library — no google-auth-oauthlib.

    python3 scripts/gsc_auth.py --client-secret-file ~/Downloads/client_secret_*.json

THE 7-DAY TRAP: if the OAuth consent screen is User type "External" and still in
"Testing", Google expires refresh tokens after 7 DAYS and the cron dies quietly
a week later. Either set User type to "Internal" (available on a Workspace org,
and this org clearly is one) or publish the app to "In production". The script
warns about this at the end because it cannot detect it for you.
"""
import argparse
import glob
import json
import os
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"

_result = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _result.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in _result
        self.wfile.write(
            b"<h2>Authorised. You can close this tab and return to the terminal.</h2>"
            if ok else
            b"<h2>Authorisation failed. Check the terminal.</h2>"
        )

    def log_message(self, *a):
        pass  # keep the console clean


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def load_client(path):
    if not path:
        matches = sorted(glob.glob(os.path.expanduser("~/Downloads/client_secret_*.json")))
        if not matches:
            sys.exit("[!] No --client-secret-file given and none found in ~/Downloads.")
        path = matches[-1]
        print(f"[i] using {path}")
    path = os.path.expanduser(path)
    with open(path) as fh:
        data = json.load(fh)
    node = data.get("installed") or data.get("web")
    if not node:
        sys.exit('[!] That file is not an OAuth client. Expected {"installed":…} or {"web":…}.')
    if "installed" not in data:
        print("[!] This is a WEB app client. It will work only if you add the exact")
        print("[!] loopback redirect below to its Authorised redirect URIs. A")
        print("[!] 'Desktop app' client avoids that step entirely.")
    return node["client_id"], node["client_secret"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-secret-file")
    ap.add_argument("--write-env", action="store_true",
                    help="also write .gsc-oauth.json (gitignored) for local use")
    args = ap.parse_args()

    client_id, client_secret = load_client(args.client_secret_file)
    port = free_port()
    redirect = f"http://localhost:{port}"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",   # required to get a refresh token at all
        "prompt": "consent",        # forces a NEW refresh token even if previously granted
    }
    url = f"{AUTH_URI}?{urllib.parse.urlencode(params)}"

    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print(f"\n[i] redirect URI in use: {redirect}")
    print("[i] opening your browser. Sign in as the account that owns the Search")
    print("    Console property, and approve read-only Search Console access.\n")
    print(f"    If the browser does not open, paste this:\n\n{url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    server.socket.settimeout(300)
    for _ in range(300):
        if _result:
            break
        threading.Event().wait(1)

    if "error" in _result:
        sys.exit(f"[!] Google returned an error: {_result['error']}")
    if "code" not in _result:
        sys.exit("[!] Timed out waiting for the browser redirect.")

    resp = requests.post(TOKEN_URI, timeout=30, data={
        "code": _result["code"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect,
        "grant_type": "authorization_code",
    })
    if not resp.ok:
        sys.exit(f"[!] Token exchange failed: {resp.status_code} {resp.text[:300]}")
    tok = resp.json()
    refresh = tok.get("refresh_token")
    if not refresh:
        sys.exit("[!] No refresh_token returned. Revoke prior access at "
                 "https://myaccount.google.com/permissions and re-run.")

    blob = json.dumps({"client_id": client_id, "client_secret": client_secret,
                       "refresh_token": refresh}, separators=(",", ":"))

    print("\n" + "=" * 72)
    print("AUTHORISED. Store this — it is a credential.")
    print("=" * 72)
    print("\nLocal shell:\n")
    print(f"  export GSC_OAUTH_JSON='{blob}'\n")
    print("Railway (one variable, no file on disk):\n")
    print("  railway variables --service patrolgarage-pipeline \\")
    print(f"    --set 'GSC_OAUTH_JSON={blob}'\n")
    print("=" * 72)
    print("REFRESH TOKEN LIFETIME — read this:")
    print("  If the OAuth consent screen is User type 'External' AND still in")
    print("  'Testing', Google expires this token after 7 DAYS and the nightly")
    print("  refresh will start failing silently next week.")
    print("  Fix: set User type to 'Internal', or publish the app to 'In production'.")
    print("=" * 72)

    if args.write_env:
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           ".gsc-oauth.json")
        with open(out, "w") as fh:
            fh.write(blob)
        os.chmod(out, 0o600)
        print(f"\n[i] also written to {out} (chmod 600, gitignored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
