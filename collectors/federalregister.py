#!/usr/bin/env python3
"""
Feed 14 — Federal Register: the newest US federal documents (rules, notices,
proposed rules) — keyless, public-domain. Compliance-change signal feed.
"""
import sys
from common import collect, fetch_json

SOURCE = "https://www.federalregister.gov"

d = fetch_json(SOURCE + "/api/v1/documents.json?per_page=100&order=newest")
jobs = []
for r in d.get("results", []):
    agency = ", ".join(a.get("name", "") for a in (r.get("agencies") or [])[:2]) or None
    jobs.append({
        "title": r.get("title"),
        "org": agency,
        "location": None,
        "detail": f"{r.get('type', '')} · published {r.get('publication_date', '')}".strip(),
        "url": r.get("html_url"),
    })
sys.exit(collect("federalregister", "Federal Register — newest federal documents", "government",
                 SOURCE, jobs, min_items=80))
