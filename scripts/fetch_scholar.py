#!/usr/bin/env python3
"""Fetch publications from Google Scholar and write data/publications.json.

Limitations: Direct scraping often triggers a CAPTCHA. If a CAPTCHA or block is
detected we skip updating (keeping the previous file). This keeps the static
fallback on the site intact. Consider replacing with a manually maintained
BibTeX/JSON list or an external service (e.g. Publish or Perish export) for
reliability.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Dict

import requests

BASE = "https://scholar.google.com/citations"
# User id provided by user request
USER_ID = "4hBNIx8AAAAJ"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def parse_publications(html: str) -> List[Dict[str, str]]:
    """Very lightweight regex-based extraction of the first page of works."""
    rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', html, re.DOTALL)
    pubs: List[Dict[str, str]] = []
    for row in rows:
        title_match = re.search(r'class="gsc_a_at">(.*?)</a>', row)
        title = re.sub('<.*?>', '', title_match.group(1)).strip() if title_match else 'Untitled'
        link_match = re.search(r'<a href="(/citations\?view_op=view_citation[^"]+)"', row)
        link = 'https://scholar.google.com' + link_match.group(1) if link_match else None
        authors = ''
        venue = ''
        snippet_match = re.search(
            r'class="gsc_a_at"[^>]*>(.*?)</a>.*?<div class="gs_gray">(.*?)</div>.*?<div class="gs_gray">(.*?)</div>',
            row,
            re.DOTALL,
        )
        if snippet_match:
            authors = re.sub('<.*?>', '', snippet_match.group(2)).strip()
            venue = re.sub('<.*?>', '', snippet_match.group(3)).strip()
        year = ''
        year_match = re.search(r'class="gsc_a_h gsc_a_hc gs_ibl">(\d{4})</span>', row) or re.search(
            r'class="gsc_a_y">\s*<span class="gsc_a_h gsc_a_hc gs_ibl">(\d{4})</span>', row
        )
        if year_match:
            year = year_match.group(1)
        pubs.append(
            {
                'title': title,
                'url': link,
                'authors': authors,
                'venue': venue,
                'year': year,
            }
        )
    return pubs


def fetch() -> List[Dict[str, str]]:
    url = f"{BASE}?hl=en&user={USER_ID}&view_op=list_works&sortby=pubdate&cstart=0&pagesize=100"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text
    if 'gs_captcha_f' in html or "not a robot" in html:
        raise RuntimeError("Blocked by Google Scholar CAPTCHA – manual intervention required.")
    return parse_publications(html)


def main():
    out_path = Path(__file__).parent.parent / 'data' / 'publications.json'
    try:
        pubs = fetch()
    except Exception as e:  # noqa: BLE001 keep broad to avoid overwrites
        print(f'[fetch_scholar] Skipped update: {e}', file=sys.stderr)
        return
    if not pubs:
        print('[fetch_scholar] Parsed 0 publications; keeping existing file.')
        return
    pubs = pubs[:100]
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(pubs, f, ensure_ascii=False, indent=2)
    print(f'[fetch_scholar] Wrote {len(pubs)} publications to {out_path}')


if __name__ == '__main__':  # pragma: no cover
    main()
