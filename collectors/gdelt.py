#!/usr/bin/env python3
"""
Feed 15 — GDELT DOC 2.0: global news articles mentioning staffing/recruiting
in the last day. "Unlimited commercial use without fee" per GDELT's terms;
cite GDELT and link gdeltproject.org (the site does, in the feed panel).
Rate limit is 1 request / 5 seconds; we make exactly 1 per hour.
"""
import sys
import json
import time
import urllib.request
from common import collect, BROWSER_UA

SOURCE = "https://www.gdeltproject.org/"

url = ("https://api.gdeltproject.org/api/v2/doc/doc"
       "?query=(staffing%20OR%20%22recruiting%20agency%22%20OR%20%22recruitment%20agency%22)"
       "&mode=artlist&maxrecords=75&format=json&sort=datedesc&timespan=1d")

req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
raw = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
try:
    d = json.loads(raw)
except Exception:
    # GDELT answers throttled requests with plain text; treat as a miss so
    # health records it and the next hourly run retries (self-healing).
    print(f"FAIL[gdelt]: non-JSON response ({raw[:80]!r}...) — throttled or empty", file=sys.stderr)
    sys.exit(2)

arts = [a for a in d.get("articles", []) if a.get("language") == "English"]
jobs = []
for a in arts:
    jobs.append({
        "title": a.get("title"),
        "org": a.get("domain"),
        "location": a.get("sourcecountry"),
        "detail": f"news · {a.get('seendate', '')}",
        "url": a.get("url"),
    })
sys.exit(collect("gdelt", "GDELT — global staffing & recruiting news (24h)", "news",
                 SOURCE, jobs, min_items=5))
