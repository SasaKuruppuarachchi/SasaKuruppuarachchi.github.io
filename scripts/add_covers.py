#!/usr/bin/env python3
"""
Add `cover: "..."` to each Jekyll post's front matter by selecting:
  1) First <img> with data-cover or data-thumb in body, else
  2) First <img src="..."> in body.

Skips files that already have a non-empty `cover:`.

Usage:
  python3 scripts/add_covers.py            # dry-run, prints planned changes
  python3 scripts/add_covers.py --write    # write changes to disk
  python3 scripts/add_covers.py --verbose  # more logs
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from typing import Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")

IMG_WITH_MARK_RE = re.compile(r"<img[^>]*(?:data-cover|data-thumb)[^>]*>", re.I | re.S)
IMG_SRC_RE = re.compile(r"src=[\"']([^\"']+)[\"']", re.I)
FIRST_IMG_WITH_SRC_RE = re.compile(r"<img[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.I | re.S)


def find_front_matter_sections(text: str) -> Optional[Tuple[int, int]]:
    """Return (start_idx, end_idx) of the front matter block (exclusive of markers), or None.
    We expect a file starting with a line '---' and ending front matter at the next line '---'.
    """
    if not text.startswith("---"):
        return None
    # Split into lines keeping ends to compute indices
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].strip().startswith("---"):
        return None
    # Find closing '---'
    fm_end_line_idx = None
    for i in range(1, min(len(lines), 500)):  # front matter shouldn't be huge
        if lines[i].strip().startswith('---'):
            fm_end_line_idx = i
            break
    if fm_end_line_idx is None:
        return None
    # Compute indices in original text
    start_idx = len(lines[0])  # after first '---' line
    end_idx = sum(len(l) for l in lines[:fm_end_line_idx])  # start of closing '---' line
    return start_idx, end_idx


def extract_body(text: str) -> str:
    rng = find_front_matter_sections(text)
    if not rng:
        return text
    _, end = rng
    # Find end of closing '---' line
    lines = text.splitlines(keepends=True)
    # Recompute closing line idx
    closing_idx = 0
    seen = 0
    for i, l in enumerate(lines):
        seen += len(l)
        if seen > end:
            closing_idx = i
            break
    body = ''.join(lines[closing_idx+1:])
    return body


def has_cover_in_front_matter(front_matter: str) -> bool:
    # Simple check: line starting with 'cover:' and non-empty value after colon
    for raw in front_matter.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.lower().startswith('cover:'):
            # If something after colon
            return bool(line.split(':', 1)[1].strip())
    return False


def compute_cover_from_body(body: str) -> Optional[str]:
    # 1) Find first marked image tag
    m = IMG_WITH_MARK_RE.search(body)
    if m:
        tag = m.group(0)
        msrc = IMG_SRC_RE.search(tag)
        if msrc:
            return msrc.group(1)
    # 2) Fallback: first image with src
    m = FIRST_IMG_WITH_SRC_RE.search(body)
    if m:
        return m.group(1)
    return None


def insert_cover(front_matter: str, cover_url: str) -> str:
    # Insert before the closing '---' line; but we only have the inner FM here.
    # We'll append a new line 'cover: "..."' at the end, preserving trailing newline if present in FM.
    trailing_nl = "\n" if front_matter.endswith("\n") else ""
    if front_matter and not front_matter.endswith("\n"):
        front_matter = front_matter + "\n"
    front_matter += f'cover: "{cover_url}"\n'
    # Remove double trailing empty lines
    return front_matter.rstrip("\n") + trailing_nl


def process_file(path: str, write: bool = False, verbose: bool = False) -> Tuple[bool, Optional[str]]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    rng = find_front_matter_sections(text)
    if not rng:
        if verbose:
            print(f"[skip] No front matter: {os.path.relpath(path, ROOT)}")
        return False, None
    start, end = rng
    fm = text[start:end]
    if has_cover_in_front_matter(fm):
        if verbose:
            print(f"[skip] Cover exists: {os.path.relpath(path, ROOT)}")
        return False, None
    body = extract_body(text)
    cover = compute_cover_from_body(body)
    if not cover:
        if verbose:
            print(f"[skip] No image found: {os.path.relpath(path, ROOT)}")
        return False, None
    new_fm = insert_cover(fm, cover)
    new_text = text[:start] + new_fm + text[end:]
    if write:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
    rel = os.path.relpath(path, ROOT)
    print(("[write] " if write else "[plan] ") + f"{rel} -> cover: {cover}")
    return True, cover


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='Write changes to files')
    ap.add_argument('--verbose', action='store_true', help='Verbose logs')
    args = ap.parse_args()

    if not os.path.isdir(POSTS_DIR):
        print(f"No _posts directory found at {POSTS_DIR}", file=sys.stderr)
        sys.exit(1)

    total = 0
    changed = 0
    updated = 0

    for name in sorted(os.listdir(POSTS_DIR)):
        if not (name.endswith('.html') or name.endswith('.md') or name.endswith('.markdown')):
            continue
        total += 1
        path = os.path.join(POSTS_DIR, name)
        did, _ = process_file(path, write=args.write, verbose=args.verbose)
        changed += 1 if did else 0

    print(f"Done. Scanned: {total}, Updated: {changed}")


if __name__ == '__main__':
    main()
