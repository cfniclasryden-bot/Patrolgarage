#!/usr/bin/env python3
"""research.py — gather source material for a keyword"""

import sys
import os
import json
import time
import re
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YT_AVAILABLE = True
except ImportError:
    YT_AVAILABLE = False
    print("[!] youtube-transcript-api not installed. YouTube transcripts disabled.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
RESEARCH_DIR.mkdir(exist_ok=True)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def unwrap_ddg_url(href):
    if href.startswith("//duckduckgo.com/l/") or href.startswith("https://duckduckgo.com/l/"):
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        if "uddg" in params:
            return unquote(params["uddg"][0])
    return href


def search_duckduckgo(query, num_results=10):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [!] DuckDuckGo search failed: {e}")
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.select("a.result__a")[:num_results]:
        href = a.get("href", "")
        title = a.get_text(strip=True)
        real_url = unwrap_ddg_url(href)
        if real_url.startswith("http") and title:
            results.append({"title": title, "url": real_url})
    return results


def fetch_page_text(url, max_chars=8000):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
    except Exception:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body
    if not main:
        return None
    text = main.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text[:max_chars]


def search_youtube_videos(query, num_results=5):
    """Find YouTube videos for the keyword via DuckDuckGo."""
    yt_query = f"{query} site:youtube.com"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(yt_query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    video_ids = []
    for a in soup.select("a.result__a"):
        href = unwrap_ddg_url(a.get("href", ""))
        match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", href)
        if match:
            video_ids.append({"id": match.group(1), "title": a.get_text(strip=True)})
        if len(video_ids) >= num_results:
            break
    return video_ids


def fetch_youtube_transcript(video_id, max_chars=6000):
    if not YT_AVAILABLE:
        return None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        text = " ".join(item["text"] for item in transcript)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return None


def gather_research(keyword):
    print(f"[+] Researching: {keyword}")
    sources = []

    # 1. Web search
    print(f"[+] Searching DuckDuckGo for web pages...")
    web_results = search_duckduckgo(keyword, num_results=10)
    print(f"    Found {len(web_results)} web results")
    for i, result in enumerate(web_results, 1):
        print(f"    [{i}/{len(web_results)}] {result['url'][:80]}")
        text = fetch_page_text(result["url"])
        if text and len(text) > 300:
            sources.append({"type": "web", "title": result["title"], "url": result["url"], "content": text})
        else:
            print(f"        [skip]")
        time.sleep(1.2)

    # 2. UAE forum search
    print(f"\n[+] Searching UAE car forums...")
    forum_query = f"{keyword} (site:gcc4x4.com OR site:arabianrides.com OR site:uaeoffroaders.com)"
    forum_results = search_duckduckgo(forum_query, num_results=5)
    print(f"    Found {len(forum_results)} forum results")
    for i, result in enumerate(forum_results, 1):
        print(f"    [{i}/{len(forum_results)}] {result['url'][:80]}")
        text = fetch_page_text(result["url"])
        if text and len(text) > 300:
            sources.append({"type": "forum", "title": result["title"], "url": result["url"], "content": text})
        time.sleep(1.2)

    # 3. YouTube transcripts
    if YT_AVAILABLE:
        print(f"\n[+] Searching YouTube...")
        videos = search_youtube_videos(keyword, num_results=5)
        print(f"    Found {len(videos)} videos")
        for i, video in enumerate(videos, 1):
            print(f"    [{i}/{len(videos)}] {video['title'][:80]}")
            transcript = fetch_youtube_transcript(video["id"])
            if transcript and len(transcript) > 500:
                sources.append({
                    "type": "youtube",
                    "title": video["title"],
                    "url": f"https://youtube.com/watch?v={video['id']}",
                    "content": transcript
                })
            else:
                print(f"        [skip - no transcript]")
            time.sleep(1.0)

    data = {"keyword": keyword, "source_count": len(sources), "sources": sources}
    slug = slugify(keyword)
    out_path = RESEARCH_DIR / f"{slug}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Saved {len(sources)} sources to {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 research.py \"your keyword here\"")
        sys.exit(1)
    keyword = " ".join(sys.argv[1:])
    gather_research(keyword)
