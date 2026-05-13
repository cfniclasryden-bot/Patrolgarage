#!/usr/bin/env python3
"""image_gen.py - generate gpt-image-1 hero image and replace template hero"""

import sys
import re
import base64
import requests
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).parent.parent
BLOG = ROOT / "blog"
IMAGES_DIR = ROOT / "images" / "blog"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()

def get_post_title(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else None

def build_prompt(title):
    return (
        f"Cinematic automotive photograph illustrating: '{title}'. "
        "A Nissan Patrol Y62 SUV in a Dubai workshop or desert setting. "
        "Dark moody lighting, professional editorial photography, "
        "no text overlays, no logos, no faces, "
        "wide composition, deep blacks, warm golden Middle Eastern tones, "
        "35mm lens, shallow depth of field, automotive magazine style."
    )

def generate_image(slug, title):
    prompt = build_prompt(title)
    print(f"[*] Generating image: {title[:60]}...")
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1536x1024",
        quality="medium",
        n=1
    )
    # gpt-image-1 returns base64-encoded image data
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

    # Replace hero image references in HTML
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
