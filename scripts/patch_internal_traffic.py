#!/usr/bin/env python3
"""patch_internal_traffic.py — mark the owner's own visits as GA4 internal traffic.

GA4's IP rule cannot catch a phone on mobile data, and on 2026-10-05 one
post-deploy QA pass sent 59 lead events here (and 52 on topchallenger.ae), more
than a month of real leads. So a browser can mark itself:

    https://patrolgarage.ae/?nr_internal=1   marks this browser as internal
    https://patrolgarage.ae/?nr_internal=0   clears it

While marked, gtag('set') puts traffic_type=internal on EVERY event the page
sends (page_view, whatsapp_click, phone_click, ...), and GA4's "Internal Traffic"
data filter drops them once it is Active. It has to run after gtag() exists and
BEFORE gtag('config'), or the page_view goes out unmarked, so it is inserted
directly in front of the config call. Every page has exactly one, in one of two
forms: pretty-printed (62 pages on 2026-10-07) or minified (5).

Stored in a cookie AND localStorage, both rewritten on every visit, because
Safari caps cookies set from JavaScript at 7 days. A browser that visits at
least once a week stays marked; one that does not needs the link again. The
same snippet is on topchallenger.ae (site_config.INTERNAL_TRAFFIC_JS there).

    python3 scripts/patch_internal_traffic.py           # dry run
    python3 scripts/patch_internal_traffic.py --write   # patch, preserving mtimes

assemble.py calls inject() on its template, so new posts get it too.
Idempotent: a page already containing MARKER is skipped. mtimes are preserved
because journal_update.py derives each post's displayed date and the listing
order from them (see patch_clarity.py).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "nr_internal"

SNIPPET = (
    "(function () {"
    " var k = 'nr_internal', m = /[?&]nr_internal=([01])(?:&|$)/.exec(location.search), on = false;"
    " try { on = m ? m[1] === '1' : (/(?:^|;\\s*)nr_internal=1(?:;|$)/.test(document.cookie) || localStorage.getItem(k) === '1'); } catch (e) {}"
    " if (on) { gtag('set', { traffic_type: 'internal' }); }"
    " try { if (on || m) { document.cookie = k + (on ? '=1; Max-Age=63072000' : '=; Max-Age=0') + '; Path=/; SameSite=Lax; Secure'; } } catch (e) {}"
    " try { if (on) { localStorage.setItem(k, '1'); } else if (m) { localStorage.removeItem(k); } } catch (e) {}"
    " })();"
)

# Group 1 is the indentation before a pretty-printed config call, "" when minified.
CONFIG_RE = re.compile(r"(^[ \t]*)?(gtag\(\s*['\"]config['\"])", re.M)


def inject(html):
    """Return (html, injected). Inserts SNIPPET in front of the first config call."""
    if MARKER in html:
        return html, False
    m = CONFIG_RE.search(html)
    if not m:
        return html, False
    indent = m.group(1)
    if indent is not None:          # pretty: own line, same indentation
        new = html[:m.start()] + indent + SNIPPET + "\n" + html[m.start():]
    else:                           # minified: inline
        new = html[:m.start(2)] + SNIPPET + html[m.start(2):]
    return new, True


def target_files():
    out = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / f for f in out]


def main():
    write = "--write" in sys.argv[1:]
    done, skipped, missing = 0, 0, []
    for path in target_files():
        html = path.read_text(encoding="utf-8")
        new, injected = inject(html)
        if not injected:
            if MARKER in html:
                skipped += 1
            else:
                missing.append(path.relative_to(ROOT))
            continue
        done += 1
        if write:
            st = path.stat()
            path.write_text(new, encoding="utf-8")
            os.utime(path, (st.st_atime, st.st_mtime))
    print(f"[+] {'patched' if write else 'would patch'}: {done}  already present: {skipped}")
    if missing:
        print(f"[!] no gtag('config') found in: {', '.join(map(str, missing))}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
