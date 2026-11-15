#!/usr/bin/env python3
"""
Feed 10 — SEC EDGAR full-text search: new Form D filings from the last 7 days
= private companies raising money, with no key and US-public-domain data.
The free Crunchbase replacement. SEC requires an honest UA declaring contact.
"""
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from common import collect

BASE = "https://efts.sec.gov/LATEST/search-index"
SOURCE = "https://efts.sec.gov/LATEST/search-index"

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=7)
q = '"total offering amount"'
url = (f"{BASE}?q={urllib.request.quote(q)}&forms=D&dateRange=custom"
       f"&startdt={start:%Y-%m-%d}&enddt={today:%Y-%m-%d}")
hdr = {"User-Agent": "PipeKeeperBot/0.1 (data pipeline; contact: nilesh)"}
import json as _json
req = urllib.request.Request(url, headers=hdr)
with urllib.request.urlopen(req, timeout=45) as r:
    d = _json.loads(r.read().decode())

hits = d.get("hits", {}).get("hits", [])
jobs = []
for h in hits:
    s = h.get("_source", {})
    name = (s.get("display_names") or ["(unknown filer)"])[0]
    company = name.split(" (CIK")[0].strip()
    loc = ", ".join(s.get("biz_locations") or []) or None
    jobs.append({
        "title": f"{company} raised (Form D)",
        "org": company,
        "location": loc,
        "detail": f"SEC Form D · filed {s.get('file_date', '?')}",
        "url": f"https://www.sec.gov/Archives/edgar/data/{(s.get('ciks') or ['0'])[0].lstrip('0')}/{h.get('_id','').split(':')[0].replace('-', '')}/{h.get('_id','').split(':')[0]}-index.htm",
    })
sys.exit(collect("edgarformd", "SEC EDGAR — new private funding rounds (Form D, 7 days)", "funding",
                 SOURCE, jobs, min_items=0))
