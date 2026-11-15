#!/usr/bin/env python3
"""
Feed 15 — openFDA enforcement reports: newest food/drug/device recalls.
Realtime risk signal for supply chains, QA teams, and compliance buyers.
Keyless, US-public-domain data (same openFDA infra as the 510(k) feed).
"""
import sys
from common import collect, fetch_json

SOURCE = "https://open.fda.gov/apis/food/enforcement/"

d = fetch_json("https://api.fda.gov/food/enforcement.json?limit=100&sort=report_date:desc")
jobs = []
for r in d.get("results", []):
    where = ", ".join(x for x in (r.get("city"), r.get("state")) if x) or None
    desc = r.get("product_description")
    if desc and len(desc) > 140:
        desc = desc[:137] + "…"
    jobs.append({
        "title": desc or r.get("recall_number") or "(recall)",
        "org": r.get("recalling_firm"),
        "location": where,
        "detail": f"{r.get('status', '')} recall · {r.get('reason_for_recall', '')}".strip(),
        "url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
    })
sys.exit(collect("openfdaenforcement", "openFDA — newest recalls & enforcement actions", "government",
                 SOURCE, jobs, min_items=30))
