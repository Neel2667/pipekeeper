#!/usr/bin/env python3
"""Feed 07 — Himalayas remote jobs via public API."""
import sys
from common import collect, fetch_json

SOURCE = "https://himalayas.app/jobs/api"

d = fetch_json(SOURCE + "?limit=50")
jobs = []
for j in d.get("jobs", []):
    sal = None
    if j.get("minSalary"):
        period = j.get("salaryPeriod") or ""
        sal = f"${int(j['minSalary']):,}" + (f"–${int(j['maxSalary']):,}" if j.get("maxSalary") else "")
        sal += f"/{period[0]}" if period else ""
    loc = ", ".join(j.get("locationRestrictions") or []) or "remote"
    jobs.append({
        "title": j.get("title"),
        "org": j.get("companyName"),
        "location": loc,
        "detail": sal or j.get("employmentType"),
        "url": f"https://himalayas.app/jobs/{j.get('companySlug')}/{j.get('slug')}" if j.get("slug") else None,
    })
sys.exit(collect("himalayas", "Himalayas — remote jobs", "jobs", SOURCE, jobs, min_items=20))
