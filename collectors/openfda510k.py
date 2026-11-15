#!/usr/bin/env python3
"""
Feed 13 — openFDA: newest 510(k) device clearances (no key needed).
Medtech market signal: companies clearing devices = hiring/launching.
US-public-domain data.
"""
import sys
from common import collect, fetch_json

SOURCE = "https://open.fda.gov/apis/device/510k/"

d = fetch_json("https://api.fda.gov/device/510k.json?limit=100&sort=date_received:desc")
jobs = []
for r in d.get("results", []):
    where = ", ".join(x for x in (r.get("city"), r.get("state")) if x) or None
    jobs.append({
        "title": r.get("device_name"),
        "org": r.get("applicant"),
        "location": where,
        "detail": f"510(k) {r.get('decision_code', '')} · K{str(r.get('k_number', '')).lstrip('K')} · {r.get('decision_date', '')}".strip(),
        "url": f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID=K{str(r.get('k_number', '')).lstrip('K')}",
    })
sys.exit(collect("openfda510k", "openFDA — newest device clearances (510k)", "government",
                 SOURCE, jobs, min_items=80))
