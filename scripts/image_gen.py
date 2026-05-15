#!/usr/bin/env python3
"""image_gen.py - generate brand-matched hero image and replace template hero"""

import sys
import os
import re
import base64
import requests
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).parent.parent
BLOG = ROOT / "blog"
IMAGES_DIR = ROOT / "images" / "blog"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Hardcoded for Patrol Garage pipeline. Brand profile fetched from Supabase.
SITE_ID = "03ab1c68-a6ef-48b3-987e-0069c4eb2152"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Site-specific subject hints. Without these, brand alone can't tell DALL-E what to render.
# These describe WHAT the article is about, brand profile describes HOW it should look.
SUBJECT_HINT = "a Nissan Patrol SUV (Y61, Y62, or Y63 generation) in a Dubai automotive context"

client = OpenAI()


# ---------- Brand profile loading ----------

def fetch_brand_profile():
    """Load brand profile from Supabase. Returns dict or empty dict on failure."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {}
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/sites",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            params={"id": f"eq.{SITE_ID}", "select": "brand_profile"},
            timeout=10,
        )
        rows = r.json()
        if rows and rows[0].get("brand_profile"):
            return rows[0]["brand_profile"]
    except Exception as e:
        print(f"[!] Could not fetch brand profile: {e}")
    return {}


def describe_color(hex_color):
    """Translate hex to descriptive language for the image model."""
    if not hex_color or not hex_color.startswith("#") or len(hex_color) != 7:
        return ""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    mx, mn = max(r, g, b), min(r, g, b)
    sat = (mx - mn) / max(mx, 1)
    brightness = (r + g + b) / 3

    # Neutrals
    if sat < 0.15:
        if brightness < 64: return "black"
        if brightness < 128: return "charcoal grey"
        if brightness < 200: return "light grey"
        return "off-white"

    # Saturated hues
    if r >= g and r >= b:
        hue = "warm amber" if g > b and g > r * 0.7 else ("rust red" if g > b else ("crimson" if b > r * 0.7 else "red"))
    elif g >= r and g >= b:
        hue = "teal green" if b > g * 0.7 else ("olive" if r > g * 0.7 else "green")
    else:
        hue = "purple" if r > b * 0.7 else ("teal" if g > b * 0.7 else "blue")

    # Brightness modifier
    if brightness > 200:
        hue = "pale " + hue
    elif brightness < 80:
        hue = "deep " + hue

    # Special palette names
    if r > 200 and 170 < g < 220 and 130 < b < 180: hue = "warm beige"
    if 130 < r < 180 and 100 < g < 150 and 50 < b < 110: hue = "rich tan"

    return hue


def brand_style_block(brand):
    """Convert brand profile dict into a prompt fragment."""
    if not brand:
        return ""

    parts = []

    # Color palette (skip if monochrome — let mood handle it)
    mood = brand.get("visual_mood", "")
    is_monochrome = "monochrome" in mood.lower()

    if not is_monochrome:
        colors = brand.get("brand_colors", {}) or {}
        color_names = [describe_color(c) for c in [colors.get("primary"), colors.get("secondary"), colors.get("accent")] if c]
        color_names = [c for c in color_names if c]
        if color_names:
            parts.append(f"Color palette: {', '.join(color_names)}")

    # Visual mood translation
    mood_map = {
        "monochrome": "high-contrast black and white aesthetic with minimal color",
        "monochrome editorial": "high-contrast black and white editorial photography, magazine-quality lighting",
        "monochrome bold": "high-contrast monochrome with bold cinematic composition",
        "bold": "bold and saturated tones, high-energy composition",
        "muted bright modern": "muted, sophisticated, modern atmosphere",
        "muted bright": "soft refined daylight tones",
        "elegant": "elegant refined premium feel",
        "modern": "modern, clean, contemporary",
    }
    if mood:
        parts.append(f"Mood: {mood_map.get(mood, mood)}")

    # Photography style based on typography
    font = ((brand.get("typography") or {}).get("primary") or "").lower()
    if any(k in font for k in ["serif", "playfair", "didot", "garamond"]):
        parts.append("Photography style: classic, considered framing, soft natural light")
    elif any(k in font for k in ["mono", "jetbrains", "fira"]):
        parts.append("Photography style: dramatic lighting, editorial composition, documentary feel")
    elif any(k in font for k in ["archivo", "geist", "inter", "helvetica", "roboto"]):
        parts.append("Photography style: clean contemporary composition, sharp focus, modern editorial")

    return ". ".join(parts) + "." if parts else ""


# ---------- Existing helpers ----------

def get_post_title(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else None


def build_prompt(title, brand):
    """Build a brand-matched image prompt."""
    style = brand_style_block(brand)
    base = (
        f"Cinematic photograph illustrating: '{title}'. "
        f"Subject: {SUBJECT_HINT}. "
        "No text overlays, no logos, no faces, no license plates. "
        "Wide editorial composition, 35mm lens, shallow depth of field."
    )
    if style:
        return f"{base}\n\nBrand style: {style}"
    return base


def generate_image(slug, title):
    brand = fetch_brand_profile()
    if brand:
        print(f"[*] Brand: {brand.get('visual_mood', 'unknown mood')}, "
              f"primary={(brand.get('brand_colors') or {}).get('primary', 'n/a')}")
    else:
        print("[*] No brand profile found — using default style")

    prompt = build_prompt(title, brand)
    print(f"[*] Prompt:\n{prompt}\n")
    print(f"[*] Generating image: {title[:60]}...")

    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="medium",
        n=1
    )
    img_data = base64.b64decode(resp.data[0].b64_json)
    out_path = IMAGES_DIR / f"{slug}.jpg"
    out_path.write_bytes(img_data)
    print(f"[+] Saved: {out_path.relative_to(ROOT)} ({len(img_data)//1024} KB)")
    return out_path


def replace_template_hero(slug):
    post = BLOG / f"{slug}.html"
    if not post.exists():
        print(f"[!] Post not found: {post}")
        return False

    html = post.read_text()
    rel_path = f"../images/blog/{slug}.jpg"
    abs_url = f"https://patrolgarage.ae/images/blog/{slug}.jpg"

    html = re.sub(
        r'src="[^"]*hero[^"]*\.(jpg|jpeg|png|webp)"',
        f'src="{rel_path}"',
        html,
        flags=re.IGNORECASE
    )
    html = re.sub(
        r'(content|src)="https://patrolgarage\.ae/images/[^"]*\.(jpg|jpeg|png|webp)"',
        f'\\1="{abs_url}"',
        html,
        flags=re.IGNORECASE
    )

    post.write_text(html)
    print(f"[+] Updated hero image in {post.name}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 image_gen.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    post = BLOG / f"{slug}.html"

    if not post.exists():
        print(f"[!] Post not found: {post}")
        sys.exit(1)

    title = get_post_title(post.read_text())
    if not title:
        print(f"[!] No <h1> title found in {post}")
        sys.exit(1)

    generate_image(slug, title)
    replace_template_hero(slug)


if __name__ == "__main__":
    main()
