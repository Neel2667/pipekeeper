#!/usr/bin/env python3
"""
PipeKeeper collector: Host Healthcare travel-healthcare job board.
Stdlib only. Merges each run into data/hosthealthcare.json, tracking:
- first_seen / last_seen per job (delta detection)
- jobs_new_this_run flag
Part of the self-healing pipeline demo.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.hosthealthcare.com/jobs/"
# Site drops non-browser user agents; use a browser UA (identity/contact sent via header below)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
CONTACT = "PipeKeeperBot/0.1 (pipeline demo; contact: nilesh)"
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hosthealthcare.json"

CARD_RE = re.compile(
    r'jobcard__location">.*?</span>\s*(?P<location>[^<]+)</div>.*?'
    r'jobcard__title">(?P<title>[^<]+)</strong>(?P<extra>.{0,2500}?)View\s+Details',
    re.S,
)
PAY_RE = re.compile(r"Estimated\s+(?:Hourly\s+Pay|Total\s+Pay):.*?\$\s*([\d,]+(?:\.\d+)?)", re.S)
DURATION_RE = re.compile(r"(\d+)\s*Weeks", re.S)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "From": CONTACT, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        return resp.read().decode("utf-8", "replace")


def parse(html: str) -> list[dict]:
    jobs = []
    for m in CARD_RE.finditer(html):
        title = m.group("title").strip()
        location = m.group("location").strip()
        extra = m.group("extra") or ""
        pay = PAY_RE.search(extra)
        dur = DURATION_RE.search(extra)
        kind = "travel" if "Travel" in extra else ("local" if "Local" in extra else "")
        jobs.append(
            {
                "title": title,
                "location": location,
                "pay_usd_week": pay.group(1) if pay else None,
                "weeks": int(dur.group(1)) if dur else None,
                "kind": kind,
            }
        )
    return jobs


def main() -> int:
    html = fetch(URL)
    jobs = parse(html)
    if len(jobs) < 5:
        # sanity guard: markup changed or page broken -> treat as failure
        print(f"FAIL: only {len(jobs)} jobs parsed (expected >=5); markup may have changed", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    existing = {"jobs_seen": {}, "runs": []}
    if DATA_FILE.exists():
        try:
            existing = json.loads(DATA_FILE.read_text())
        except Exception:
            print("WARN: existing data file corrupt, starting fresh", file=sys.stderr)

    seen = existing.get("jobs_seen", {})
    key = lambda j: f"{j['title'].strip().lower()}|{j['location'].strip().lower()}"
    new_count = 0
    for j in jobs:
        k = key(j)
        rec = seen.get(k)
        if rec is None:
            seen[k] = {"first_seen": now, "last_seen": now, "title": j["title"], "location": j["location"]}
            j["new_this_run"] = True
            new_count += 1
        else:
            rec["last_seen"] = now
            j["new_this_run"] = False

    out = {
        "source": URL,
        "collected_at": now,
        "jobs_on_board": len(jobs),
        "new_this_run": new_count,
        "total_tracked": len(seen),
        "jobs": jobs,
        "runs": (existing.get("runs", []) + [{"at": now, "jobs": len(jobs), "new": new_count}])[-50:],
        "jobs_seen": seen,
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(out, indent=1))
    print(f"OK: {len(jobs)} jobs on board, {new_count} new this run, {len(seen)} tracked total at {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
