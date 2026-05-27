"""
RAGWORTH OMNISCALE v3.0 — GLOBAL TIMEZONE-AWARE INTELLIGENCE ENGINE
====================================================================
Phase 1 of the coordinated Omni Intelligence system.

Finds businesses worldwide that:
  1. Are currently in business hours (callable RIGHT NOW)
  2. Show signals of needing AI services
  3. Have posted recent digital ads / job listings
  4. Are across ALL industries and ALL countries

Returns enriched leads with source URLs attached.
"""

import os
import sys
import json
import time
import re
import random
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlencode, quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"])
    import requests
    from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR   = BASE_DIR / "database"
LEADS_DIR = BASE_DIR / "finance" / "leads"
LEADS_DIR.mkdir(parents=True, exist_ok=True)

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# ─── GLOBAL CITY → UTC OFFSET LOOKUP ────────────────────────────────────────
# Format: "City, Country": UTC_offset_hours (standard / winter time)
CITY_UTC_OFFSETS = {
    # Americas
    "New York, USA": -5, "Los Angeles, USA": -8, "Chicago, USA": -6,
    "Houston, USA": -6, "Miami, USA": -5, "San Francisco, USA": -8,
    "Seattle, USA": -8, "Boston, USA": -5, "Atlanta, USA": -5,
    "Dallas, USA": -6, "Denver, USA": -7, "Phoenix, USA": -7,
    "Toronto, Canada": -5, "Vancouver, Canada": -8, "Montreal, Canada": -5,
    "Mexico City, Mexico": -6, "Sao Paulo, Brazil": -3, "Buenos Aires, Argentina": -3,
    "Bogota, Colombia": -5, "Lima, Peru": -5, "Santiago, Chile": -4,
    # Europe
    "London, UK": 0, "Manchester, UK": 0, "Edinburgh, UK": 0,
    "Dublin, Ireland": 0, "Paris, France": 1, "Berlin, Germany": 1,
    "Amsterdam, Netherlands": 1, "Brussels, Belgium": 1, "Zurich, Switzerland": 1,
    "Vienna, Austria": 1, "Madrid, Spain": 1, "Barcelona, Spain": 1,
    "Rome, Italy": 1, "Milan, Italy": 1, "Stockholm, Sweden": 1,
    "Oslo, Norway": 1, "Copenhagen, Denmark": 1, "Helsinki, Finland": 2,
    "Warsaw, Poland": 1, "Prague, Czech Republic": 1, "Budapest, Hungary": 1,
    "Lisbon, Portugal": 0, "Athens, Greece": 2, "Istanbul, Turkey": 3,
    "Kyiv, Ukraine": 2, "Moscow, Russia": 3, "Bucharest, Romania": 2,
    # Middle East & Africa
    "Dubai, UAE": 4, "Abu Dhabi, UAE": 4, "Riyadh, Saudi Arabia": 3,
    "Doha, Qatar": 3, "Kuwait City, Kuwait": 3, "Manama, Bahrain": 3,
    "Muscat, Oman": 4, "Cairo, Egypt": 2, "Lagos, Nigeria": 1,
    "Nairobi, Kenya": 3, "Johannesburg, South Africa": 2, "Casablanca, Morocco": 1,
    "Accra, Ghana": 0, "Dar es Salaam, Tanzania": 3, "Addis Ababa, Ethiopia": 3,
    # South Asia
    "Mumbai, India": 5, "Delhi, India": 5, "Bangalore, India": 5,
    "Hyderabad, India": 5, "Chennai, India": 5, "Pune, India": 5,
    "Kolkata, India": 5, "Karachi, Pakistan": 5, "Lahore, Pakistan": 5,
    "Dhaka, Bangladesh": 6, "Colombo, Sri Lanka": 5,
    # East & Southeast Asia
    "Singapore, Singapore": 8, "Kuala Lumpur, Malaysia": 8,
    "Jakarta, Indonesia": 7, "Bangkok, Thailand": 7, "Manila, Philippines": 8,
    "Ho Chi Minh City, Vietnam": 7, "Hanoi, Vietnam": 7,
    "Tokyo, Japan": 9, "Osaka, Japan": 9, "Seoul, South Korea": 9,
    "Beijing, China": 8, "Shanghai, China": 8, "Shenzhen, China": 8,
    "Guangzhou, China": 8, "Hong Kong, China": 8, "Taipei, Taiwan": 8,
    # Oceania
    "Sydney, Australia": 10, "Melbourne, Australia": 10, "Brisbane, Australia": 10,
    "Perth, Australia": 8, "Auckland, New Zealand": 12,
}

# ─── GLOBAL INDUSTRY POOL ────────────────────────────────────────────────────
ALL_INDUSTRIES = [
    # Professional Services
    "Law Firm", "Accounting Firm", "Management Consulting", "Financial Advisory",
    "Insurance Agency", "Real Estate Agency", "Mortgage Broker", "Tax Consultancy",
    # Healthcare
    "Private Clinic", "Dental Practice", "Physiotherapy Clinic", "Medical Laboratory",
    "Pharmacy Chain", "Mental Health Clinic", "Optometry Practice",
    # Technology
    "SaaS Startup", "IT Services Company", "Cybersecurity Firm", "Software Development Agency",
    "Data Analytics Company", "Cloud Services Provider", "Digital Agency",
    # Retail & E-commerce
    "E-commerce Brand", "Retail Chain", "Fashion Brand", "Electronics Retailer",
    "Luxury Goods Brand", "Furniture Retailer",
    # Hospitality & Food
    "Hotel Chain", "Restaurant Group", "Food Delivery Service", "Catering Company",
    "Tourism Agency", "Event Management Company",
    # Education
    "Private School", "Training Academy", "Online Course Platform", "EdTech Startup",
    "Language School", "Test Prep Center",
    # Manufacturing & Logistics
    "Manufacturing Company", "Logistics Company", "Supply Chain Company",
    "Freight Forwarding Company", "Construction Company",
    # Media & Marketing
    "Marketing Agency", "PR Agency", "Media Production Company",
    "Advertising Agency", "Content Agency", "Influencer Marketing Agency",
    # Finance & Fintech
    "Fintech Startup", "Investment Firm", "Hedge Fund", "Wealth Management Firm",
    "Crypto Exchange", "Payment Processing Company",
    # Non-profit & Government Adjacent
    "NGO", "Foundation", "Think Tank", "Trade Association",
]

# ─── RECENT ADS / DIGITAL DEMAND QUERY TEMPLATES ────────────────────────────
AD_SIGNAL_QUERIES = [
    '"{industry}" "{city}" "hiring" ("digital marketing" OR "AI" OR "automation") -site:glassdoor.com',
    '"{industry}" "{city}" "looking for" ("web developer" OR "AI engineer" OR "CRM") site:linkedin.com/jobs',
    '"{industry}" "{city}" ("digital transformation" OR "automate" OR "AI integration") after:2024',
    '"{industry}" "{city}" "agency" ("social media" OR "SEO" OR "paid ads") contact',
    '"{industry}" "{city}" site:clutch.co OR site:upwork.com "AI" "automation"',
]

def get_random_ua():
    return random.choice(UA_LIST)

def get_city_local_hour(city_country: str) -> tuple:
    """Returns (local_hour, weekday, is_business_hours) for a given city."""
    offset = CITY_UTC_OFFSETS.get(city_country, None)
    if offset is None:
        # Try partial match
        for key, off in CITY_UTC_OFFSETS.items():
            if any(part.strip().lower() in key.lower() for part in city_country.split(",")):
                offset = off
                break
    if offset is None:
        offset = 0  # Default to UTC

    # Handle India's half-hour offset (+5:30)
    if "India" in city_country or "Mumbai" in city_country or "Delhi" in city_country:
        utc_now = datetime.now(timezone.utc)
        local = utc_now + timedelta(hours=5, minutes=30)
    else:
        utc_now = datetime.now(timezone.utc)
        local = utc_now + timedelta(hours=offset)

    local_hour = local.hour
    weekday = local.weekday()  # 0=Monday, 6=Sunday
    is_business = (9 <= local_hour < 18) and (weekday <= 4)
    return local_hour, weekday, is_business

def format_local_time(city_country: str) -> str:
    offset = CITY_UTC_OFFSETS.get(city_country, 0)
    if "India" in city_country:
        utc_now = datetime.now(timezone.utc)
        local = utc_now + timedelta(hours=5, minutes=30)
    else:
        utc_now = datetime.now(timezone.utc)
        local = utc_now + timedelta(hours=offset)
    return local.strftime("%H:%M")

def ddg_search(query: str, session: requests.Session, max_results: int = 8) -> list:
    """Performs a DuckDuckGo HTML search and returns list of {title, url}."""
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = session.get(url, timeout=15, headers={"User-Agent": get_random_ua()})
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for a in soup.find_all("a", class_="result__a")[:max_results]:
            href = a.get("href", "")
            title = a.text.strip()
            if href and not "duckduckgo.com" in href:
                results.append({"title": title, "url": href})
        return results
    except Exception as e:
        return []


class OmniScale:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": get_random_ua()})

    def analyze_tech_debt(self, url: str) -> tuple:
        """Visits a website, detects what AI/tech services they lack."""
        if not url:
            return 1.0, ["Website Development", "Digital Presence"], []

        signals_found = []
        score = 0.0
        sources = [{"label": "Company Website", "url": url}]

        try:
            r = self.session.get(url, timeout=9, headers={"User-Agent": get_random_ua()}, verify=False)
            html = r.text.lower()

            # AI & Automation
            if not any(x in html for x in ["chatbot", "chat bot", "openai", "gpt", "ai-powered", "artificial intelligence", "automation"]):
                score += 0.35
                signals_found.append("AI Chatbot / Automation")

            # CRM
            if not any(x in html for x in ["hubspot", "salesforce", "pipedrive", "zoho", "crm", "zendesk"]):
                score += 0.25
                signals_found.append("CRM Implementation")

            # Mobile / Performance
            if "viewport" not in html:
                score += 0.15
                signals_found.append("Mobile Optimization")

            # Analytics
            if not any(x in html for x in ["gtag", "google-analytics", "analytics.js", "mixpanel", "segment"]):
                score += 0.10
                signals_found.append("Analytics & Tracking Setup")

            # SEO
            if "<meta name=\"description\"" not in r.text.lower():
                score += 0.10
                signals_found.append("SEO Optimization")

            # Security
            if r.url.startswith("http://"):
                score += 0.05
                signals_found.append("SSL / HTTPS Security")

            # Growth signals (they're scaling)
            if any(x in html for x in ["careers", "we are hiring", "join our team", "jobs"]):
                signals_found.append("⚡ Actively Hiring (Growth Signal)")

        except Exception:
            score = 0.50
            signals_found.append("Infrastructure Audit")

        return round(min(score, 1.0), 2), signals_found, sources

    def detect_ad_signals(self, company_name: str, location: str) -> tuple:
        """Searches for recent job postings / ads from this company needing digital services."""
        ad_hits = []
        ad_sources = []
        queries = [
            f'"{company_name}" "hiring" ("digital" OR "AI" OR "marketing") 2024 OR 2025',
            f'"{company_name}" site:linkedin.com/jobs',
        ]
        for q in queries[:1]:  # Limit to 1 query per company for speed
            results = ddg_search(q, self.session, max_results=3)
            for res in results:
                if company_name.split()[0].lower() in res["title"].lower():
                    ad_hits.append(res["title"][:80])
                    ad_sources.append({"label": f"Job/Ad Signal: {res['title'][:50]}", "url": res["url"]})
            time.sleep(random.uniform(0.3, 0.8))
        return ad_hits, ad_sources

    def run_pulse(self, target_industry=None, target_city=None, count=10, callable_only=True, log_fn=None):
        """
        Main scrape pulse. Returns enriched leads with timezone awareness and source links.
        callable_only: if True, skip leads where local time is outside 9am-6pm Mon-Fri.
        """
        def log(msg):
            if log_fn:
                log_fn(msg)
            else:
                print(msg)

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Pick niche and city
        industry = target_industry or random.choice(ALL_INDUSTRIES)
        city = target_city or random.choice(list(CITY_UTC_OFFSETS.keys()))

        log(f"[SCALE] Phase 1 initializing: {industry} in {city}")

        # Check if this city is currently callable
        local_hour, weekday, is_business = get_city_local_hour(city)
        local_time_str = format_local_time(city)

        if callable_only and not is_business:
            log(f"[SCALE] ⏰ {city} local time: {local_time_str} — AFTER HOURS. Scanning next available market...")
            # Find an open market instead
            open_cities = [c for c in CITY_UTC_OFFSETS.keys() if get_city_local_hour(c)[2]]
            if open_cities:
                city = random.choice(open_cities)
                local_hour, weekday, is_business = get_city_local_hour(city)
                local_time_str = format_local_time(city)
                log(f"[SCALE] ✅ Redirected to OPEN market: {city} (Local: {local_time_str})")
            else:
                log("[SCALE] ⚠ No markets currently open. Running without timezone filter.")
                callable_only = False

        # Search DuckDuckGo
        query = f'"{industry}" {city} -site:yelp.com -site:tripadvisor.com -site:yellowpages.com'
        log(f"[SCALE] 🔍 Scanning: {query[:80]}...")
        search_results = ddg_search(query, self.session, max_results=count + 5)
        log(f"[SCALE] Found {len(search_results)} raw signals. Fingerprinting...")

        # Also search for recent ads in this city+industry
        ad_query = random.choice(AD_SIGNAL_QUERIES).replace("{industry}", industry).replace("{city}", city.split(",")[0])
        log(f"[SCALE] 📡 Scanning recent digital demand signals...")
        ad_results = ddg_search(ad_query, self.session, max_results=3)

        leads = []
        seen_domains = set()

        for res in search_results:
            if len(leads) >= count:
                break

            url = res["url"]
            title = res["title"]

            if "duckduckgo.com" in url or not url.startswith("http"):
                continue

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue
            seen_domains.add(domain)

            company_name = title.split("-")[0].split("|")[0].strip()
            if len(company_name) < 3:
                continue

            log(f"[SCALE] 🧬 Analyzing: {company_name} ({domain})...")

            score, services_needed, sources = self.analyze_tech_debt(url)
            sources.insert(0, {"label": "Discovery: DuckDuckGo", "url": f"https://duckduckgo.com/?q={quote_plus(query)}"})

            if score < 0.25:
                log(f"[SCALE]    → Low debt score ({score}). Skipping.")
                continue

            # Add any matching ad signals
            ad_signal = ""
            for ar in ad_results:
                if company_name.split()[0].lower() in ar["title"].lower():
                    ad_signal = ar["title"][:80]
                    sources.append({"label": f"Ad/Job Signal", "url": ar["url"]})
                    break

            lead_id = f"LEAD-{int(time.time())}-{random.randint(100,999)}"

            lead = {
                "id": lead_id,
                "company": company_name,
                "website": url,
                "domain": domain,
                "location": city,
                "local_time_now": local_time_str,
                "is_callable_now": is_business,
                "niche": industry,
                "services_needed": services_needed,
                "recent_ad_signal": ad_signal,
                "intelligence_score": score,
                "sources": sources,
                "source": "OmniScale:v3",
                "added_on": datetime.now().strftime("%Y-%m-%d"),
                # Phase 2 fields (to be filled by OmniScout)
                "contact_name": "",
                "contact_title": "",
                "contact_linkedin": "",
                "contact_email": "",
                "phase2_complete": False,
            }

            leads.append(lead)
            log(f"[SCALE] ✔ Lead queued: {company_name} | Score: {score} | {city} {local_time_str}")
            time.sleep(random.uniform(0.4, 1.0))

        log(f"[SCALE] Phase 1 complete. {len(leads)} businesses queued for Phase 2 contact triangulation.")
        return leads


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    engine = OmniScale()
    results = engine.run_pulse(count=5, callable_only=False)
    for r in results:
        print(f"  → {r['company']} | {r['location']} | Score: {r['intelligence_score']}")
