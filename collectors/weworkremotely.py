#!/usr/bin/env python3
"""Feed 04 — We Work Remotely programming jobs via public RSS."""
import sys
import xml.etree.ElementTree as ET
from common import collect, fetch_text, strip_html

SOURCE = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

xml = fetch_text(SOURCE)
root = ET.fromstring(xml)
jobs = []
for item in root.iter("item"):
    title = (item.findtext("title") or "").strip()
    if ": " in title:
        org, role = title.split(": ", 1)
    else:
        org, role = None, title
    cats = [c.text.strip() for c in item.findall("category") if c.text]
    jobs.append({
        "title": role,
        "org": org,
        "location": None,
        "detail": cats[0] if cats else None,
        "url": item.findtext("link"),
    })
sys.exit(collect("weworkremotely", "We Work Remotely — programming jobs", "jobs", SOURCE, jobs, min_items=10))
