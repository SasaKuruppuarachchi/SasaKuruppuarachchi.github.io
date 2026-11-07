#!/usr/bin/env python3
"""Fetch the latest videos from the YouTube channel RSS feed into _data/videos.json.

Runs server-side (no CORS, no third-party proxy), so the home page can render the
Media section at build time. Used by .github/workflows/update-publications.yml.

  python3 scripts/fetch_youtube.py
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CHANNEL_ID = "UCWAFJEwX8tbk-QnDfpqJPag"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = Path(__file__).resolve().parent.parent / "_data" / "videos.json"
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def main() -> int:
    req = urllib.request.Request(FEED, headers={"User-Agent": "portfolio-site-builder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
    except Exception as e:  # keep the previous file on any failure
        print(f"[fetch_youtube] failed: {e}; keeping existing {OUT.name}")
        return 0

    videos = []
    for entry in root.findall("a:entry", NS):
        vid = entry.findtext("yt:videoId", namespaces=NS)
        if not vid:
            continue
        group = entry.find("media:group", NS)
        desc = (group.findtext("media:description", default="", namespaces=NS) if group is not None else "").strip()
        videos.append({
            "id": vid,
            "title": entry.findtext("a:title", default="", namespaces=NS).strip(),
            "published": entry.findtext("a:published", default="", namespaces=NS)[:10],
            "description": desc.split("\n")[0][:200],
            "shorts": "/shorts/" in (entry.find("a:link", NS).get("href", "") if entry.find("a:link", NS) is not None else ""),
        })

    if not videos:
        print("[fetch_youtube] no videos found; keeping existing file")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(videos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[fetch_youtube] wrote {len(videos)} videos to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
