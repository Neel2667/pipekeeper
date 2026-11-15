#!/usr/bin/env python3
"""
Builds data/feeds.json (the multi-feed index the website consumes) and
appends a run entry with per-collector status to data/health.json.
Usage: python3 collectors/feeds_index.py [status_file]
where status_file has one "collector_id ok|fail" line per collector.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

FALLBACK_META = {  # for pre-framework feeds whose files lack name/category
    "hosthealthcare": ("Host Healthcare — travel healthcare jobs", "jobs"),
}

now = datetime.now(timezone.utc).isoformat(timespec="seconds")
feeds = []
for fp in sorted(DATA.glob("*.json")):
    if fp.name in ("feeds.json", "health.json", "heartbeat.json"):
        continue
    try:
        d = json.loads(fp.read_text())
    except Exception:
        continue
    if "collected_at" not in d:
        continue
    fid = d.get("id") or fp.stem
    name, cat = d.get("name"), d.get("category")
    if not name:
        name, cat = FALLBACK_META.get(fid, (fid, "misc"))
    feeds.append({
        "id": fid,
        "name": name,
        "category": cat,
        "source": d.get("source"),
        "collected_at": d.get("collected_at"),
        "jobs_on_board": d.get("jobs_on_board", 0),
        "new_this_run": d.get("new_this_run", 0),
        "total_tracked": d.get("total_tracked", 0),
        "runs": len(d.get("runs", [])),
    })

(DATA / "feeds.json").write_text(json.dumps({"generated_at": now, "feeds": feeds}, indent=1))

# ---- health ----
status = {}
if len(sys.argv) > 1:
    for line in Path(sys.argv[1]).read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            status[parts[0]] = parts[1] == "ok"

hp = DATA / "health.json"
try:
    h = json.loads(hp.read_text())
except Exception:
    h = {"runs": []}
h["runs"] = (h.get("runs", []) + [{"at": now, "feeds": len(feeds),
                                   "ok": sum(1 for v in status.values() if v),
                                   "failed": sorted(k for k, v in status.items() if not v)}])[-200:]
h["last_run"] = now
h["last_status"] = status
hp.write_text(json.dumps(h, indent=1))
print(f"feeds.json: {len(feeds)} feeds indexed; health: {sum(1 for v in status.values() if v)}/{len(status)} collectors ok")
