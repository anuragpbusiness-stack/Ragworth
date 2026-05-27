"""
RAGWORTH OMNISCALE v4.0 — SIGNAL CLUSTER ENGINE
================================================
Research-backed: Leads with 3+ stacked signals convert at 60-80%.

Five signal layers per lead:
  1. TECHNOGRAPHIC  — What tools they're missing (AI, CRM, analytics, SSL)
  2. TRIGGER EVENTS — Funding, new leadership, expansion, rebranding
  3. PAIN SIGNALS   — Job postings that reveal what they struggle with
  4. INTENT SIGNALS — Public statements about digital transformation / AI
  5. AD DEMAND      — They're actively spending money on ads (have budget)

A lead only qualifies if it scores >= 0.45 AND has >= 2 distinct signal categories.
This ensures you're calling someone with a REAL problem, REAL budget, and REAL urgency.

Callable window: 12:00 PM — 7:00 PM local time (Mon-Fri)
"""

import sys
import json
import time
import re
import random
from datetime import datetime, timezone, timedelta
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

BASE_DIR  = Path(__file__).resolve().parent.parent
DB_DIR    = BASE_DIR / "database"
LEADS_DIR = BASE_DIR / "finance" / "leads"
LEADS_DIR.mkdir(parents=True, exist_ok=True)

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
]

# ─── TIMEZONE MAP (City → UTC offset hours) ─────────────────────────────────
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

ALL_INDUSTRIES = [
    "Law Firm", "Accounting Firm", "Management Consulting", "Financial Advisory",
    "Insurance Agency", "Real Estate Agency", "Mortgage Broker", "Tax Consultancy",
    "Private Clinic", "Dental Practice", "Physiotherapy Clinic", "Medical Laboratory",
    "Pharmacy Chain", "Mental Health Clinic", "Optometry Practice",
    "SaaS Startup", "IT Services Company", "Cybersecurity Firm", "Software Development Agency",
    "Data Analytics Company", "Cloud Services Provider", "Digital Agency",
    "E-commerce Brand", "Retail Chain", "Fashion Brand", "Electronics Retailer",
    "Luxury Goods Brand", "Furniture Retailer",
    "Hotel Chain", "Restaurant Group", "Food Delivery Service", "Catering Company",
    "Tourism Agency", "Event Management Company",
    "Private School", "Training Academy", "Online Course Platform", "EdTech Startup",
    "Language School", "Test Prep Center",
    "Manufacturing Company", "Logistics Company", "Supply Chain Company",
    "Freight Forwarding Company", "Construction Company",
    "Marketing Agency", "PR Agency", "Media Production Company",
    "Advertising Agency", "Content Agency", "Influencer Marketing Agency",
    "Fintech Startup", "Investment Firm", "Hedge Fund", "Wealth Management Firm",
    "Crypto Exchange", "Payment Processing Company",
    "NGO", "Foundation", "Think Tank", "Trade Association",
    "Architecture Firm", "Interior Design Studio", "Engineering Consultancy",
    "Recruitment Agency", "HR Consulting Firm", "Staffing Agency",
]

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_random_ua():
    return random.choice(UA_LIST)

def get_city_local_time(city: str):
    """Returns (local_hour, weekday, is_callable, time_str) for a city."""
    offset = CITY_UTC_OFFSETS.get(city, None)
    if offset is None:
        for key, off in CITY_UTC_OFFSETS.items():
            if any(p.strip().lower() in key.lower() for p in city.split(",")):
                offset = off
                break
    if offset is None:
        offset = 0

    utc_now = datetime.now(timezone.utc)
    if "India" in city or offset == 5:
        local = utc_now + timedelta(hours=5, minutes=30)
    else:
        local = utc_now + timedelta(hours=offset)

    h = local.hour
    wd = local.weekday()
    callable_now = (12 <= h < 19) and (wd <= 4)
    return h, wd, callable_now, local.strftime("%H:%M")

def ddg_search(query: str, session: requests.Session, n: int = 6) -> list:
    """DuckDuckGo search — returns [{title, url}]"""
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = session.get(url, timeout=14, headers={"User-Agent": get_random_ua()})
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        for a in soup.find_all("a", class_="result__a")[:n]:
            href = a.get("href", "")
            if href and "duckduckgo.com" not in href:
                out.append({"title": a.text.strip(), "url": href})
        return out
    except:
        return []


# ─── SIGNAL DETECTION MODULES ────────────────────────────────────────────────

def detect_technographic_signals(url: str, session: requests.Session) -> tuple:
    """
    Layer 1: Visit website and detect missing AI/tech stack elements.
    Returns (score_contribution, signals_list, sources_list)
    """
    if not url:
        return 0.35, ["No Website (Max Opportunity)"], [{"label": "No Website Found", "url": ""}]

    score = 0.0
    signals = []
    sources = [{"label": "Company Website", "url": url}]

    try:
        r = session.get(url, timeout=9, headers={"User-Agent": get_random_ua()}, verify=False)
        html = r.text.lower()

        # AI & Automation gap
        ai_markers = ["chatbot", "chat bot", "openai", "gpt", "ai-powered", "artificial intelligence",
                      "automation", "copilot", "intercom", "drift", "tidio", "crisp.chat"]
        if not any(x in html for x in ai_markers):
            score += 0.20
            signals.append("🤖 No AI / Chatbot Detected")

        # CRM gap
        crm_markers = ["hubspot", "salesforce", "pipedrive", "zoho crm", "freshsales", "monday.com",
                       "crm", "zendesk", "intercom"]
        if not any(x in html for x in crm_markers):
            score += 0.15
            signals.append("📋 No CRM System Detected")

        # Analytics gap
        analytics = ["gtag(", "google-analytics", "analytics.js", "mixpanel", "segment.io",
                     "hotjar", "clarity.ms", "heap.io"]
        if not any(x in html for x in analytics):
            score += 0.08
            signals.append("📊 No Analytics Tracking")

        # Mobile readiness
        if "viewport" not in html:
            score += 0.10
            signals.append("📱 Not Mobile Optimised")

        # HTTPS
        if r.url.startswith("http://"):
            score += 0.07
            signals.append("🔒 No SSL / HTTPS")

        # Speed (slow = customer friction)
        if r.elapsed.total_seconds() > 3:
            score += 0.05
            signals.append("⚡ Slow Website (>3s)")

        # SEO gap
        if '<meta name="description"' not in r.text.lower():
            score += 0.05
            signals.append("🔍 No SEO Meta Tags")

        # Growth signal (hiring = scaling = needs tools)
        if any(x in html for x in ["we are hiring", "join our team", "careers", "job openings"]):
            score += 0.10
            signals.append("🚀 Actively Hiring (Growth Signal)")

    except Exception:
        score = 0.30
        signals.append("🔌 Site Inaccessible / Offline")

    return round(min(score, 0.50), 2), signals, sources


def detect_trigger_events(company_name: str, location: str, session: requests.Session) -> tuple:
    """
    Layer 2: Search for recent trigger events — funding, new leadership, expansion.
    These are THE highest-converting signals. A new CMO has fresh budget and mandate.
    Returns (score_contribution, signals_list, sources_list)
    """
    score = 0.0
    signals = []
    sources = []
    city = location.split(",")[0].strip()

    trigger_queries = [
        (f'"{company_name}" ("new CEO" OR "new CTO" OR "new CMO" OR "appointed" OR "joins as") 2024 OR 2025',
         "New Executive Hire", 0.25),
        (f'"{company_name}" ("funding" OR "raised" OR "Series A" OR "Series B" OR "investment") 2024 OR 2025',
         "Recent Funding Round", 0.22),
        (f'"{company_name}" ("expansion" OR "new office" OR "new market" OR "launches in") 2024 OR 2025',
         "Geographic Expansion", 0.18),
        (f'"{company_name}" ("digital transformation" OR "AI strategy" OR "automate" OR "modernise") 2024 OR 2025',
         "Digital Transformation Initiative", 0.20),
    ]

    for query, label, weight in trigger_queries[:2]:  # Check top 2 for speed
        results = ddg_search(query, session, n=2)
        time.sleep(random.uniform(0.3, 0.7))
        for res in results:
            name_word = company_name.split()[0].lower()
            if name_word in res["title"].lower() or name_word in res["url"].lower():
                score += weight
                signals.append(f"⚡ {label}: {res['title'][:60]}")
                sources.append({"label": f"Trigger: {label}", "url": res["url"]})
                break  # One hit per query is enough

    return round(min(score, 0.35), 2), signals, sources


def detect_pain_signals(company_name: str, industry: str, session: requests.Session) -> tuple:
    """
    Layer 3: Search for job postings that reveal what they're struggling with.
    Hiring for a 'Data Entry Clerk' means they need AI automation.
    Hiring 'Customer Support Agent x5' means they need a chatbot.
    Returns (score_contribution, signals_list, sources_list)
    """
    score = 0.0
    signals = []
    sources = []

    # Pain-to-service map: if they're hiring for this role → they need AI
    pain_map = {
        "data entry": ("Manual Data Processing", 0.20),
        "customer service representative": ("Customer Service Automation", 0.20),
        "social media manager": ("AI Content Generation", 0.18),
        "bookkeeper": ("AI Accounting / Automation", 0.18),
        "receptionist": ("AI Receptionist / Voice Bot", 0.18),
        "marketing coordinator": ("AI Marketing Automation", 0.16),
        "cold caller": ("AI Outreach Automation", 0.18),
        "content writer": ("AI Content Generation", 0.16),
        "lead generation specialist": ("AI Lead Gen Automation", 0.16),
        "operations manager": ("AI Workflow Automation", 0.15),
    }

    query = f'"{company_name}" hiring site:linkedin.com/jobs OR site:indeed.com OR site:glassdoor.com'
    results = ddg_search(query, session, n=4)
    time.sleep(random.uniform(0.3, 0.6))

    for res in results:
        title_lower = res["title"].lower()
        for keyword, (pain_label, weight) in pain_map.items():
            if keyword in title_lower:
                score += weight
                signals.append(f"💼 Hiring: '{res['title'][:50]}' → Needs {pain_label}")
                sources.append({"label": f"Job Signal: {res['title'][:40]}", "url": res["url"]})
                break

    return round(min(score, 0.25), 2), signals, sources


def detect_intent_signals(company_name: str, industry: str, session: requests.Session) -> tuple:
    """
    Layer 4: Search for public intent — they've talked about needing AI/digital change.
    Companies that publicly mention 'we need to modernise' are warm leads.
    Returns (score_contribution, signals_list, sources_list)
    """
    score = 0.0
    signals = []
    sources = []

    intent_queries = [
        f'"{company_name}" ("struggling with" OR "challenge" OR "pain point" OR "bottleneck") "digital" OR "process" 2024',
        f'"{company_name}" site:linkedin.com ("digital" OR "AI" OR "automation" OR "transform") 2024 OR 2025',
    ]

    for q in intent_queries[:1]:
        results = ddg_search(q, session, n=2)
        time.sleep(random.uniform(0.2, 0.5))
        for res in results:
            name_word = company_name.split()[0].lower()
            if name_word in res["title"].lower():
                score += 0.15
                signals.append(f"🎯 Intent: {res['title'][:60]}")
                sources.append({"label": f"Intent Signal", "url": res["url"]})
                break

    return round(min(score, 0.15), 2), signals, sources


def detect_ad_budget_signals(company_name: str, location: str, session: requests.Session) -> tuple:
    """
    Layer 5: Companies running ads have BUDGET. They spend money = they'll pay you.
    Also catches businesses posting about needing digital services.
    Returns (score_contribution, signals_list, sources_list)
    """
    score = 0.0
    signals = []
    sources = []
    city = location.split(",")[0].strip()

    q = f'"{company_name}" {city} ("Google Ads" OR "Facebook Ads" OR "running ads" OR "digital marketing" OR "SEO agency") 2024 OR 2025'
    results = ddg_search(q, session, n=2)
    time.sleep(random.uniform(0.2, 0.5))

    for res in results:
        name_word = company_name.split()[0].lower()
        if name_word in res["title"].lower() or name_word in res["url"].lower():
            score += 0.12
            signals.append(f"💰 Ad Budget Signal: {res['title'][:55]}")
            sources.append({"label": f"Ad/Budget Signal", "url": res["url"]})
            break

    return round(min(score, 0.12), 2), signals, sources


# ─── MAIN ENGINE ─────────────────────────────────────────────────────────────

class OmniScale:
    def __init__(self):
        import urllib3
        urllib3.disable_warnings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": get_random_ua()})

    def run_pulse(self, target_industry=None, target_city=None, count=8,
                  callable_only=True, log_fn=None):
        """
        Full signal-cluster scrape. Returns only leads with strong stacked signals.
        Min threshold: score >= 0.45 AND signals from >= 2 distinct categories.
        """
        def log(msg):
            if log_fn: log_fn(msg)
            else: print(msg)

        industry = target_industry or random.choice(ALL_INDUSTRIES)
        city     = target_city or random.choice(list(CITY_UTC_OFFSETS.keys()))

        local_h, wd, callable_now, time_str = get_city_local_time(city)

        if callable_only and not callable_now:
            log(f"[SCALE] ⏰ {city} local time: {time_str} — outside 12pm-7pm window. Finding open market...")
            open_cities = [c for c in CITY_UTC_OFFSETS if get_city_local_time(c)[2]]
            if open_cities:
                city = random.choice(open_cities)
                local_h, wd, callable_now, time_str = get_city_local_time(city)
                log(f"[SCALE] ✅ Redirected to: {city} (Local: {time_str})")
            else:
                log("[SCALE] ⚠ No callable markets now. Running without timezone filter.")
                callable_only = False

        log(f"[SCALE] 🌍 Target: {industry} in {city} | Local time: {time_str}")
        log(f"[SCALE] 🔬 Signal-cluster mode: 5-layer analysis per lead")

        # Primary discovery
        query = f'"{industry}" {city} -site:yelp.com -site:tripadvisor.com -site:yellowpages.com -site:facebook.com'
        log(f"[SCALE] 🔍 Discovery query: {query[:80]}...")
        raw_results = ddg_search(query, self.session, n=count + 8)

        # Also run a secondary intent-discovery query
        intent_query = f'{industry} {city} ("AI" OR "automation" OR "digital transformation") 2024 OR 2025'
        raw_results += ddg_search(intent_query, self.session, n=4)
        log(f"[SCALE] Found {len(raw_results)} raw signals. Running 5-layer analysis...")

        leads = []
        seen_domains = set()

        for res in raw_results:
            if len(leads) >= count:
                break

            url   = res["url"]
            title = res["title"]

            if not url.startswith("http") or "duckduckgo.com" in url:
                continue

            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if not domain or domain in seen_domains:
                continue
            # Skip directories, review sites, news aggregators
            skip_domains = ["yelp.com", "tripadvisor.com", "yellowpages.com", "facebook.com",
                           "twitter.com", "instagram.com", "bbc.com", "reuters.com",
                           "bloomberg.com", "indeed.com", "glassdoor.com", "linkedin.com",
                           "clutch.co", "upwork.com", "fiverr.com"]
            if any(s in domain for s in skip_domains):
                continue
            seen_domains.add(domain)

            company_name = title.split("-")[0].split("|")[0].strip()
            if len(company_name) < 3 or len(company_name.split()) > 8:
                continue

            log(f"[SCALE] 🧬 Analysing: {company_name} ({domain})")

            all_signals  = []
            all_sources  = [{"label": "Discovery: DuckDuckGo Search", "url": f"https://duckduckgo.com/?q={quote_plus(query)}"}]
            total_score  = 0.0
            signal_types_hit = 0

            # Layer 1: Technographic
            t_score, t_sigs, t_src = detect_technographic_signals(url, self.session)
            if t_sigs:
                all_signals.extend(t_sigs)
                all_sources.extend(t_src)
                total_score += t_score
                signal_types_hit += 1
                log(f"[SCALE]   [T] {len(t_sigs)} tech gaps | +{t_score:.2f}")

            # Layer 2: Trigger events (most valuable signal)
            tr_score, tr_sigs, tr_src = detect_trigger_events(company_name, city, self.session)
            if tr_sigs:
                all_signals.extend(tr_sigs)
                all_sources.extend(tr_src)
                total_score += tr_score
                signal_types_hit += 1
                log(f"[SCALE]   [E] TRIGGER: {tr_sigs[0][:50]} | +{tr_score:.2f}")

            # Layer 3: Pain signals (job postings)
            p_score, p_sigs, p_src = detect_pain_signals(company_name, industry, self.session)
            if p_sigs:
                all_signals.extend(p_sigs)
                all_sources.extend(p_src)
                total_score += p_score
                signal_types_hit += 1
                log(f"[SCALE]   [P] PAIN: {p_sigs[0][:50]} | +{p_score:.2f}")

            # Layer 4: Intent signals
            i_score, i_sigs, i_src = detect_intent_signals(company_name, industry, self.session)
            if i_sigs:
                all_signals.extend(i_sigs)
                all_sources.extend(i_src)
                total_score += i_score
                signal_types_hit += 1
                log(f"[SCALE]   [I] INTENT: {i_sigs[0][:50]} | +{i_score:.2f}")

            # Layer 5: Ad/budget signal
            a_score, a_sigs, a_src = detect_ad_budget_signals(company_name, city, self.session)
            if a_sigs:
                all_signals.extend(a_sigs)
                all_sources.extend(a_src)
                total_score += a_score
                signal_types_hit += 1
                log(f"[SCALE]   [A] BUDGET: {a_sigs[0][:50]} | +{a_score:.2f}")

            total_score = round(min(total_score, 1.0), 2)

            # QUALITY GATE: Must have score >= 0.45 AND >= 2 distinct signal types
            if total_score < 0.45 or signal_types_hit < 2:
                log(f"[SCALE]   ✗ REJECTED — score={total_score} signals={signal_types_hit} (need ≥0.45, ≥2 types)")
                time.sleep(random.uniform(0.2, 0.5))
                continue

            # Determine the single best pitch angle based on strongest signals
            pitch_angle = _pick_pitch_angle(all_signals)

            lead_id = f"LEAD-{int(time.time())}-{random.randint(1000,9999)}"
            lead = {
                "id": lead_id,
                "company": company_name,
                "website": url,
                "domain": domain,
                "location": city,
                "local_time_now": time_str,
                "is_callable_now": callable_now,
                "niche": industry,
                "services_needed": all_signals,
                "pitch_angle": pitch_angle,
                "recent_ad_signal": next((s for s in all_signals if "💰" in s), ""),
                "intelligence_score": total_score,
                "signal_types_hit": signal_types_hit,
                "sources": all_sources,
                "source": "OmniScale:v4",
                "added_on": datetime.now().strftime("%Y-%m-%d"),
                # Phase 2 fields (filled by OmniScout)
                "contact_name": "",
                "contact_title": "",
                "contact_linkedin": "",
                "contact_email": "",
                "phase2_complete": False,
            }
            leads.append(lead)
            log(f"[SCALE] ✅ QUALIFIED: {company_name} | Score: {total_score} | {signal_types_hit} signal types")
            time.sleep(random.uniform(0.5, 1.2))

        log(f"[SCALE] Phase 1 complete. {len(leads)}/{len(raw_results)} businesses passed quality gate.")
        return leads


def _pick_pitch_angle(signals: list) -> str:
    """Returns the single best pitch opener based on detected signals."""
    for s in signals:
        if "Trigger" in s or "⚡" in s:
            return "Congratulate them on the trigger event, then ask: 'We help companies like yours scale faster with AI — are you exploring that yet?'"
        if "Hiring" in s or "💼" in s:
            return f"They're hiring for a role AI can handle. Open with: 'I noticed you're hiring for [role] — we've helped similar companies automate that with AI and cut that cost entirely. Worth a quick chat?'"
        if "No AI" in s or "🤖" in s:
            return "They have zero AI tools. Open with: 'Most [industry] businesses we work with have added an AI assistant that handles 60% of customer queries — are you still doing that manually?'"
        if "No CRM" in s or "📋" in s:
            return "No CRM = chaotic sales process. Open with: 'How are you currently tracking your leads and follow-ups? We can set up a full AI-powered CRM in a week.'"
    return "Ask about their biggest operational bottleneck: 'What's the one thing in your business that if it were automated, would save you the most time?'"


if __name__ == "__main__":
    import urllib3; urllib3.disable_warnings()
    engine = OmniScale()
    leads = engine.run_pulse(count=3, callable_only=False)
    for l in leads:
        print(f"\n  → {l['company']} | Score: {l['intelligence_score']} | {l['signal_types_hit']} signals")
        print(f"     PITCH: {l['pitch_angle'][:80]}")
