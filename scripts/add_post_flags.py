#!/usr/bin/env python3
"""
Add status and visibility fields to all Jekyll posts.

Fields:
  - status: Finished | Ongoing
  - visibility: Published | Unlisted

Usage:
  python3 scripts/add_post_flags.py                 # dry-run with defaults
  python3 scripts/add_post_flags.py --write         # write defaults to files
  python3 scripts/add_post_flags.py --status Ongoing --visibility Unlisted --write

Notes:
  - Skips files without front matter.
  - Won't overwrite existing keys unless --force is provided.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "_posts")

ALLOWED_STATUS = {"Finished", "Ongoing"}
ALLOWED_VISIBILITY = {"Published", "Unlisted"}


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


def has_key(front_matter: str, key: str) -> bool:
    k = key.lower() + ":"
    for raw in front_matter.splitlines():
        line = raw.strip().lower()
        if line.startswith(k):
            return True
    return False


def set_or_append(front_matter: str, key: str, value: str, force: bool = False) -> str:
    lines = front_matter.splitlines()
    key_lower = key.lower()
    replaced = False
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.lower().startswith(key_lower + ":"):
            if force:
                lines[i] = f"{key}: {value}"
            replaced = True
            break
    if not replaced and not has_key(front_matter, key):
        if front_matter and not front_matter.endswith("\n"):
            front_matter += "\n"
        front_matter += f"{key}: {value}\n"
        return front_matter
    return "\n".join(lines) + ("\n" if front_matter.endswith("\n") else "")


def process_file(path: str, status: str, visibility: str, write: bool, force: bool, verbose: bool) -> bool:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    rng = find_front_matter_sections(text)
    if not rng:
        if verbose:
            print(f"[skip] No front matter: {os.path.relpath(path, ROOT)}")
        return False
    start, end = rng
    fm = text[start:end]
    orig_fm = fm
    fm = set_or_append(fm, 'status', status, force=force)
    fm = set_or_append(fm, 'visibility', visibility, force=force)
    if fm == orig_fm:
        if verbose:
            print(f"[skip] Already has keys: {os.path.relpath(path, ROOT)}")
        return False
    new_text = text[:start] + fm + text[end:]
    if write:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
    print(("[write] " if write else "[plan] ") + f"{os.path.relpath(path, ROOT)} -> status={status}, visibility={visibility}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--status', default='Finished', help='Finished or Ongoing')
    ap.add_argument('--visibility', default='Published', help='Published or Unlisted')
    ap.add_argument('--write', action='store_true', help='Write changes to files')
    ap.add_argument('--force', action='store_true', help='Overwrite existing values')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    status = args.status.strip().capitalize()
    visibility = args.visibility.strip().capitalize()
    if status not in ALLOWED_STATUS:
        print(f"Invalid --status '{args.status}'. Allowed: {sorted(ALLOWED_STATUS)}", file=sys.stderr)
        sys.exit(2)
    if visibility not in ALLOWED_VISIBILITY:
        print(f"Invalid --visibility '{args.visibility}'. Allowed: {sorted(ALLOWED_VISIBILITY)}", file=sys.stderr)
        sys.exit(2)

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
        if process_file(path, status, visibility, args.write, args.force, args.verbose):
            updated += 1
    print(f"Done. Scanned: {total}, Updated: {updated}")


if __name__ == '__main__':
    main()
