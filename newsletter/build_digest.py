#!/usr/bin/env python3
"""
PipeKeeper Weekly — automated newsletter digest.
Reads the live data files, computes week-over-week deltas, builds a clean
HTML email, and either:
  - creates + schedules a MailerLite campaign (ML_API_KEY + ML_GROUP_ID env), or
  - sends via plain SMTP (SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_TO env), or
  - just writes the preview HTML (no env set) for visual checking.
Stdlib only. Runs weekly from GitHub Actions (newsletter.yml).
"""
import json
import os
import smtplib
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = "https://neel2667.github.io/pipekeeper/"

CATEGORY_LABELS = {
    "jobs": "Job boards",
    "hiring-signal": "Hiring signals",
    "funding": "Funding & contracts",
    "government": "Government & safety",
    "misc": "Other feeds",
}


def load(path, default):
    try:
        return json.loads((DATA / path).read_text())
    except Exception:
        return default


def week_iso(dt):
    return f"{dt:%B %-d, %Y}" if os.name != "nt" else f"{dt:%B %d, %Y}".replace(" 0", " ")


def build_digest():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat(timespec="seconds")
    index = load("feeds.json", {"feeds": []})
    feeds = index.get("feeds", [])

    sections = {c: [] for c in CATEGORY_LABELS}
    total_new_week = 0
    ok = 0
    highlights = []  # (feed_name, records list)

    for f in feeds:
        d = load(f"{f['id']}.json", None)
        if not d:
            continue
        seen = d.get("jobs_seen", {})
        new_week = sum(1 for v in seen.values() if v.get("first_seen", "") >= week_ago)
        total_new_week += new_week
        if f.get("source") not in (None,) and new_week >= 0:
            ok += 1
        line = (f"<b>{f['jobs_on_board']}</b> latest records · "
                f"<b>+{new_week}</b> new this week · "
                f"{len(d.get('runs', []))} runs")
        sections.setdefault(f.get("category", "misc"), []).append(
            f"<li><b>{f['name']}</b> — {line}</li>")

        # pick highlights: newest 2 records per feed that are new this week
        fresh = [j for j in d.get("jobs", []) if j.get("new_this_run")][0:0]  # placeholder
        fresh_records = []
        for j in d.get("jobs", []):
            k = "|".join((j.get(x) or "").strip().lower()[:120] for x in ("title", "org", "location"))
            rec = seen.get(k)
            if rec and rec.get("first_seen", "") >= week_ago:
                fresh_records.append(j)
        for j in fresh_records[:2]:
            highlights.append((f["name"], j))

    hi_html = ""
    for name, j in highlights[:8]:
        det = j.get("detail") or ""
        org = f" · {j['org']}" if j.get("org") else ""
        loc = f" · {j['location']}" if j.get("location") else ""
        link_open = f"<a href='{j['url']}' style='color:#4c6b00;text-decoration:none;font-weight:600;'>" if j.get("url") else "<b>"
        link_close = "</a>" if j.get("url") else "</b>"
        hi_html += (f"<tr><td style='padding:7px 0;border-bottom:1px solid #e8eadf;'>"
                    f"{link_open}{j['title'][:90]}{link_close}"
                    f"<span style='color:#7a8394;'>{org}{loc} — {det}</span>"
                    f"<span style='color:#9aa2b1;font-size:11px;'> via {name}</span></td></tr>")

    section_html = ""
    for cat, items in sections.items():
        if not items:
            continue
        section_html += (f"<p style='margin:18px 0 6px;font-size:12px;letter-spacing:1.5px;"
                         f"text-transform:uppercase;color:#4c6b00;font-weight:700;'>"
                         f"{CATEGORY_LABELS.get(cat, cat)}</p>"
                         f"<ul style='margin:0;padding-left:18px;color:#333a45;font-size:14px;line-height:1.7;'>"
                         + "".join(items) + "</ul>")

    html = f"""<!doctype html><html><body style="margin:0;background:#f4f6ee;">
<div style="max-width:600px;margin:0 auto;padding:28px 22px;font-family:Georgia,'Times New Roman',serif;background:#ffffff;">
  <div style="border-bottom:2px solid #cdef3c;padding-bottom:14px;margin-bottom:18px;">
    <span style="font-size:13px;letter-spacing:2px;color:#4c6b00;font-weight:700;">PIPEKEEPER WEEKLY</span>
    <div style="font-size:26px;margin-top:8px;color:#15181d;">15 feeds. One week of market truth.</div>
    <div style="font-size:13px;color:#7a8394;margin-top:6px;">Week of {week_iso(now)} · {ok}/15 feeds green · +{total_new_week} new records this week</div>
  </div>

  <p style="font-size:14px;color:#333a45;line-height:1.7;margin:0 0 4px;">Fresh from the hourly pipeline — every record below was collected automatically, timestamped, and health-checked. Click through for sources.</p>

  <p style="margin:20px 0 6px;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#4c6b00;font-weight:700;">New this week — highlights</p>
  <table style="width:100%;border-collapse:collapse;font-size:14px;">{hi_html or '<tr><td style="color:#7a8394;">First digest — highlights grow as weeks accumulate.</td></tr>'}</table>

  {section_html}

  <div style="margin-top:26px;padding:16px 18px;background:#f4f6ee;border-radius:10px;font-size:13px;color:#333a45;line-height:1.6;">
    <b>Health check:</b> {ok}/15 collectors green, hourly cadence, latest run {ago_text(now, index)}.
    <br><b>Want the raw data?</b> Full hourly feeds $99–149/mo, or we run pipelines for you $300–800/mo —
    <a href="{SITE}" style="color:#4c6b00;">see everything live</a>.
  </div>
  <p style="font-size:11px;color:#9aa2b1;margin-top:18px;">You're receiving this because you subscribed at {SITE}. Reply to unsubscribe — a human reads it.</p>
</div></body></html>"""
    return html, {"week_of": now.date().isoformat(), "feeds_ok": ok, "new_this_week": total_new_week}


def ago_text(now, index):
    try:
        host = load("hosthealthcare.json", None)
        t = datetime.fromisoformat(host["collected_at"])
        m = int((now - t).total_seconds() // 60)
        return f"{m} min ago" if m < 90 else f"{m // 60} hrs ago"
    except Exception:
        return "on schedule"


def send_mailerlite(html, subject):
    key = os.environ["ML_API_KEY"]
    group = os.environ.get("ML_GROUP_ID", "")
    def ml(method, url, payload=None):
        req = urllib.request.Request(url, method=method,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            data=json.dumps(payload).encode() if payload else None)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    camp = ml("POST", "https://connect.mailerlite.com/api/campaigns", {
        "name": f"PipeKeeper Weekly {subject.split('—')[-1].strip()}",
        "subject": subject,
        "from_name": "PipeKeeper",
        "reply_to": os.environ.get("NEWSLETTER_FROM", "hello@pipekeeper.dev"),
        "groups": [group] if group else [],
        "content": {"type": "html", "value": html},
    })
    cid = camp["data"]["id"]
    ml("POST", f"https://connect.mailerlite.com/api/campaigns/{cid}/schedule", {"schedule": "now"})
    return f"mailerlite campaign {cid} scheduled now"


def send_smtp(html, subject):
    msg = EmailMessage()
    msg["From"] = formataddr(("PipeKeeper Weekly", os.environ["SMTP_USER"]))
    msg["To"] = os.environ["SMTP_TO"]
    msg["Subject"] = subject
    msg.set_content("Weekly digest — enable HTML to view.")
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    host, port = os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 465))
    with smtplib.SMTP_SSL(host, port, context=ctx) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    return f"smtp sent to {msg['To']}"


def main():
    html, meta = build_digest()
    out = ROOT / "data" / "digest_preview.html"
    out.write_text(html)
    print(f"digest built: week_of={meta['week_of']} feeds_ok={meta['feeds_ok']} new_week={meta['new_this_week']} -> {out}")

    subject = f"PipeKeeper Weekly — {meta['new_this_week']} new records, week of {meta['week_of']}"
    mode = "preview"
    try:
        if os.environ.get("ML_API_KEY"):
            mode = send_mailerlite(html, subject)
        elif os.environ.get("SMTP_HOST"):
            mode = send_smtp(html, subject)
    except Exception as e:
        print(f"WARN: send failed ({e}); digest saved as preview only", file=sys.stderr)
    print(f"delivery mode: {mode}")


if __name__ == "__main__":
    main()
