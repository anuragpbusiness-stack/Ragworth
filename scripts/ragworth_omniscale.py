"""
RAGWORTH OMNISCALE v2.0 — GLOBAL INTELLIGENCE ENGINE
=====================================================
The "God View" Scraper. Detects technical debt and growth blockers
across the planet to find the Top 50 leads every hour.
"""

import os
import sys
import json
import time
import re
import random
import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    print("[*] Installing required modules (requests, beautifulsoup4)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"])
    import requests
    from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
LEADS_DIR = BASE_DIR / "finance" / "leads"
LEADS_DIR.mkdir(parents=True, exist_ok=True)

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

class OmniScale:
    def __init__(self):
        self.session = requests.Session()
        self.grid_file = DB_DIR / "global_grid.json"

    def banner(self):
        print("\n" + "═" * 80)
        print("  R A G W O R T H   O M N I S C A L E   [ GLOBAL GRID ACTIVE ]")
        print("═" * 80)
        print("  Mode:      AUTOMATED GLOBAL SCAN")
        print("  Detecting: WEBSITES | CRM | AI INTEGRATION")
        print("═" * 80 + "\n")

    def analyze_tech_debt(self, url):
        """
        The 'Intelligence' part. Detects what they are missing.
        """
        debt_score = 0
        services_needed = []
        
        if not url:
            return 1.0, ["Website Development"] # Instant high priority

        try:
            r = self.session.get(url, timeout=8, headers={"User-Agent": random.choice(UA_LIST)}, verify=False)
            html = r.text.lower()
            
            # 1. CRM DETECTION
            crm_indicators = ["hubspot", "salesforce", "zendesk", "intercom", "drift", "pipedrive", "zoho"]
            if not any(x in html for x in crm_indicators):
                debt_score += 0.3
                services_needed.append("CRM Implementation")
            
            # 2. AI DETECTION
            if not any(x in html for x in ["chat", "bot", "assistant", "ai-powered", "chatbot", "openai", "copilot"]):
                debt_score += 0.4
                services_needed.append("AI Integration")

            # 3. WEBSITE QUALITY
            if "viewport" not in html: # Not mobile friendly
                debt_score += 0.2
                services_needed.append("Mobile Optimization")
            if r.elapsed.total_seconds() > 2: # Slow site
                debt_score += 0.1
                services_needed.append("Performance Upgrade")

        except Exception as e:
            # Site offline or blocking
            debt_score = 0.5
            services_needed.append("Infrastructure Audit")

        return round(min(debt_score, 1.0), 2), services_needed

    def run_pulse(self, target_industry=None, target_city=None, count=10):
        """Runs one global 'pulse' — picks a random industry/city if none specified, and finds targets."""
        self.banner()
        
        # Load grid
        with open(self.grid_file, "r", encoding="utf-8") as f:
            grid = json.load(f)
        
        if not target_industry:
            target_industry = random.choice(grid["industries"])
        if not target_city:
            target_city = random.choice(grid["cities"])
        
        print(f"[*] Dispatching Scout to: {target_industry} in {target_city}")
        
        # Discovery via DuckDuckGo
        query = f'"{target_industry}" {target_city} -site:yelp.com -site:tripadvisor.com'
        search_url = f"https://duckduckgo.com/html/?q={query}"
        
        leads = []
        try:
            r = self.session.get(search_url, timeout=15, headers={"User-Agent": random.choice(UA_LIST)})
            soup = BeautifulSoup(r.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            print(f"[*] Search returned {len(results)} raw results. Fingerprinting candidates...")
            
            for res in results:
                name = res.text.strip()
                link = res['href']
                
                # Filter out search redirects or irrelevant results
                if "duckduckgo.com" in link or not link.startswith("http"):
                    continue
                    
                domain = urlparse(link).netloc.replace("www.", "")
                if not domain:
                    continue
                
                print(f"  [🔍] Analyzing: {domain}...")
                score, needs = self.analyze_tech_debt(link)
                
                if score > 0.3: # Only keep leads that need some help
                    lead_entry = {
                        "company": name.split("-")[0].strip(),
                        "website": link,
                        "domain": domain,
                        "intelligence_score": score,
                        "pain_points": ", ".join(needs) if needs else "CRM/AI Modernization",
                        "niche": target_industry,
                        "location": target_city,
                        "status": "High Priority Opportunity"
                    }
                    leads.append(lead_entry)
                    print(f"    [✔] High Debt Found: {lead_entry['company']} | Score: {score}")
                
                if len(leads) >= count: 
                    break
                time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"[!] Pulse failed: {e}")

        # Save and log
        if leads:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            csv_path = LEADS_DIR / f"omniscale_{ts}.csv"
            self._save_results(leads, csv_path)
            self._merge_to_db(leads)
            
        return leads

    def _save_results(self, leads, path):
        if not leads: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(leads[0].keys()))
            w.writeheader()
            w.writerows(leads)
        print(f"\n[✔] Pulse Complete. {len(leads)} Global Leads saved to CSV: {path.name}")

    def _merge_to_db(self, new_leads):
        try:
            # Dynamically resolve path to import RagworthOS
            sys.path.append(str(BASE_DIR / "scripts"))
            from ragworth_os import RagworthOS
            rag_os = RagworthOS()
            rag_os.add_scouted_leads(new_leads)
        except Exception as e:
            print(f"[!] Warning: Centralized database merge failed: {e}. Attempting direct leads.json write fallback...")
            leads_file = DB_DIR / "leads.json"
            if not leads_file.exists():
                return
            with open(leads_file, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            existing = {l.get("company", "").lower() for l in db.get("lead_list", [])}
            added = 0
            for lead in new_leads:
                if lead['company'].lower() in existing: 
                    continue
                db["lead_list"].append({
                    "name": "Decision Maker",
                    "company": lead['company'],
                    "hq": lead['location'],
                    "niche": lead['niche'],
                    "potential_value": "$10,000+",
                    "status": lead['status'],
                    "pain_point": lead['pain_points'],
                    "added_on": datetime.now().strftime("%Y-%m-%d"),
                    "email": f"contact@{lead['domain']}" if lead['domain'] else "info@company.com",
                    "website": lead['website'],
                    "confidence": lead['intelligence_score'],
                    "source": "OmniScale:GlobalScout"
                })
                added += 1
                
            db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            db["metadata"]["total_leads"] = len(db["lead_list"])
            with open(leads_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2)
            print(f"[✔] Fallback: Merged {added} new leads into central JSON database.")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default=None)
    parser.add_argument("--loc", default=None)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    engine = OmniScale()
    engine.run_pulse(args.niche, args.loc, args.count)
