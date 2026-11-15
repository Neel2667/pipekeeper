#!/usr/bin/env python3
"""Feed 05 — Working Nomads remote jobs via public API."""
import sys
from common import collect, fetch_json

SOURCE = "https://www.workingnomads.com/api/exposed_jobs/"

jobs = fetch_json(SOURCE)
out = []
for j in jobs:
    out.append({
        "title": j.get("title"),
        "org": j.get("company_name") or j.get("company"),
        "location": j.get("location"),
        "detail": j.get("category_name") or (", ".join(j.get("category_labels", "").split(",")) or None) if isinstance(j.get("category_labels"), str) else j.get("category_name"),
        "url": j.get("url"),
    })
sys.exit(collect("workingnomads", "Working Nomads — remote jobs", "jobs", SOURCE, out, min_items=15))
