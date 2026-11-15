#!/usr/bin/env python3
"""
Feed 08 — Public ATS hiring tracker: latest job postings from selected
companies via Greenhouse's public board API (meant for embedding; no auth).
Companies: Anthropic, Stripe, Databricks. Boards that 404 are skipped;
sanity requires >=2 boards still alive.
"""
import sys
import urllib.error
from common import collect, fetch_json

COMPANIES = [("anthropic", "Anthropic"), ("stripe", "Stripe"), ("databricks", "Databricks")]
SOURCE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

ok_boards = 0
jobs = []
for slug, name in COMPANIES:
    try:
        d = fetch_json(SOURCE.format(slug=slug))
    except urllib.error.HTTPError as e:
        print(f"WARN[greenhouse]: board {slug} -> HTTP {e.code}, skipping", file=sys.stderr)
        continue
    ok_boards += 1
    for j in d.get("jobs", []):
        jobs.append({
            "title": j.get("title"),
            "org": j.get("company_name") or name,
            "location": (j.get("location") or {}).get("name"),
            "detail": name,
            "url": j.get("absolute_url"),
        })
if ok_boards < 2:
    print(f"FAIL[greenhouse]: only {ok_boards} boards alive of {len(COMPANIES)}", file=sys.stderr)
    sys.exit(2)
sys.exit(collect("greenhouse", "Hiring tracker — Anthropic · Stripe · Databricks", "hiring-signal",
                 "https://boards.greenhouse.io", jobs, min_items=25))
