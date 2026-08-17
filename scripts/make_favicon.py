#!/usr/bin/env python3
"""make_favicon.py — generate the site favicon set from the brand shield mark.

The site had NO favicon of any kind until 2026-08-17: no /favicon.ico, no
<link rel="icon">, nothing. Google therefore showed the generic globe
placeholder next to every patrolgarage.ae result.

The mark is the same shield used in the header logo (scripts/add_logo_mark.py),
so the tab icon and the on-page logo are the same shape. The header version is a
thin outline on a transparent background; that vanishes below ~32px, so the
favicon uses a SOLID white shield on the brand near-black instead. Legibility at
16px wins over stroke fidelity — the silhouette is identical either way.

Google's favicon requirements this satisfies:
  - square, with sides a multiple of 48 (48/96/192/512 PNGs are emitted)
  - a real /favicon.ico at the site root (16/32/48 frames)
  - referenced from <link rel="icon"> with a root-absolute path

Outputs (all at PROJECT_ROOT):
  favicon.ico                 16 + 32 + 48 frames
  favicon.svg                 resolution-independent, preferred by modern browsers
  images/favicon-48x48.png    \
  images/favicon-96x96.png     >  multiples of 48, the size Google wants
  images/favicon-192x192.png  /
  images/favicon-512x512.png  /
  images/apple-touch-icon.png 180x180, opaque (iOS ignores alpha)

Rerun after any brand change:  python3 scripts/make_favicon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "images"

BG = (10, 10, 10, 255)        # --bg  #0a0a0a
FG = (255, 255, 255, 255)     # --white

# The header logo's shield, verbatim from add_logo_mark.py, in its 24x28 viewBox:
#   M12 1 L2 5 v9 c0 7 4.5 11 10 13 c5.5 -2 10 -6 10 -13 V5 l-10 -4 z
VIEW_W, VIEW_H = 24.0, 28.0
SHIELD_TOP = (12.0, 1.0)
SHIELD_LEFT = (2.0, 5.0)
SHIELD_LEFT_BOTTOM = (2.0, 14.0)
CURVE_L = ((2.0, 21.0), (6.5, 25.0), (12.0, 27.0))    # controls + end
CURVE_R = ((17.5, 25.0), (22.0, 21.0), (22.0, 14.0))
SHIELD_RIGHT = (22.0, 5.0)

PAD = 0.14        # fraction of the canvas left clear around the mark
SS = 8            # supersampling factor — Pillow has no antialiased polygon fill


def _cubic(p0, c1, c2, p3, steps=64):
    """Points along a cubic bezier, since Pillow cannot draw one."""
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def shield_points():
    """The shield outline as a flat polygon in viewBox coordinates."""
    pts = [SHIELD_TOP, SHIELD_LEFT, SHIELD_LEFT_BOTTOM]
    pts += _cubic(SHIELD_LEFT_BOTTOM, CURVE_L[0], CURVE_L[1], CURVE_L[2])
    pts += _cubic(CURVE_L[2], CURVE_R[0], CURVE_R[1], CURVE_R[2])
    pts += [SHIELD_RIGHT]
    return pts


def render(size, opaque_bg=True):
    """One square icon at `size` px, drawn big and downsampled for clean edges."""
    big = size * SS
    img = Image.new("RGBA", (big, big), BG if opaque_bg else (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fit the 24x28 mark into the padded square, preserving aspect ratio.
    avail = big * (1 - 2 * PAD)
    scale = min(avail / VIEW_W, avail / VIEW_H)
    off_x = (big - VIEW_W * scale) / 2
    off_y = (big - VIEW_H * scale) / 2
    draw.polygon(
        [(off_x + x * scale, off_y + y * scale) for x, y in shield_points()],
        fill=FG,
    )
    return img.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" fill="#0a0a0a"/>
  <path d="M16 3.5 5.83 7.57v9.15c0 7.12 4.58 11.19 10.17 13.22 5.59-2.03 10.17-6.1 10.17-13.22V7.57L16 3.5z" fill="#ffffff"/>
</svg>
"""


def write_ico(path, images):
    """Assemble a multi-frame .ico from independently rendered PNGs.

    Pillow's ICO writer derives every frame by downscaling the ONE image it is
    given, so passing the 16px render produced a single-frame 16x16 file — no 48,
    which is the frame Google actually looks for. The container is trivial, so
    build it directly and keep each size's own LANCZOS render.

    PNG-compressed frames are used throughout (valid since Vista, and what
    topchallenger.ae's own icon already ships).
    """
    import io
    import struct

    blobs = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        blobs.append(buf.getvalue())

    header = struct.pack("<HHH", 0, 1, len(blobs))       # reserved, type=icon, count
    offset = len(header) + 16 * len(blobs)
    entries = b""
    for img, blob in zip(images, blobs):
        w = 0 if img.width >= 256 else img.width          # 0 means 256 in ICO
        h = 0 if img.height >= 256 else img.height
        entries += struct.pack(
            "<BBBBHHII", w, h, 0, 0, 1, 32, len(blob), offset
        )
        offset += len(blob)
    path.write_bytes(header + entries + b"".join(blobs))


MANIFEST = """{
  "name": "Patrol Garage Dubai — Nissan Patrol Specialist",
  "short_name": "Patrol Garage",
  "icons": [
    { "src": "/images/favicon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/images/favicon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "theme_color": "#0a0a0a",
  "background_color": "#0a0a0a",
  "display": "standalone",
  "start_url": "/"
}
"""


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)

    # .ico — 48 is the frame Google actually wants; 16/32 keep browser tabs crisp.
    write_ico(ROOT / "favicon.ico", [render(s) for s in (16, 32, 48)])
    print("[OK] favicon.ico (16, 32, 48)")

    (ROOT / "favicon.svg").write_text(SVG, encoding="utf-8")
    print("[OK] favicon.svg")

    for s in (48, 96, 192, 512):
        render(s).save(IMAGES / f"favicon-{s}x{s}.png")
        print(f"[OK] images/favicon-{s}x{s}.png")

    # iOS composites onto white if the icon has alpha, so keep it fully opaque.
    render(180).convert("RGB").save(IMAGES / "apple-touch-icon.png")
    print("[OK] images/apple-touch-icon.png (180x180, opaque)")

    (ROOT / "site.webmanifest").write_text(MANIFEST, encoding="utf-8")
    print("[OK] site.webmanifest")


if __name__ == "__main__":
    main()
