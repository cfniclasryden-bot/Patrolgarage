#!/usr/bin/env python3
"""Regression test for the hero-image model chain, the approved-image fallback
and the failure alert line.

    python3 scripts/test_hero_fallback.py

Exit 0 = all cases behave. No network and no image is generated: the OpenAI
client is a stub.

WHAT IT HOLDS (added 2026-11-02)
--------------------------------
Every run from 26 Oct to 2 Nov 2026 failed at "generate hero image" with
400 invalid_value "The model 'gpt-image-1' does not exist.", and the log never
showed it because run() printed only the first 500 characters of stderr.
- The default model is not gpt-image-1, and IMAGE_MODEL overrides it.
- A model rejection moves on to the next model; any other error does not.
- When generation fails, the hero is an approved image and the stage exits 0,
  saying HERO_FALLBACK_USED.
- run() logs the END of stderr, and a failed stage's reason reaches the alert.
"""
import base64
import importlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("OPENAI_API_KEY", "test-only-no-call-is-made")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-only-no-call-is-made")

failures = []


def check(label, ok, detail=""):
    print(f"  {'ok      ' if ok else 'FAIL    '} {label}")
    if not ok:
        failures.append(f"{label}{': ' + detail if detail else ''}")


class ModelGone(Exception):
    def __init__(self):
        super().__init__("Error code: 400 - The model 'gpt-image-1' does not exist.")
        self.body = {"message": "The model 'gpt-image-1' does not exist.",
                     "param": "model", "code": "invalid_value"}


class Quota(Exception):
    def __init__(self):
        super().__init__("Error code: 429 - You exceeded your current quota")
        self.body = {"message": "You exceeded your current quota", "code": "insufficient_quota"}


def png_b64():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (1536, 1024), (90, 90, 90)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class FakeImages:
    def __init__(self, behaviour):
        self.behaviour, self.models = behaviour, []

    def generate(self, model, **kw):
        self.models.append(model)
        b = self.behaviour(model)
        if isinstance(b, Exception):
            raise b
        return type("R", (), {"data": [type("D", (), {"b64_json": b})()]})()


def fake_client(behaviour):
    imgs = FakeImages(behaviour)
    return type("C", (), {"images": imgs})(), imgs


import image_gen as ig  # noqa: E402

print("model chain")
check("default model is not the retired gpt-image-1", ig.IMAGE_MODELS[0] != "gpt-image-1", ig.IMAGE_MODELS[0])
check("gpt-image-1 is not anywhere in the chain", "gpt-image-1" not in ig.IMAGE_MODELS)
os.environ["IMAGE_MODEL"] = "gpt-image-test-override"
check("IMAGE_MODEL overrides the default", importlib.reload(ig).IMAGE_MODELS[0] == "gpt-image-test-override")
del os.environ["IMAGE_MODEL"]
ig = importlib.reload(ig)
check("a 400 on param=model is a model rejection", ig._is_model_rejection(ModelGone()))
check("a quota error is not a model rejection", not ig._is_model_rejection(Quota()))

c, imgs = fake_client(lambda m: ModelGone() if m == ig.IMAGE_MODELS[0] else png_b64())
ig._client = c
out = ig._generate_bytes("prompt")
check("rejected model falls through to the next one", imgs.models == ig.IMAGE_MODELS[:2] and out[:4] == b"\x89PNG", str(imgs.models))
c, imgs = fake_client(lambda m: Quota())
ig._client = c
try:
    ig._generate_bytes("prompt"); raised = False
except Quota:
    raised = True
check("a non-model error is raised at once, without trying other models", raised and len(imgs.models) == 1, str(imgs.models))

print("approved-image fallback")
real_images, real_blog = ig.IMAGES_DIR, ig.BLOG
with tempfile.TemporaryDirectory() as tmp:
    slug = "y62-test-fallback-slug"
    if ig.approved_fallbacks.__code__.co_argcount:
        # PG: the pool IS images/blog (heroes of live posts), so copy it in first.
        import shutil
        (Path(tmp) / "blog").mkdir()
        for j in ig.approved_fallbacks(slug):
            shutil.copy(j, Path(tmp) / j.name)
            (Path(tmp) / "blog" / f"{j.stem}.html").write_text("x")
        ig.BLOG = Path(tmp) / "blog"
    ig.IMAGES_DIR = Path(tmp)
    fb = ig.use_fallback(slug) if ig.use_fallback.__code__.co_argcount == 1 else ig.use_fallback(slug, "Y62 test")
    jpg = fb[0] if isinstance(fb, tuple) else fb
    check("a fallback image is chosen and written", jpg is not None and Path(jpg).exists() and Path(jpg).stat().st_size > 1000)
    if hasattr(ig, "site_config") and hasattr(ig.site_config, "HERO_DEFAULT_SIZE"):
        from PIL import Image
        check("TC fallback is written at the generated hero size",
              Image.open(jpg).size == tuple(ig.site_config.HERO_DEFAULT_SIZE), str(Image.open(jpg).size))
        check("TC fallback carries the approved human alt", isinstance(fb, tuple) and len(fb[1]) > 20)
        check("no fallback photo claims genuine parts",
              all("genuine" not in a.lower() for _, a in ig.approved_fallbacks()))
    else:
        live = [j for j in ig.approved_fallbacks("x")]
        check("PG fallback pool is only heroes of live posts",
              bool(live) and all((ig.BLOG / f"{j.stem}.html").exists() for j in live))
        check("PG fallback never reuses the post's own file", all(j.stem != slug for j in ig.approved_fallbacks(slug)))
ig.IMAGES_DIR, ig.BLOG = real_images, real_blog

print("stage contract (subprocess, fallback path)")
with tempfile.TemporaryDirectory() as tmp:
    # Run main() in a child with generation forced to fail and outputs redirected,
    # so the real repo's images and posts are never written.
    code = f"""
import sys, shutil; sys.path.insert(0, {str(HERE)!r})
from pathlib import Path
import image_gen as ig
src = sorted(ig.BLOG.glob('*.html'))[0]
tmp = Path({tmp!r})
(tmp / 'blog').mkdir(); (tmp / 'img').mkdir()
shutil.copy(src, tmp / 'blog' / 'y62-stage-test.html')
pool = ig.approved_fallbacks('y62-stage-test') if ig.approved_fallbacks.__code__.co_argcount else None
ig.BLOG = tmp / 'blog'
if pool is not None:
    for j in pool: shutil.copy(j, tmp / 'img' / j.name); (tmp/'blog'/(j.stem+'.html')).write_text('x')
ig.IMAGES_DIR = tmp / 'img'
def boom(*a, **k): raise RuntimeError("The model 'gpt-image-1' does not exist.")
ig.generate_image = boom
if hasattr(ig, 'describe_image'): ig.describe_image = lambda p: None
sys.argv = ['image_gen.py', 'y62-stage-test']
ig.main()
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=HERE.parent)
    check("generation failure + fallback exits 0", r.returncode == 0, (r.stderr or r.stdout)[-400:])
    check("it says HERO_FALLBACK_USED", "HERO_FALLBACK_USED" in r.stdout)
    check("it prints the real error on stderr", "does not exist" in r.stderr)

print("failure logging")
import run_pipeline as rp  # noqa: E402
logged = []
rp.log = logged.append
msg = "BadRequestError: The model 'gpt-image-1' does not exist."
cmd = [sys.executable, "-c", "import sys\nfor i in range(80): print('frame', i, 'x'*40, file=sys.stderr)\n"
       f"sys.exit({msg!r})"]
ok = rp.run(cmd, "generate hero image")
check("a failing stage returns False", ok is False)
check("the exception line at the END of stderr is logged", any("does not exist" in l for l in logged))
check("the alert detail is the exception line", rp.LAST_FAILURE["detail"] == msg, rp.LAST_FAILURE["detail"])
src = (HERE / "run_pipeline.py").read_text()
check("main() logs one [ALERT] PIPELINE_FAILED line", "[ALERT] PIPELINE_FAILED" in src)

if failures:
    print("\n[!] hero fallback regression FAILED:")
    for f in failures:
        print("   -", f)
    sys.exit(1)
print("\n[+] hero fallback regression passed: model chain, approved-image fallback, stage exit, failure logging.")
