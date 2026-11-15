#!/usr/bin/env python3
"""Feed 06 — Jobicy remote jobs via public API (credit + link-back required by their terms; the site links every source)."""
import sys
from common import collect, fetch_json

SOURCE = "https://jobicy.com/api/v2/remote-jobs"

d = fetch_json(SOURCE + "?count=50")
jobs = [{
    "title": j.get("jobTitle"),
    "org": j.get("companyName"),
    "location": j.get("jobGeo"),
    "detail": (j.get("jobLevel") or None) or (", ".join(j.get("jobType") or []) or None),
    "url": j.get("url"),
} for j in d.get("jobs", [])]
sys.exit(collect("jobicy", "Jobicy — remote jobs", "jobs", SOURCE, jobs, min_items=15))
