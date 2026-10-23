#!/usr/bin/env python3
"""Regression test for scripts/indexnow.py and its publish.py hook (2026-10-23).
Offline: no request leaves the machine.

    python3 scripts/test_indexnow.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import indexnow  # noqa: E402

failures = []
H = f"https://{indexnow.HOST}"


def expect(name, got, want):
    if got != want:
        failures.append(f"{name}:\n      got  {got!r}\n      want {want!r}")


# --- the key file is at the site root, holds exactly the key, and ships -------------
expect("key is 32 hex", bool(__import__("re").fullmatch(r"[0-9a-f]{32}", indexnow.KEY)), True)
expect("key file exists at the site root", indexnow.KEY_FILE.exists(), True)
if indexnow.KEY_FILE.exists():
    expect("key file content", indexnow.KEY_FILE.read_text().strip(), indexnow.KEY)
expect("key location", indexnow.KEY_LOCATION, f"{H}/{indexnow.KEY}.txt")
ignored = [l.strip() for l in (ROOT / ".vercelignore").read_text().splitlines()
           if l.strip() and not l.startswith("#")]
expect("key file is not in .vercelignore",
       [p for p in ignored if p in (indexnow.KEY_FILE.name, "*.txt")], [])

# --- file path -> URL (cleanUrls off: .html kept, directory indexes end in /) -----
for path, want in [("index.html", f"{H}/"), ("about.html", f"{H}/about.html"),
                   ("blog/nissan-patrol-x.html", f"{H}/blog/nissan-patrol-x.html"),
                   ("blog/index.html", f"{H}/blog/"), ("blog/page/2/index.html", f"{H}/blog/page/2/"),
                   ("services/y62-major-service-dubai.html", f"{H}/services/y62-major-service-dubai.html"),
                   ("sitemap.xml", None), ("images/blog/a.webp", None), ("scripts/publish.py", None),
                   (f"{indexnow.KEY}.txt", None)]:
    expect(f"path_to_url({path})", indexnow.path_to_url(path), want)

# --- changed_urls against a throwaway repo ---------------------------------------
def sm(*paths):
    return "<urlset>" + "".join(f"<url><loc>{H}{p}</loc></url>" for p in paths) + "</urlset>"


with tempfile.TemporaryDirectory() as d:
    g = lambda *a: subprocess.run(["git", *a], cwd=d, check=True, capture_output=True)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    files = {"index.html": "home", "about.html": "about", "blog/old.html": "old", "blog/keep.html": "keep",
             "blog/moved.html": "m", "sitemap.xml": sm("/", "/about.html", "/blog/old.html", "/blog/keep.html", "/blog/moved.html"),
             "scripts/x.py": "1", "images/a.webp": "a"}
    for p, c in files.items():
        Path(d, p).parent.mkdir(parents=True, exist_ok=True); Path(d, p).write_text(c)
    g("add", "-A"); g("commit", "-qm", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
    Path(d, "about.html").write_text("about v2")                 # modified, in sitemap  -> ping
    Path(d, "blog/new.html").write_text("new")                   # added, in sitemap     -> ping
    Path(d, "templates").mkdir(); Path(d, "templates/post.html").write_text("t")   # not in sitemap -> no
    Path(d, "blog/old.html").unlink()                            # deleted, was in sitemap -> ping
    g("mv", "blog/moved.html", "blog/renamed.html")              # rename: old gone + new  -> both
    Path(d, "scripts/x.py").write_text("2")                      # pipeline file          -> no
    Path(d, "images/a.webp").write_text("b")                     # asset                  -> no
    Path(d, "sitemap.xml").write_text(sm("/", "/about.html", "/blog/keep.html", "/blog/new.html", "/blog/renamed.html"))
    g("add", "-A"); g("commit", "-qm", "deploy")
    got = sorted(indexnow.changed_urls(base, "HEAD", root=d))
    expect("changed_urls", got, sorted([f"{H}/about.html", f"{H}/blog/new.html", f"{H}/blog/old.html",
                                        f"{H}/blog/moved.html", f"{H}/blog/renamed.html"]))
    expect("nothing changed -> no URLs", indexnow.changed_urls("HEAD", "HEAD", root=d), [])
    expect("no base -> no URLs", indexnow.changed_urls(None, "HEAD", root=d), [])

# --- ping: never raises, only our host, empty list sends nothing ------------------
class R:
    def __init__(self, code, text=""): self.status_code, self.text = code, text


calls = []
real_post = indexnow.requests.post
try:
    indexnow.requests.post = lambda url, json=None, **k: (calls.append(json), R(202))[1]
    ok, detail = indexnow.ping([f"{H}/a", f"{H}/a", "https://other.example/x"])
    expect("ping 202 accepted", ok, True)
    expect("ping sends deduped, own-host URLs only", calls[-1]["urlList"], [f"{H}/a"])
    expect("ping body", {k: calls[-1][k] for k in ("host", "key", "keyLocation")},
           {"host": indexnow.HOST, "key": indexnow.KEY, "keyLocation": indexnow.KEY_LOCATION})
    n = len(calls)
    expect("empty list -> no request", (indexnow.ping([])[0], len(calls)), (True, n))
    indexnow.requests.post = lambda *a, **k: R(422, "URLs don't belong to the host")
    expect("ping 422 reported, not raised", indexnow.ping([f"{H}/a"])[0], False)

    def boom(*a, **k):
        raise indexnow.requests.ConnectionError("down")
    indexnow.requests.post = boom
    expect("ping network error reported, not raised", indexnow.ping([f"{H}/a"])[0], False)
    os.environ["INDEXNOW_DISABLED"] = "1"
    indexnow.requests.post = lambda *a, **k: failures.append("sent while INDEXNOW_DISABLED") or R(200)
    expect("INDEXNOW_DISABLED sends nothing", indexnow.ping([f"{H}/a"])[0], True)
finally:
    os.environ.pop("INDEXNOW_DISABLED", None)
    indexnow.requests.post = real_post

# --- the Bing Webmaster key never ships with the site --------------------------------
expect(".bing-api.json is in .vercelignore", ".bing-api.json" in ignored, True)
expect(".gsc-oauth.json is in .vercelignore", ".gsc-oauth.json" in ignored, True)

# --- publish.py hook: base at the start of publish(), ping after a real deploy -----
import publish  # noqa: E402

pings = []
saved = {n: getattr(publish, n) for n in ("run",)}
saved_base, saved_ping = indexnow.deploy_base, indexnow.ping_deploy
saved_env = {k: os.environ.get(k) for k in ("VERCEL_TOKEN", "DEPLOY_DRY_RUN", "DEPLOY_TARGET")}
try:
    os.environ["VERCEL_TOKEN"] = "test-token-not-real"
    os.environ.pop("DEPLOY_TARGET", None); os.environ.pop("DEPLOY_DRY_RUN", None)
    indexnow.ping_deploy = lambda base, head="HEAD": pings.append(base)
    publish._INDEXNOW_BASE = "BASE123"
    publish.run = lambda *a, **k: True
    publish.deploy_site()
    expect("successful deploy pings once with the pre-run base", pings, ["BASE123"])
    pings.clear()
    publish.run = lambda *a, **k: False
    publish.deploy_site()
    expect("failed deploy does not ping", pings, [])
    os.environ["DEPLOY_DRY_RUN"] = "1"
    publish.run = lambda *a, **k: failures.append("dry run ran the deploy") or True
    publish.deploy_site()
    expect("dry-run deploy does not ping", pings, [])
    os.environ.pop("DEPLOY_DRY_RUN")
    indexnow.ping_deploy = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bang"))
    publish.run = lambda *a, **k: True
    expect("a crashing ping does not fail the deploy", publish.deploy_site(), True)
    # publish() must take the base BEFORE it commits: stop it at the commit and look.
    seen = []
    indexnow.deploy_base = lambda: seen.append("base") or "B2"
    saved_cp = publish.commit_and_push
    publish.commit_and_push = lambda keyword=None: seen.append("commit") or False
    for n in ("ensure_static_pages", "ensure_images", "update_sitemap"):
        saved[n] = getattr(publish, n); setattr(publish, n, lambda *a, **k: None)
    saved["subprocess_run"] = publish.subprocess.run
    publish.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "", "")
    # copy_pins and patch_ad_routing WRITE pages; publish() imports them by name,
    # so stand-ins in sys.modules keep this test from touching the site.
    import types
    real_mods = {m: sys.modules.get(m) for m in ("copy_pins", "patch_ad_routing")}
    sys.modules["copy_pins"] = types.SimpleNamespace(apply_all=lambda: (0, 0, []))
    sys.modules["patch_ad_routing"] = types.SimpleNamespace(run=lambda write=False: [])
    try:
        publish.publish()
    finally:
        for m, mod in real_mods.items():
            if mod is None: sys.modules.pop(m, None)
            else: sys.modules[m] = mod
    publish.commit_and_push = saved_cp
    expect("publish() takes the base before committing", seen[:2], ["base", "commit"])
    expect("publish() stores the base for deploy_site()", publish._INDEXNOW_BASE, "B2")
finally:
    publish.subprocess.run = saved.pop("subprocess_run", publish.subprocess.run)
    for n, f in saved.items():
        setattr(publish, n, f)
    indexnow.deploy_base, indexnow.ping_deploy = saved_base, saved_ping
    for k, v in saved_env.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v

if failures:
    print(f"[!] indexnow regression FAILED ({len(failures)}):")
    for f in failures:
        print("    - " + f)
    sys.exit(1)
print("[+] indexnow regression passed: key file, URL mapping, changed-pages diff, ping safety, Bing key not shipped, publish hook.")
