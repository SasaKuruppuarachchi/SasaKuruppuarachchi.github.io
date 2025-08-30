#!/usr/bin/env python3
import json, re, sys, time
from pathlib import Path
try:
    import requests
except ImportError:
    print('requests module required', file=sys.stderr)
    sys.exit(1)

USER_ID = '4hBNIx8AAAAJ'
BASE = 'https://scholar.google.com/citations'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}

def fetch():
    # Basic public profile publications page
    url = f"{BASE}?hl=en&user={USER_ID}&view_op=list_works&sortby=pubdate"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text
    # Each publication row starts with <tr class="gsc_a_tr">
    rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', html, re.DOTALL)
    pubs = []
    for row in rows:
        # title
        title_match = re.search(r'class="gsc_a_at">(.*?)</a>', row)
        title = re.sub('<.*?>', '', title_match.group(1)).strip() if title_match else 'Untitled'
        # link
        link_match = re.search(r'<a href="(/citations\?view_op=view_citation[^"]+)"', row)
        link = 'https://scholar.google.com' + link_match.group(1) if link_match else None
        # authors and venue appear in sibling divs when you fetch details page; limited on list, but snippet contains authors+venue in a span
        # We'll fetch snippet via data-content attribute
        snippet = ''
        snippet_match = re.search(r'class="gsc_a_at"[^>]*data-href="[^"]*"[^>]*>(.*?)</a>.*?<div class="gs_gray">(.*?)</div>.*?<div class="gs_gray">(.*?)</div>', row, re.DOTALL)
        authors = venue = ''
        year = ''
        if snippet_match:
            authors = re.sub('<.*?>', '', snippet_match.group(2)).strip()
            venue = re.sub('<.*?>', '', snippet_match.group(3)).strip()
        # year
        year_match = re.search(r'class="gsc_a_h gsc_a_hc gs_ibl">(\d{4})</span>', row)
        if not year_match:
            year_match = re.search(r'class="gsc_a_y">\s*<span class="gsc_a_h gsc_a_hc gs_ibl">(\d{4})</span>', row)
        if year_match:
            year = year_match.group(1)
        pubs.append({
            'title': title,
            'url': link,
            'authors': authors,
            'venue': venue,
            'year': year
        })
    return pubs

def main():
    out_path = Path(__file__).parent.parent / 'data' / 'publications.json'
    pubs = fetch()
    # Keep only first 100 to limit size
    pubs = pubs[:100]
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(pubs, f, ensure_ascii=False, indent=2)
    print(f'Wrote {len(pubs)} publications to {out_path}')

if __name__ == '__main__':
    main()
