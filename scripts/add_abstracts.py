#!/usr/bin/env python3
"""
Generate a short abstract (1–2 sentences) for each post and add it to front matter.
Strategy:
  - If 'abstract:' already exists and is non-empty, skip.
  - Prefer the first <p>...</p> block (HTML), else use the beginning of body text.
  - Strip HTML, normalize whitespace.
  - Split into sentences (., !, ?). Take 1–2 sentences up to ~300 chars.
  - Ensure it ends with punctuation.

Usage:
  python3 scripts/add_abstracts.py            # dry-run
  python3 scripts/add_abstracts.py --write    # write changes
  python3 scripts/add_abstracts.py --verbose  # verbose logs
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from html import unescape
from typing import Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")

P_TAG_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.!?])\s+")


def find_front_matter_sections(text: str) -> Optional[Tuple[int, int]]:
    if not text.startswith("---"):
        return None
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].strip().startswith("---"):
        return None
    fm_end_line_idx = None
    for i in range(1, min(len(lines), 500)):
        if lines[i].strip().startswith('---'):
            fm_end_line_idx = i
            break
    if fm_end_line_idx is None:
        return None
    start_idx = len(lines[0])
    end_idx = sum(len(l) for l in lines[:fm_end_line_idx])
    return start_idx, end_idx


def extract_body(text: str) -> str:
    rng = find_front_matter_sections(text)
    if not rng:
        return text
    _, end = rng
    lines = text.splitlines(keepends=True)
    closing_idx = 0
    seen = 0
    for i, l in enumerate(lines):
        seen += len(l)
        if seen > end:
            closing_idx = i
            break
    return ''.join(lines[closing_idx+1:])


def has_nonempty_key(front_matter: str, key: str) -> bool:
    key_lower = key.lower()
    for raw in front_matter.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.lower().startswith(key_lower + ':'):
            return bool(line.split(':', 1)[1].strip())
    return False


def clean_text(html: str) -> str:
    # Remove scripts/styles quickly
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    # Strip tags
    text = TAG_RE.sub(' ', html)
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_abstract_from_body(body_html: str, max_chars: int = 300) -> Optional[str]:
    para = None
    m = P_TAG_RE.search(body_html)
    if m:
        para = m.group(1)
    else:
        # fallback: first ~800 chars of body
        para = body_html[:800]
    text = clean_text(para)
    if not text:
        return None
    # Split into sentences
    parts = SENTENCE_SPLIT_RE.split(text)
    # Filter out very short bits
    parts = [p.strip() for p in parts if len(p.strip().split()) >= 3]
    if not parts:
        parts = [text]
    abstract = parts[0]
    if len(abstract) < max_chars and len(parts) > 1:
        candidate = abstract + ' ' + parts[1]
        if len(candidate) <= max_chars:
            abstract = candidate
    # Trim to max_chars without cutting mid-word
    if len(abstract) > max_chars:
        cut = abstract[:max_chars]
        cut = cut.rsplit(' ', 1)[0]
        abstract = cut
    # Ensure ending punctuation
    if abstract and abstract[-1] not in '.!?':
        abstract += '.'
    return abstract


def insert_key(front_matter: str, key: str, value: str) -> str:
    trailing_nl = "\n" if front_matter.endswith("\n") else ""
    if front_matter and not front_matter.endswith("\n"):
        front_matter = front_matter + "\n"
    safe = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
    front_matter += f'{key}: "{safe}"\n'
    return front_matter.rstrip("\n") + trailing_nl


def process_file(path: str, write: bool = False, verbose: bool = False) -> bool:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    rng = find_front_matter_sections(text)
    if not rng:
        if verbose:
            print(f"[skip] No front matter: {os.path.relpath(path, ROOT)}")
        return False
    start, end = rng
    fm = text[start:end]
    if has_nonempty_key(fm, 'abstract'):
        if verbose:
            print(f"[skip] Abstract exists: {os.path.relpath(path, ROOT)}")
        return False
    body_html = extract_body(text)
    abstract = make_abstract_from_body(body_html)
    if not abstract:
        if verbose:
            print(f"[skip] No text found: {os.path.relpath(path, ROOT)}")
        return False
    new_fm = insert_key(fm, 'abstract', abstract)
    new_text = text[:start] + new_fm + text[end:]
    if write:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
    rel = os.path.relpath(path, ROOT)
    print(("[write] " if write else "[plan] ") + f"{rel} -> abstract: {abstract[:80]}{'…' if len(abstract)>80 else ''}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    if not os.path.isdir(POSTS_DIR):
        print(f"No _posts directory found at {POSTS_DIR}", file=sys.stderr)
        sys.exit(1)

    total = 0
    updated = 0
    for name in sorted(os.listdir(POSTS_DIR)):
        if not (name.endswith('.html') or name.endswith('.md') or name.endswith('.markdown')):
            continue
        total += 1
        path = os.path.join(POSTS_DIR, name)
        if process_file(path, write=args.write, verbose=args.verbose):
            updated += 1
    print(f"Done. Scanned: {total}, Updated: {updated}")


if __name__ == '__main__':
    main()
