#!/usr/bin/env python3
"""
Feed 09 — Hacker News "Ask HN: Who is hiring?" — the freshest public list of
companies actively recruiting, via the keyless HN Algolia API.
Lead-gen signal: each comment is a company announcing open roles.
"""
import sys
from common import collect, fetch_json, strip_html

BASE = "https://hn.algolia.com/api/v1"

stories = fetch_json(BASE + "/search_by_date?tags=story,author_whoishiring&hitsPerPage=3")
story = next((h for h in stories.get("hits", []) if "Who is hiring?" in h.get("title", "")), None)
if not story:
    print("FAIL[hnhiring]: no 'Who is hiring?' story found", file=sys.stderr)
    sys.exit(2)

comments = fetch_json(BASE + f"/search_by_date?tags=comment,story_{story['story_id']}&hitsPerPage=250")
jobs = []
for c in comments.get("hits", []):
    # structural filter: only TOP-LEVEL comments are company posts; replies
    # (to applicants or other companies) have a parent_id != the story id
    if str(c.get("parent_id")) != str(story["story_id"]):
        continue
    text = strip_html(c.get("comment_text") or "", limit=160)
    if not text:
        continue
    first = text.split("|")[0].split(". ")[0].strip()
    low = text.lower()
    # quality gate: drop replies, job-seeker posts, and one-liners
    if len(text) < 25 or any(p in low for p in (
            "wrong thread", "is not working", "not working yet", "seeking work",
            "seeking freelance", "seeking remote", "seeking senior", "email:",
            "portfolio:", "flagged", "deleted", "[dead]", "see you in", "who is hiring?",
            "who wants to be hired")):
        continue
    jobs.append({
        "title": first[:110] or "(company post)",
        "org": c.get("author"),
        "location": None,
        "detail": f"Ask HN · {story['title'].split('(')[-1].strip(') ')}",
        "url": f"https://news.ycombinator.com/item?id={c.get('objectID')}",
    })
sys.exit(collect("hnhiring", "Hacker News — Who is hiring? (companies recruiting now)", "hiring-signal",
                 "https://news.ycombinator.com", jobs, min_items=30))
