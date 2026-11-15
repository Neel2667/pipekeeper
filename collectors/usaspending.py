#!/usr/bin/env python3
"""
Feed 11 — USAspending: federal contract awards >$1M from the last 3 days
(keyless public API). Lead-gen signal: companies newly winning government money.
"""
import sys
from datetime import datetime, timedelta, timezone
from common import collect, post_json

SOURCE = "https://www.usaspending.gov"

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=3)
payload = {
    "filters": {
        "award_type_codes": ["A", "B", "C", "D"],
        "time_period": [{"start_date": f"{start}", "end_date": f"{today}"}],
        "award_amounts": [{"lower_bound": 1000000}],
    },
    "limit": 100,
    "page": 1,
    "fields": ["Award ID", "Recipient Name", "Award Amount", "Description",
               "Start Date", "Awarding Agency", "generated_internal_id"],
}
d = post_json("https://api.usaspending.gov/api/v2/search/spending_by_award/", payload)
results = d.get("results", [])
jobs = []
for r in results:
    amt = r.get("Award Amount")
    amount = f"${amt:,.0f}" if isinstance(amt, (int, float)) else None
    gid = r.get("generated_internal_id")
    jobs.append({
        "title": r.get("Description") or r.get("Award ID") or "(contract)",
        "org": r.get("Recipient Name"),
        "location": None,
        "detail": f"{amount or ''} · {r.get('Awarding Agency') or ''} · start {r.get('Start Date') or '?'}".strip(" ·"),
        "url": f"https://www.usaspending.gov/award/{gid}" if gid else None,
    })
sys.exit(collect("usaspending", "Federal contracts — awards >$1M (last 3 days)", "funding",
                 SOURCE, jobs, min_items=5))
