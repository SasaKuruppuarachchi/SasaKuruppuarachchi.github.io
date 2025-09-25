#!/usr/bin/env python3
"""
Import WordPress WXR (XML) into Jekyll _posts/*.html files.

- Reads the export XML path from argv[1] or uses default under 'lagacy/*.xml'.
- Generates files as _posts/YYYY-MM-DD-slug.html with front matter:
  layout: post, title, date, categories, tags, permalink.
-
Media mapping:
  Any src/href pointing to '.../wp-content/uploads/...' will be rewritten to '/assets/media/...'.

Limitations:
  - Only 'post' items with status 'publish' are imported.
  - Keeps HTML content intact besides a few WP block wrappers removal.
"""
from __future__ import annotations
import os
import re
import sys
import html
import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\-\s]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value or "post"


def wp_to_jekyll_date(s: str) -> dt.datetime:
    # s examples: '2016-07-06 16:43:29'
    try:
        return dt.datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt.datetime.utcnow()


def rewrite_media_urls(html_text: str) -> str:
    # Map wordpress uploads to local assets/media
    def repl(m):
        url = m.group(1)
        # Extract the /wp-content/uploads/... tail
        i = url.find("/wp-content/uploads/")
        if i != -1:
            tail = url[i + len("/wp-content/uploads/"):]
            return f'="/assets/media/{tail}"'
        return m.group(0)

    html_text = re.sub(r'="(https?:[^"\s]+)"', repl, html_text)
    return html_text


def clean_wp_blocks(content: str) -> str:
    # Remove Gutenberg comment wrappers and Jetpack tiled-gallery wrappers while keeping inner HTML
    content = re.sub(r"<!--\s*/?wp:[^>]*-->\n?", "", content)
    # Remove common div wrappers used by jetpack galleries but keep inner img tags
    content = re.sub(r"<div class=\"wp-block-jetpack-tiled-gallery[\s\S]*?>", "", content)
    content = content.replace("</div></div></div>", "")
    # Centered figures -> keep figure/img; theme CSS will handle alignment
    content = content.replace("class=\"aligncenter\"", "")
    return content


def extract_text(elem: ET.Element, name: str, namespace: str | None = None) -> str:
    if namespace:
        child = elem.find(f"{namespace}{name}")
    else:
        child = elem.find(name)
    if child is None:
        return ""
    return child.text or ""


def import_wordpress(xml_path: Path) -> int:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {
        'content': '{http://purl.org/rss/1.0/modules/content/}',
        'wp': '{http://wordpress.org/export/1.2/}',
        'dc': '{http://purl.org/dc/elements/1.1/}',
    }

    channel = root.find('channel')
    if channel is None:
        raise RuntimeError("Invalid WXR: missing channel")

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for item in channel.findall('item'):
        post_type = extract_text(item, 'post_type', ns['wp'])
        status = extract_text(item, 'status', ns['wp'])
        if post_type != 'post' or status != 'publish':
            continue

        title = extract_text(item, 'title')
        slug = extract_text(item, 'post_name', ns['wp']) or slugify(title)
        date_s = extract_text(item, 'post_date', ns['wp'])
        date = wp_to_jekyll_date(date_s)
        guid = extract_text(item, 'guid')

        # categories and tags
        cats = []
        tags = []
    for cat in item.findall('category'):
            domain = cat.get('domain', '')
            name = (cat.text or '').strip()
            if not name:
                continue
            if domain == 'category':
                cats.append(name)
            elif domain == 'post_tag':
                tags.append(name)

    content_html = extract_text(item, 'encoded', ns['content'])
    content_html = html.unescape(content_html)
    content_html = clean_wp_blocks(content_html)
    content_html = rewrite_media_urls(content_html)

    # Determine cover image from first <img src="...">
    m = re.search(r'<img[^>]+src="([^"]+)"', content_html, re.IGNORECASE)
    cover = m.group(1) if m else ""

    # Build front matter
    safe_title = (title or "").replace('"', '\\"')
    front_matter = [
            '---',
            'layout: post',
            f'title: "{safe_title}"',
            f'date: {date.strftime("%Y-%m-%d %H:%M:%S %z").strip() or date.strftime("%Y-%m-%d %H:%M:%S")}',
        ]
        if cats:
            front_matter.append('categories: [' + ', '.join(f'"{c}"' for c in cats) + ']')
        if tags:
            front_matter.append('tags: [' + ', '.join(f'"{t}"' for t in tags) + ']')
        if guid:
            front_matter.append(f'original_url: "{guid}"')
        if cover:
            front_matter.append(f'cover: "{cover}"')
        front_matter.append('---')

        body = "\n".join(front_matter) + "\n\n" + content_html.strip() + "\n"

        filename = f"{date.strftime('%Y-%m-%d')}-{slug}.html"
        out_path = POSTS_DIR / filename
        out_path.write_text(body, encoding='utf-8')
        count += 1

    return count


def main():
    xml_arg = None
    if len(sys.argv) > 1:
        xml_arg = Path(sys.argv[1])
    else:
        xml_arg = None
    if not xml_arg or not xml_arg.exists():
        print("WordPress export XML not found. Provide path as argument.")
        sys.exit(1)

    count = import_wordpress(xml_arg)
    print(f"Imported {count} posts from {xml_arg.name}")


if __name__ == '__main__':
    main()
