#!/usr/bin/env python3
"""Feed 03 — Remotive remote jobs via public API."""
import sys
from common import collect, fetch_json

SOURCE = "https://remotive.com/api/remote-jobs"

d = fetch_json(SOURCE + "?limit=100")
jobs = [{
    "title": j.get("title"),
    "org": j.get("company_name"),
    "location": (j.get("candidate_required_location") or "remote"),
    "detail": j.get("salary") or j.get("category"),
    "url": j.get("url"),
} for j in d.get("jobs", [])]
# the public API currently returns a capped pool of listings (16); floor set accordingly
sys.exit(collect("remotive", "Remotive — remote jobs", "jobs", SOURCE, jobs, min_items=10))
