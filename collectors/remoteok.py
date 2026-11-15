#!/usr/bin/env python3
"""
Feed 02 — RemoteOK remote tech jobs via their public API.
RemoteOK's API terms require a link back with credit; the site's feed panel
links the source for every record, satisfying attribution.
"""
import sys
from common import collect, fetch_json

SOURCE = "https://remoteok.com/api"

items = fetch_json(SOURCE)
jobs = []
for j in items:
    if not isinstance(j, dict) or "position" not in j:
        continue  # first element is the legal notice
    salary = None
    if j.get("salary_min") and j.get("salary_max"):
        salary = f"${int(j['salary_min']):,}–${int(j['salary_max']):,}"
    jobs.append({
        "title": j.get("position"),
        "org": j.get("company"),
        "location": j.get("location") or "remote",
        "detail": salary or (", ".join((j.get("tags") or [])[:3]) or None),
        "url": j.get("url"),
    })
sys.exit(collect("remoteok", "RemoteOK — remote tech jobs", "jobs", SOURCE, jobs, min_items=20))
