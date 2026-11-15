#!/usr/bin/env python3
"""
PipeKeeper shared collector framework. Stdlib only.
Every collector produces the same envelope in data/<feed_id>.json:
  {id, name, source, collected_at, jobs_on_board, new_this_run,
   total_tracked, jobs, runs, jobs_seen}
with each job normalized to {title, org, location, detail, url, new_this_run}.
Delta detection (first_seen/last_seen) is identical across feeds.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
BOT_UA = "PipeKeeperBot/0.1 (data pipeline; contact: nilesh)"
CONTACT = "PipeKeeperBot/0.1 (pipeline demo; contact: nilesh)"
MAX_SEEN = 5000  # bound jobs_seen growth per feed
MAX_JOBS = 120   # records stored in the live "jobs" snapshot (all items still delta-tracked)

ENTITIES = [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
            ("&#39;", "'"), ("&apos;", "'"), ("&nbsp;", " "), ("&#x27;", "'"), ("&#x2F;", "/")]


def fetch_json(url, headers=None, timeout=45):
    """GET a JSON document with browser UA + contact header."""
    h = {"User-Agent": BROWSER_UA, "From": CONTACT, "Accept": "application/json,text/*;q=0.9,*/*;q=0.8"}
    if headers:
        h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def post_json(url, payload, headers=None, timeout=45):
    h = {"User-Agent": BOT_UA, "From": CONTACT, "Content-Type": "application/json",
         "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def fetch_text(url, headers=None, timeout=45):
    h = {"User-Agent": BROWSER_UA, "From": CONTACT, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(s, limit=240):
    if not s:
        return None
    s = re.sub(r"<[^>]+>", " ", s)
    for a, b in ENTITIES:
        s = s.replace(a, b)
    return (re.sub(r"\s+", " ", s).strip()[:limit]) or None


def clean(v):
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s[:240] or None


def rec(title, org=None, location=None, detail=None, url=None):
    return {"title": clean(title) or "(untitled)", "org": clean(org),
            "location": clean(location), "detail": clean(detail), "url": url or None}


def collect(feed_id, display_name, category, source, items, min_items=1):
    """Merge items into data/<feed_id>.json with delta tracking. Exit 2 on sanity failure."""
    items = [rec(**i) for i in items]
    if len(items) < min_items:
        print(f"FAIL[{feed_id}]: only {len(items)} records parsed (expected >={min_items}); "
              f"source markup/API may have changed", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fp = DATA / f"{feed_id}.json"
    existing = {"jobs_seen": {}, "runs": []}
    if fp.exists():
        try:
            existing = json.loads(fp.read_text())
        except Exception:
            print(f"WARN[{feed_id}]: data file corrupt, starting fresh", file=sys.stderr)

    seen = existing.get("jobs_seen", {})

    def key(i):
        return "|".join((i.get(k) or "").strip().lower()[:120] for k in ("title", "org", "location"))

    new_count = 0
    for i in items:
        k = key(i)
        old = seen.get(k)
        if old is None:
            seen[k] = {"first_seen": now, "last_seen": now,
                       "title": i["title"], "org": i["org"], "location": i["location"]}
            i["new_this_run"] = True
            new_count += 1
        else:
            old["last_seen"] = now
            i["new_this_run"] = False

    # bound the seen index: drop the oldest entries past MAX_SEEN
    if len(seen) > MAX_SEEN:
        keep = set(k for k, _ in sorted(seen.items(), key=lambda kv: kv[1].get("last_seen", ""),
                                        reverse=True)[:MAX_SEEN])
        for k in [k for k in seen if k not in keep]:
            del seen[k]

    out = {
        "id": feed_id,
        "name": display_name,
        "category": category,
        "source": source,
        "collected_at": now,
        "jobs_on_board": len(items),
        "new_this_run": new_count,
        "total_tracked": len(seen),
        "jobs": items[:MAX_JOBS],
        "runs": (existing.get("runs", []) + [{"at": now, "jobs": len(items), "new": new_count}])[-50:],
        "jobs_seen": seen,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(out, indent=1))
    print(f"OK[{feed_id}]: {len(items)} records, {new_count} new, {len(seen)} tracked at {now}")
    return 0
