import os
import json
import csv
import sys
from datetime import datetime

class RagworthREI:
    """
    Ragworth Executive Intelligence (REI)
    The central operating system for Ragon Co.
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_dir = os.path.join(self.base_dir, "database")
        self.fin_dir = os.path.join(self.base_dir, "finance")
        self.leads_file = os.path.join(self.db_dir, "leads.json")
        self.ledger_file = os.path.join(self.fin_dir, "ledger.csv")
        self.auth_key = "RAGON2026"

    def authenticate(self):
        print("\n" + "═"*60)
        print(" RAGWORTH EXECUTIVE INTELLIGENCE v1.0")
        print("═"*60)
        key = input("Enter Executive Key: ")
        if key != self.auth_key:
            print("[!] Unauthorized. Access Logged.")
            sys.exit()
        print("[✔] Authorization Successful.")

    def run(self):
        self.authenticate()
        while True:
            print("\n" + "═"*60)
            print(" [ RAGWORTH OPERATING SYSTEM ]")
            print("═"*60)
            print(" [1] CEO DASHBOARD       (Revenue, Leads, KPIs)")
            print(" [2] LOG REVENUE         (Capture Payments)")
            print(" [3] INTELLIGENCE SCOUT  (Global / Targeted / Maps)")
            print(" [4] EXIT SESSION")
            print("═"*60)
            
            cmd = input("Select Protocol: ").strip()
            
            if cmd == "1": 
                self.show_dashboard()
            elif cmd == "2": 
                self.log_payment()
            elif cmd == "3":
                print("\n[ INTELLIGENCE PROTOCOLS ]")
                print(" A. OMNISCALE  (Global Tech-Debt / AI Gap)")
                print(" B. OMNISCOUT  (Targeted Persona Triangulation)")
                sub = input("Select Scout Mode [A/B]: ").strip().upper()
                if sub == "A": 
                    self.scout_omniscale()
                elif sub == "B": 
                    self.scout_omni()
            elif cmd == "4":
                print("\n[✔] Session closed. Ragworth standing by.\n")
                break
            else: 
                print("[!] Invalid Protocol.")

    def show_dashboard(self):
        total_rev = 0.0
        try:
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Amount_USD") and not row["Amount_USD"].startswith("#"):
                        total_rev += float(row["Amount_USD"])
        except Exception as e:
            pass

        try:
            with open(self.leads_file, "r", encoding="utf-8") as f:
                leads = json.load(f).get("lead_list", [])
        except:
            leads = []

        print("\n" + "═"*60)
        print(" [ RAGWORTH EXECUTIVE SUMMARY ]")
        print("═"*60)
        print(f" Revenue (MRR): ${total_rev:.2f}")
        print(f" Target Goal:   $100,000.00")
        print(f" Active Leads:  {len(leads)}")
        print(f" Systems:       100% SECURE & OPERATIONAL")
        print("═"*60)

    def log_payment(self):
        client = input("Client Name: ").strip()
        amount = input("Amount (USD): ").strip()
        service = input("Service Type: ").strip()
        notes = input("Notes: ").strip()

        if not client or not amount or not service:
            print("[!] Invalid details.")
            return

        date = datetime.now().strftime("%Y-%m-%d")
        invoice_id = f"RAG-{datetime.now().strftime('%Y%m%d%H%M')}"
        row = [date, invoice_id, client, service, amount, "Paid", "Wire Transfer", "N/A", notes]

        with open(self.ledger_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print(f"[✔] Successfully recorded ${amount} revenue.")

    def scout_omniscale(self):
        print("\n[*] Initializing OmniScale search...")
        from ragworth_omniscale import OmniScale
        scale = OmniScale()
        scale.run_pulse(count=5)

    def scout_omni(self):
        niche = input("Target Niche [Boutique Law Firm]: ").strip() or "Boutique Law Firm"
        loc = input("Target Location [London]: ").strip() or "London"
        print("\n[*] Initializing OmniScout triangulation...")
        from ragworth_omniscout import OmniScout
        scout = OmniScout()
        scout.hunt(niche=niche, location=loc, count=5)

if __name__ == "__main__":
    rei = RagworthREI()
    rei.run()
