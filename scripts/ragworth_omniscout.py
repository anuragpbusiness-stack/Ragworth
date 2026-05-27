"""
RAGWORTH OMNISCOUT v1.0 — THE INTELLIGENCE ENGINE
==================================================
Zero-Key Triangulation Scraper. 
Uses: Google/DuckDuckGo Dorking, LinkedIn Public Profiles, and 
Direct Company Sitemap Extraction to find high-value leads.
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

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
LEADS_DIR = BASE_DIR / "finance" / "leads"
LEADS_DIR.mkdir(parents=True, exist_ok=True)

# User Agents to avoid simple blocking
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]

class OmniScout:
    def __init__(self):
        self.session = requests.Session()

    def banner(self):
        print("\n" + "═" * 70)
        print("  R A G W O R T H   O M N I S C O U T   [ INTELLIGENCE LAYER ]")
        print("═" * 70)
        print("  Status:    OPERATIONAL")
        print("  Engine:    Triangulation Protocol v1.0")
        print("  Auth:      ZERO-KEY (Public Intelligence)")
        print("═" * 70 + "\n")

    def discover_companies(self, niche, location, count=10):
        """Finds company domains using DuckDuckGo HTML."""
        print(f"[*] Phase 1: Mining {niche} in {location}...")
        query = f'"{niche}" {location} site:linkedin.com/company'
        url = f"https://duckduckgo.com/html/?q={query}"
        
        try:
            r = self.session.get(url, timeout=15, headers={"User-Agent": random.choice(UA_LIST)})
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.find_all('a', class_='result__a')
            
            companies = []
            for link in links:
                title = link.text.strip()
                href = link['href']
                
                # Extract clean company name
                name = title.split("|")[0].split(":")[0].split("-")[0].strip()
                if not name or "linkedin.com" in name.lower() or "duckduckgo" in href:
                    continue
                    
                companies.append({
                    "name": name,
                    "source_url": href
                })
            return companies[:count]
        except Exception as e:
            print(f"  [!] Mining error: {e}")
            return []

    def find_decision_makers(self, company_name, location):
        """Finds LinkedIn profiles for CEOs/Managing Partners without API."""
        print(f"    [🔍] Finding decision makers for: {company_name}")
        titles = ["CEO", "Founder", "Managing Partner", "Director"]
        results = []
        
        for title in titles[:2]: # Limit to save time
            query = f'"{company_name}" "{title}" {location} site:linkedin.com/in'
            url = f"https://duckduckgo.com/html/?q={query}"
            
            try:
                r = self.session.get(url, timeout=10, headers={"User-Agent": random.choice(UA_LIST)})
                soup = BeautifulSoup(r.text, 'html.parser')
                res = soup.find('a', class_='result__a')
                if res and "linkedin.com/in/" in res['href']:
                    full_name = res.text.split("-")[0].split("|")[0].strip()
                    # Clean up names like "John Doe - Managing Director"
                    full_name = re.sub(r'\s+[-|].*$', '', full_name)
                    results.append({
                        "full_name": full_name,
                        "title": title,
                        "linkedin": res['href']
                    })
                    break # Found one, move on
            except: 
                pass
            time.sleep(1)
        return results

    def synthesize_intelligence(self, company_name, person_name):
        """
        1. Find company domain
        2. Guess email patterns
        3. Crawl for confirmation
        """
        domain = ""
        query = f'"{company_name}" official website'
        try:
            r = self.session.get(f"https://duckduckgo.com/html/?q={query}", timeout=10, headers={"User-Agent": random.choice(UA_LIST)})
            soup = BeautifulSoup(r.text, 'html.parser')
            res = soup.find('a', class_='result__a')
            if res:
                link = res['href']
                if not "duckduckgo" in link:
                    domain = urlparse(link).netloc.replace("www.", "")
        except: 
            pass

        if not domain: 
            # Fallback domain structure
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
            domain = f"{clean_name}.com"

        score = 0.5 # Default
        signals = []
        try:
            r = self.session.get(f"https://{domain}", timeout=5, headers={"User-Agent": random.choice(UA_LIST)}, verify=False)
            content = r.text.lower()
            if "ai" in content or "automation" in content or "intelligence" in content:
                score += 0.2
                signals.append("AI-Interested")
            if "careers" in content or "hiring" in content or "join our team" in content:
                score += 0.1
                signals.append("Growing")
        except: 
            pass

        # Email Synthesis
        email = f"info@{domain}"
        if person_name and person_name != "Decision Maker":
            parts = person_name.lower().split()
            if len(parts) >= 2:
                patterns = [
                    f"{parts[0]}.{parts[1]}@{domain}",
                    f"{parts[0]}@{domain}",
                    f"{parts[0][0]}{parts[1]}@{domain}"
                ]
                email = patterns[0] # Default to standard corporate first.last@company.com

        return {
            "email": email,
            "domain": domain,
            "intelligence_score": round(min(score, 1.0), 2),
            "signals": signals
        }

    def hunt(self, niche="Boutique Law Firm", location="London", count=10):
        self.banner()
        start_time = time.time()
        
        # 1. Discover
        companies = self.discover_companies(niche, location, count)
        print(f"  [✔] {len(companies)} companies discovered.\n")

        leads = []
        for co in companies:
            # 2. Find Person
            people = self.find_decision_makers(co['name'], location)
            person = people[0] if people else {"full_name": "Decision Maker", "title": "Owner/Partner", "linkedin": ""}
            
            # 3. Synthesize Intel
            intel = self.synthesize_intelligence(co['name'], person['full_name'])
            
            # 4. Construct Lead
            lead = {
                "first_name": person['full_name'].split()[0] if " " in person['full_name'] else person['full_name'],
                "last_name": person['full_name'].split()[-1] if " " in person['full_name'] else "",
                "title": person['title'],
                "company": co['name'],
                "domain": intel['domain'],
                "email": intel['email'],
                "linkedin": person['linkedin'],
                "location": location,
                "confidence": intel['intelligence_score'],
                "signals": ", ".join(intel['signals']) if intel['signals'] else "High-Value Target",
                "source": "OmniScout:PublicTriangulation",
                "added_on": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            leads.append(lead)
            print(f"    [+] {lead['company']} | {person['full_name']} | Score: {lead['confidence']}")
            
            time.sleep(random.uniform(0.5, 1.5))
            if len(leads) >= count: 
                break

        # Sort by Score (Intelligence)
        leads = sorted(leads, key=lambda x: x['confidence'], reverse=True)

        # Save
        if leads:
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            csv_path = LEADS_DIR / f"ragworth_omniscout_{ts}.csv"
            self._save_csv(leads, csv_path)
            added = self._merge_to_db(leads)
        else:
            added = 0
            csv_path = "None"

        print("\n" + "═" * 70)
        print(f"  ✓ OMNISCOUT HUNT COMPLETE in {int(time.time() - start_time)}s")
        print(f"    Target:          {niche} in {location}")
        print(f"    Top Leads Found: {len(leads)}")
        print(f"    Added to DB:     {added}")
        print(f"    CSV Delivered:   {csv_path}")
        print("═" * 70 + "\n")
        return leads

    def _save_csv(self, leads, path):
        if not leads: return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(leads[0].keys()))
            w.writeheader()
            w.writerows(leads)

    def _merge_to_db(self, new_leads):
        try:
            # Dynamically resolve path to import RagworthOS
            sys.path.append(str(BASE_DIR / "scripts"))
            from ragworth_os import RagworthOS
            rag_os = RagworthOS()
            return rag_os.add_scouted_leads(new_leads)
        except Exception as e:
            print(f"[!] Warning: Centralized database merge failed: {e}. Attempting direct leads.json write fallback...")
            leads_file = DB_DIR / "leads.json"
            if not leads_file.exists():
                return 0
            with open(leads_file, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            existing = {l.get("company", "").lower() for l in db.get("lead_list", [])}
            added = 0
            for lead in new_leads:
                if lead['company'].lower() in existing: 
                    continue
                db["lead_list"].append({
                    "name": f"{lead['first_name']} {lead['last_name']}",
                    "company": lead['company'],
                    "title": lead['title'],
                    "hq": lead['location'],
                    "niche": lead['signals'] or "Target Profile",
                    "email": lead['email'],
                    "website": f"https://{lead['domain']}" if lead['domain'] else "",
                    "linkedin": lead['linkedin'],
                    "potential_value": "$15,000+",
                    "status": "Scouted (OmniScout)",
                    "source": lead['source'],
                    "confidence": lead['confidence'],
                    "pain_point": "Manual business workflow vulnerabilities",
                    "added_on": datetime.now().strftime("%Y-%m-%d")
                })
                added += 1
                
            db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            db["metadata"]["total_leads"] = len(db["lead_list"])
            with open(leads_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2)
            print(f"[✔] Fallback: Merged {added} new leads into central JSON database.")
            return added

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="Boutique Law Firm")
    parser.add_argument("--loc", default="London")
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    scout = OmniScout()
    scout.hunt(args.niche, args.loc, args.count)
