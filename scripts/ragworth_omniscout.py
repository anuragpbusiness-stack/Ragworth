"""
RAGWORTH OMNISCOUT v3.0 — COORDINATED CONTACT TRIANGULATION ENGINE
===================================================================
Phase 2 of the Omni Intelligence system.

Receives exact businesses discovered by OmniScale and:
  1. Finds the RIGHT decision-maker for AI services (CEO/CTO/CMO/COO/Founder)
  2. Synthesizes their email from name + domain patterns
  3. Attaches LinkedIn source URLs
  4. Returns fully enriched leads ready for the pipeline

Services offered: ANYTHING AI — so we target the broadest set of buyers:
  C-Suite (CEO, Founder, MD, COO), Tech Leaders (CTO, CIO, Head of Digital),
  Marketing (CMO, Marketing Director), Operations (COO, Head of Ops)
"""

import sys
import json
import time
import re
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"])
    import requests
    from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Decision-maker titles to hunt (in priority order for AI services)
AI_BUYER_TITLES = [
    "CEO", "Founder", "Co-Founder", "Managing Director", "Managing Partner",
    "CTO", "Chief Technology Officer", "Head of Technology", "VP Technology",
    "COO", "Chief Operating Officer", "Head of Operations",
    "CMO", "Chief Marketing Officer", "Marketing Director",
    "Director of Digital", "Head of Digital Transformation",
    "CIO", "Chief Information Officer",
    "President", "Owner", "Partner",
]

# Subset to actually search (top 4 most likely buyers)
SEARCH_TITLES = ["CEO", "CTO", "CMO", "COO", "Founder", "Managing Director"]

def get_random_ua():
    return random.choice(UA_LIST)

def ddg_search_one(query: str, session: requests.Session) -> dict | None:
    """Search DuckDuckGo, return first valid result as {title, url}."""
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = session.get(url, timeout=12, headers={"User-Agent": get_random_ua()})
        soup = BeautifulSoup(r.text, "html.parser")
        a = soup.find("a", class_="result__a")
        if a and not "duckduckgo.com" in a.get("href", ""):
            return {"title": a.text.strip(), "url": a["href"]}
    except:
        pass
    return None

def clean_person_name(raw: str) -> str:
    """Clean names like 'John Smith - CEO | Acme Corp' → 'John Smith'"""
    raw = re.sub(r'\s*[-|·•]\s*.*$', '', raw).strip()
    raw = re.sub(r'\s+', ' ', raw)
    # Remove non-name words
    stop_words = ["linkedin", "profile", "the", "and", "at", "in", "of"]
    parts = [w for w in raw.split() if w.lower() not in stop_words and len(w) > 1]
    return " ".join(parts[:3])  # Max 3 words for a name


class OmniScout:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": get_random_ua()})

    def find_decision_maker(self, company_name: str, location: str, domain: str) -> dict:
        """
        Searches for the right AI-buying decision-maker at the given company.
        Returns enriched contact dict.
        """
        best_person = {"full_name": "Decision Maker", "title": "Owner / Director", "linkedin": "", "sources": []}

        city = location.split(",")[0].strip()

        for title in SEARCH_TITLES[:3]:  # Try top 3 titles
            query = f'"{company_name}" "{title}" {city} site:linkedin.com/in'
            result = ddg_search_one(query, self.session)
            time.sleep(random.uniform(0.5, 1.2))

            if result and "linkedin.com/in/" in result["url"]:
                raw_name = result["title"]
                cleaned = clean_person_name(raw_name)

                # Validate: must look like a real name (2+ words, no garbage)
                if len(cleaned.split()) >= 2 and len(cleaned) > 4:
                    best_person = {
                        "full_name": cleaned,
                        "title": title,
                        "linkedin": result["url"],
                        "sources": [{"label": f"LinkedIn: {cleaned} ({title})", "url": result["url"]}],
                    }
                    break  # Found a valid person, stop searching

        return best_person

    def synthesize_email(self, person_name: str, domain: str) -> str:
        """Synthesizes most-likely corporate email from name + domain."""
        if not domain:
            return "info@company.com"

        parts = person_name.lower().split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            # Most common corporate pattern: first.last@domain
            return f"{first}.{last}@{domain}"
        elif len(parts) == 1:
            return f"{parts[0]}@{domain}"
        else:
            return f"info@{domain}"

    def enrich_businesses(self, businesses: list, log_fn=None) -> list:
        """
        Phase 2: Takes businesses from OmniScale and enriches each with
        the right AI-buyer contact + email synthesis.

        businesses: list of lead dicts from OmniScale (each has company, domain, location, etc.)
        Returns: fully enriched lead list
        """
        def log(msg):
            if log_fn:
                log_fn(msg)
            else:
                print(msg)

        enriched = []

        for i, biz in enumerate(businesses):
            company = biz.get("company", "Unknown Company")
            domain  = biz.get("domain", "")
            location = biz.get("location", "")

            log(f"[SCOUT] ({i+1}/{len(businesses)}) Triangulating contact: {company}...")

            person = self.find_decision_maker(company, location, domain)
            email  = self.synthesize_email(person["full_name"], domain)

            # Merge contact data into the business lead
            enriched_lead = dict(biz)
            enriched_lead["contact_name"]     = person["full_name"]
            enriched_lead["contact_title"]    = person["title"]
            enriched_lead["contact_linkedin"] = person["linkedin"]
            enriched_lead["contact_email"]    = email
            enriched_lead["phase2_complete"]  = True

            # Add person sources to existing sources list
            existing_sources = enriched_lead.get("sources", [])
            enriched_lead["sources"] = existing_sources + person.get("sources", [])

            if person["full_name"] != "Decision Maker":
                log(f"[SCOUT]   ✔ Found: {person['full_name']} ({person['title']}) — {email}")
            else:
                log(f"[SCOUT]   → No named contact found. Using decision-maker placeholder.")

            enriched.append(enriched_lead)
            time.sleep(random.uniform(0.3, 0.8))

        log(f"[SCOUT] Phase 2 complete. {len(enriched)} leads fully enriched.")
        return enriched

    # Legacy standalone hunt (kept for backward compat)
    def hunt(self, niche="Law Firm", location="London", count=5):
        from ragworth_omniscale import OmniScale
        scale = OmniScale()
        businesses = scale.run_pulse(target_industry=niche, target_city=location, count=count, callable_only=False)
        return self.enrich_businesses(businesses)


if __name__ == "__main__":
    from ragworth_omniscale import OmniScale
    scale = OmniScale()
    biz = scale.run_pulse(count=3, callable_only=False)
    scout = OmniScout()
    leads = scout.enrich_businesses(biz)
    for l in leads:
        print(f"  → {l['company']} | {l['contact_name']} ({l['contact_title']}) | {l['contact_email']}")
