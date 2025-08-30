#!/usr/bin/env python3
"""Fetch publications from the public ORCID API and update data/publications.json.

The script is intentionally conservative:
 - It never overwrites the existing file with an empty list.
 - It de‑duplicates works by title/DOI.
 - It keeps only lightweight summary data (title, url, authors, venue, year).
 - Authors: ORCID work summary responses do not include contributor names; to
   avoid n extra API calls we default to the profile owner name unless the
   detailed record is fetched (set ORCID_FETCH_DETAILS=1 to enable). When
   detailed fetch is enabled we resolve contributor names for each work.

Environment variables:
  ORCID_ID (optional) override the hardcoded ORCID id.
  ORCID_FETCH_DETAILS=1 to fetch each work's detail for authors (slower).

References:
  ORCID Public API (no auth needed for public data):
    GET https://pub.orcid.org/v3.0/{orcid}/record
    GET https://pub.orcid.org/v3.0/{orcid}/work/{putCode}
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests

DEFAULT_ORCID = "0000-0002-4530-8725"
BASE = "https://pub.orcid.org/v3.0"
HEADERS = {"Accept": "application/json", "User-Agent": "orcid-fetch-script/1.0"}

# Simple venue normalization mapping (can expand later)
VENUE_MAP = {
    "aiaa scitech 2024 forum": "AIAA SciTech 2024 Forum",
    "lecture notes in computer science": "Lecture Notes in Computer Science",
    # Korean venues – leave as-is but ensure consistent spacing (examples only)
}


def _norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _normalize_venue(raw: str) -> str:
    if not raw:
        return ""
    key = _norm_space(raw).lower()
    return VENUE_MAP.get(key, _norm_space(raw))


def _extract_year(date_obj: Optional[dict]) -> str:
    if not isinstance(date_obj, dict):
        return ""
    year = date_obj.get("year") or {}
    return str(year.get("value") or "")


def _fetch_json(url: str) -> Optional[dict]:
    r = requests.get(url, headers=HEADERS, timeout=40)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} for {url}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Invalid JSON from {url}: {e}") from e


def fetch_summary(orcid_id: str) -> List[dict]:
    """Fetch the full ORCID record and extract work summaries.

    Returns a list of dicts with the minimal fields; authors may remain owner only.
    """
    record_url = f"{BASE}/{orcid_id}/record"
    data = _fetch_json(record_url)
    works = (
        data.get("activities-summary", {})
        .get("works", {})
        .get("group", [])
    )
    results: List[Dict[str, str]] = []
    for group in works:
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        ws = summaries[0]
        title_obj = ((ws.get("title") or {}).get("title") or {})
        title = _norm_space(title_obj.get("value") or "Untitled")
        journal_title = (ws.get("journal-title") or {}).get("value") or ""
        pub_date = ws.get("publication-date")
        year = _extract_year(pub_date)
        put_code = ws.get("put-code")
        external_ids = ((ws.get("external-ids") or {}).get("external-id") or [])
        doi = ""
        url: Optional[str] = None
        for ext in external_ids:
            etype = (ext.get("external-id-type") or "").lower()
            if etype == "doi":
                doi = (ext.get("external-id-value") or "").strip()
                doi_clean = re.sub(r"^doi:\s*", "", doi, flags=re.I)
                if doi_clean:
                    url = f"https://doi.org/{doi_clean}"
                break
        if not url and put_code:
            # ORCID UI link fallback
            url = f"https://orcid.org/{orcid_id}/work/{put_code}"

        # Year inference heuristic if missing: look in DOI or title / venue for a 20xx pattern
        if not year:
            search_sources = [doi, title, journal_title]
            for src in search_sources:
                if not src:
                    continue
                m = re.search(r"(20\d{2})", src)
                if m:
                    year = m.group(1)
                    break

        # Normalize venue capitalization
        norm_venue = _normalize_venue(journal_title)
        results.append(
            {
                "title": title,
                "url": url,
                "doi": (f"https://doi.org/{doi}" if doi else (url if url and url.startswith("https://doi.org/") else "")),
                "authors": "Sasanka Kuruppu Arachchige",  # default; may be replaced
                "venue": norm_venue,
                "year": year,
                "_put_code": put_code,
            }
        )
    return results


def enrich_authors(orcid_id: str, pubs: List[dict]) -> None:
    if not pubs:
        return
    for pub in pubs:
        put_code = pub.get("_put_code")
        if not put_code:
            continue
        try:
            detail = _fetch_json(f"{BASE}/{orcid_id}/work/{put_code}")
        except Exception:
            continue
        contributors = (
            (detail.get("contributors") or {}).get("contributor") or []
        )
        names = []
        for c in contributors:
            n = ((c.get("credit-name") or {}).get("value")) or (
                (c.get("contributor-orcid") or {}).get("path")
            )
            if n:
                names.append(n)
        if names:
            pub["authors"] = ", ".join(names)


def dedupe(pubs: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for p in pubs:
        key = (p.get("title", "").lower(), p.get("url") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def main() -> None:
    orcid_id = os.environ.get("ORCID_ID", DEFAULT_ORCID).strip()
    fetch_details = os.environ.get("ORCID_FETCH_DETAILS") == "1"
    out_path = Path(__file__).parent.parent / "data" / "publications.json"
    try:
        pubs = fetch_summary(orcid_id)
        if fetch_details:
            enrich_authors(orcid_id, pubs)
    except Exception as e:  # noqa: BLE001
        print(f"[fetch_orcid] Skipped update: {e}", file=sys.stderr)
        return
    pubs = dedupe(pubs)
    if not pubs:
        print("[fetch_orcid] No publications found; keeping existing file.")
        return
    # Strip internal keys & clean empty fields
    for p in pubs:
        p.pop("_put_code", None)
        if not p.get("doi"):
            p.pop("doi", None)
    # Prefer newest first (year desc) then title
    pubs.sort(key=lambda x: (int(x.get("year") or 0), x.get("title") or ""), reverse=True)
    # Limit size just in case
    pubs = pubs[:200]
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(pubs, f, ensure_ascii=False, indent=2)
    print(f"[fetch_orcid] Wrote {len(pubs)} publications to {out_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
