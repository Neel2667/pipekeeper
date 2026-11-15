#!/usr/bin/env python3
"""
Feed 12 — ClinicalTrials.gov API v2: the most recently updated studies.
Life-science staffing signal: new/updated trials mean sites needing staff.
US-public-domain data, no key.
"""
import sys
from common import collect, fetch_json

SOURCE = "https://clinicaltrials.gov"

d = fetch_json(SOURCE + "/api/v2/studies?sort=LastUpdatePostDate:desc&pageSize=100")
studies = d.get("studies", [])
jobs = []
for s in studies:
    p = s.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    sponsor = (p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}) or {}).get("name")
    status = (p.get("statusModule", {}) or {}).get("overallStatus")
    nct = ident.get("nctId")
    jobs.append({
        "title": ident.get("briefTitle"),
        "org": sponsor,
        "location": status,
        "detail": f"clinical trial · {nct}" if nct else "clinical trial",
        "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
    })
sys.exit(collect("clinicaltrials", "ClinicalTrials.gov — freshly updated studies", "government",
                 SOURCE, jobs, min_items=80))
