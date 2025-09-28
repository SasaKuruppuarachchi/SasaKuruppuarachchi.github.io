#!/usr/bin/env python3
"""
Create a boilerplate Jekyll post file.

Usage:
  python3 scripts/new_post.py --title "My Post Title" --date 2025-09-27 \
      [--categories "Cat1,Cat2"] [--tags "tag1,tag2"] [--cover "/path/img.jpg"] \
      [--abstract "Short abstract..."] [--force]

This generates _posts/YYYY-MM-DD-my-post-title.html with front matter and a stub body.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"


def slugify(title: str) -> str:
    s = title.strip().lower()
    # Replace apostrophes and unicode dashes first
    s = s.replace("'", "")
    s = re.sub(r"[\u2013\u2014\u2012]", "-", s)
    # Replace non-alphanumeric with hyphens
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s)
    # Trim hyphens
    s = s.strip("-")
    return s or "post"


def parse_date(date_str: str) -> dt.datetime:
    # Accept YYYY-MM-DD or full datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            d = dt.datetime.strptime(date_str, fmt)
            if fmt == "%Y-%m-%d":
                # default time noon to keep order stable
                d = d.replace(hour=12, minute=0, second=0)
            return d
        except ValueError:
            continue
    raise ValueError("Date must be in YYYY-MM-DD or 'YYYY-MM-DD HH:MM[:SS]' format")


def as_yaml_list(csv: str | None) -> List[str]:
    if not csv:
        return []
    return [x.strip() for x in csv.split(',') if x.strip()]


def next_available_filename(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    stem = base_path.stem
    suffix = base_path.suffix
    m = re.match(r"^(.*?)-(\d+)$", stem)
    base_stem = m.group(1) if m else stem
    n = int(m.group(2)) if m else 1
    while True:
        n += 1
        candidate = base_path.with_name(f"{base_stem}-{n}{suffix}")
        if not candidate.exists():
            return candidate


def build_front_matter(title: str, d: dt.datetime, categories: List[str], tags: List[str], cover: str | None, abstract: str | None,
                       status: str = "Finished", visibility: str = "Published") -> str:
    def dq(s: str) -> str:
        # wrap in double quotes and escape internal quotes for YAML inline list
        return '"' + s.replace('"', '\\"') + '"'

    # Build YAML front matter
    cats_str = ", ".join(dq(c) for c in categories) if categories else ""
    tags_str = ", ".join(dq(t) for t in tags) if tags else ""
    lines = [
        "---",
        "layout: post",
        f"title: \"{title}\"",
        f"date: {d.strftime('%Y-%m-%d %H:%M:%S')}",
        f"categories: [{cats_str}]",
        f"tags: [{tags_str}]",
        f"status: {status}",
        f"visibility: {visibility}",
    ]
    if cover:
        lines.append(f"cover: \"{cover}\"")
    if abstract:
        lines.append(f"abstract: \"{abstract}\"")
    lines.append("---\n")
    return "\n".join(lines)


def build_body_stub() -> str:
    return (
        "\n"
        "<!-- Cover image (optional) -->\n"
        "<!-- <div class=\"wp-block-image\"><figure><img src=\"/assets/media/YYYY/MM/cover.jpg\" alt=\"\" data-cover class=\"wp-image-xxx\" /></figure></div> -->\n\n"
        "<p>Write your post content here.</p>\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Create a new Jekyll post boilerplate")
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD or 'YYYY-MM-DD HH:MM[:SS]')")
    parser.add_argument("--categories", help="Comma-separated categories", default=None)
    parser.add_argument("--tags", help="Comma-separated tags", default=None)
    parser.add_argument("--cover", help="Cover image URL (optional)", default=None)
    parser.add_argument("--abstract", help="Short abstract (optional)", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite if file exists by adding a numeric suffix")
    parser.add_argument("--status", default="Finished", choices=["Finished", "Ongoing"], help="Post status")
    parser.add_argument("--visibility", default="Published", choices=["Published", "Unlisted"], help="Post visibility")
    args = parser.parse_args()

    try:
        d = parse_date(args.date)
    except ValueError as e:
        raise SystemExit(str(e))

    title = args.title.strip()
    slug = slugify(title)
    filename = f"{d.strftime('%Y-%m-%d')}-{slug}.html"

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / filename
    if args.force and path.exists():
        path = next_available_filename(path)
    elif path.exists():
        # Without --force, still avoid clobber: choose next available
        path = next_available_filename(path)

    front_matter = build_front_matter(
        title=title,
        d=d,
        categories=as_yaml_list(args.categories),
        tags=as_yaml_list(args.tags),
        cover=args.cover,
        abstract=args.abstract,
        status=args.status,
        visibility=args.visibility,
    )
    body = build_body_stub()

    content = front_matter + body
    path.write_text(content, encoding="utf-8")

    rel = os.path.relpath(path, ROOT)
    print(f"Created: {rel}")


if __name__ == "__main__":
    main()
