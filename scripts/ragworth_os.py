import json
import os
import csv
from datetime import datetime
from urllib.parse import urlparse

# Optional PostgreSQL library support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

class RagworthOS:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.base_path, "database")
        self.finance_path = os.path.join(self.base_path, "finance")
        self.leads_file = os.path.join(self.db_path, "leads.json")
        self.ledger_file = os.path.join(self.finance_path, "ledger.csv")
        self.settings_file = os.path.join(self.db_path, "settings.json")
        
        # Determine database connection string (from environment)
        self.db_url = os.getenv("DATABASE_URL", "").strip()
        self.is_sql_active = False
        
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                # Test connection and initialize tables
                self._init_sql_tables()
                self.is_sql_active = True
                print("[✔] Persistent Cloud SQL Database Connected.")
            except Exception as e:
                print(f"[!] Warning: Failed to connect to SQL Database: {e}. Falling back to Local Files.")
                self.is_sql_active = False
        elif self.db_url and not PSYCOPG2_AVAILABLE:
            print("[!] Warning: DATABASE_URL is set but 'psycopg2' is not installed. Falling back to Local Files.")

    def _get_sql_connection(self):
        if not self.db_url:
            return None
        return psycopg2.connect(self.db_url)

    def _init_sql_tables(self):
        """Creates SQL schemas automatically if they do not exist."""
        conn = self._get_sql_connection()
        if not conn:
            return
        
        with conn.cursor() as cur:
            # 1. Leads Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    company VARCHAR(255) UNIQUE,
                    title VARCHAR(255),
                    hq VARCHAR(255),
                    niche VARCHAR(255),
                    email VARCHAR(255),
                    website TEXT,
                    linkedin TEXT,
                    potential_value VARCHAR(100),
                    status VARCHAR(100),
                    confidence REAL,
                    source VARCHAR(100),
                    pain_point TEXT,
                    added_on DATE
                );
            """)
            
            # 2. Ledger Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ledger (
                    id SERIAL PRIMARY KEY,
                    date DATE,
                    invoice_id VARCHAR(255) UNIQUE,
                    client_name VARCHAR(255),
                    service_type VARCHAR(255),
                    amount_usd REAL,
                    status VARCHAR(100),
                    payment_method VARCHAR(100),
                    tax_id VARCHAR(100),
                    notes TEXT
                );
            """)
            conn.commit()
        conn.close()

    def log_revenue(self, client_name, amount_usd, service_type, notes=""):
        date = datetime.now().strftime("%Y-%m-%d")
        invoice_id = f"RAG-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO ledger (date, invoice_id, client_name, service_type, amount_usd, status, payment_method, tax_id, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (invoice_id) DO NOTHING;
                    """, (date, invoice_id, client_name, service_type, amount_usd, "Paid", "Wire Transfer", "N/A", notes))
                    conn.commit()
                conn.close()
                print(f"[✔] Recorded ${amount_usd:.2f} cloud revenue from {client_name}.")
                return invoice_id
            except Exception as e:
                print(f"[!] Cloud SQL Log Revenue failed: {e}. Attempting local write...")
        
        # Local Fallback Write
        row = [date, invoice_id, client_name, service_type, f"{amount_usd:.2f}", "Paid", "Wire Transfer", "N/A", notes]
        os.makedirs(self.finance_path, exist_ok=True)
        file_exists = os.path.exists(self.ledger_file)
        
        with open(self.ledger_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(self.ledger_file) == 0:
                writer.writerow(["Date","Invoice_ID","Client_Name","Service_Type","Amount_USD","Status","Payment_Method","Tax_ID","Notes"])
            writer.writerow(row)
            
        print(f"[✔] Recorded ${amount_usd:.2f} local revenue from {client_name}.")
        return invoice_id

    def get_leads(self):
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                leads = []
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM leads ORDER BY id DESC;")
                    rows = cur.fetchall()
                    for r in rows:
                        leads.append({
                            "name": r["name"],
                            "company": r["company"],
                            "title": r["title"],
                            "hq": r["hq"],
                            "niche": r["niche"],
                            "email": r["email"],
                            "website": r["website"],
                            "linkedin": r["linkedin"],
                            "potential_value": r["potential_value"],
                            "status": r["status"],
                            "confidence": r["confidence"],
                            "source": r["source"],
                            "pain_point": r["pain_point"],
                            "added_on": str(r["added_on"])
                        })
                conn.close()
                return leads
            except Exception as e:
                print(f"[!] Cloud SQL Fetch Leads failed: {e}. Falling back to local...")

        # Local Fallback Read
        if not os.path.exists(self.leads_file):
            return []
        try:
            with open(self.leads_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("lead_list", [])
        except Exception as e:
            print(f"[!] Error loading local leads: {e}")
            return []

    def get_ledger(self):
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                ledger_entries = []
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM ledger ORDER BY id DESC;")
                    rows = cur.fetchall()
                    for r in rows:
                        ledger_entries.append({
                            "Date": str(r["date"]),
                            "Invoice_ID": r["invoice_id"],
                            "Client_Name": r["client_name"],
                            "Service_Type": r["service_type"],
                            "Amount_USD": str(r["amount_usd"]),
                            "Status": r["status"],
                            "Payment_Method": r["payment_method"],
                            "Tax_ID": r["tax_id"],
                            "Notes": r["notes"]
                        })
                conn.close()
                return ledger_entries
            except Exception as e:
                print(f"[!] Cloud SQL Fetch Ledger failed: {e}. Falling back to local...")

        # Local Fallback Read
        if not os.path.exists(self.ledger_file):
            return []
        
        ledger_entries = []
        try:
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Date") and not row["Date"].startswith("#"):
                        ledger_entries.append(row)
            return ledger_entries
        except Exception as e:
            print(f"[!] Error loading local ledger: {e}")
            return []

    def delete_ledger_entry(self, invoice_id):
        """Deletes a ledger entry by invoice_id from either SQL DB or local CSV fallback."""
        deleted = False
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM ledger WHERE invoice_id = %s;", (invoice_id,))
                    if cur.rowcount > 0:
                        deleted = True
                    conn.commit()
                conn.close()
                if deleted:
                    print(f"[✔] Deleted cloud ledger entry {invoice_id}.")
            except Exception as e:
                print(f"[!] Cloud SQL Delete Ledger failed: {e}. Attempting local delete...")

        # Always clean up local CSV as well (for local copy integrity/fallback parity)
        if os.path.exists(self.ledger_file):
            try:
                updated_rows = []
                headers = []
                local_found = False
                with open(self.ledger_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    try:
                        headers = next(reader)
                    except StopIteration:
                        pass
                    for row in reader:
                        if len(row) > 1 and row[1] == invoice_id:
                            local_found = True
                            continue
                        updated_rows.append(row)

                if local_found:
                    with open(self.ledger_file, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        if headers:
                            writer.writerow(headers)
                        writer.writerows(updated_rows)
                    print(f"[✔] Deleted local ledger entry {invoice_id}.")
                    deleted = True
            except Exception as e:
                print(f"[!] Error updating local ledger CSV for delete: {e}")

        return deleted

    def update_ledger_entry(self, invoice_id, client_name, amount_usd, service_type, notes, date=None, status=None):
        """Updates a ledger entry by invoice_id in either SQL DB or local CSV fallback."""
        updated = False
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    # Retrieve existing values to preserve if not passed
                    cur.execute("SELECT date, status FROM ledger WHERE invoice_id = %s;", (invoice_id,))
                    row = cur.fetchone()
                    if row:
                        db_date = date if date else row[0]
                        db_status = status if status else row[1]
                        
                        cur.execute("""
                            UPDATE ledger 
                            SET client_name = %s, amount_usd = %s, service_type = %s, notes = %s, date = %s, status = %s
                            WHERE invoice_id = %s;
                        """, (client_name, amount_usd, service_type, notes, db_date, db_status, invoice_id))
                        if cur.rowcount > 0:
                            updated = True
                        conn.commit()
                conn.close()
                if updated:
                    print(f"[✔] Updated cloud ledger entry {invoice_id}.")
            except Exception as e:
                print(f"[!] Cloud SQL Update Ledger failed: {e}. Attempting local update...")

        # Always sync or fallback to local CSV file
        if os.path.exists(self.ledger_file):
            try:
                updated_rows = []
                headers = []
                local_found = False
                with open(self.ledger_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    try:
                        headers = next(reader)
                    except StopIteration:
                        pass
                    
                    # Columns in ledger.csv:
                    # 0: Date, 1: Invoice_ID, 2: Client_Name, 3: Service_Type, 4: Amount_USD, 5: Status, 6: Payment_Method, 7: Tax_ID, 8: Notes
                    for row in reader:
                        if len(row) > 1 and row[1] == invoice_id:
                            local_found = True
                            if len(row) > 8:
                                # Date
                                row[0] = date if date else row[0]
                                # Client Name
                                row[2] = client_name
                                # Service Type
                                row[3] = service_type
                                # Amount_USD
                                row[4] = f"{amount_usd:.2f}"
                                # Status
                                if status:
                                    row[5] = status
                                # Notes
                                row[8] = notes
                        updated_rows.append(row)

                if local_found:
                    with open(self.ledger_file, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        if headers:
                            writer.writerow(headers)
                        writer.writerows(updated_rows)
                    print(f"[✔] Updated local ledger entry {invoice_id}.")
                    updated = True
            except Exception as e:
                print(f"[!] Error updating local ledger CSV for update: {e}")

        return updated

    def add_scouted_leads(self, new_leads):
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                added = 0
                with conn.cursor() as cur:
                    for lead in new_leads:
                        company = lead.get("company", "")
                        if not company: continue
                        
                        cur.execute("""
                            INSERT INTO leads (name, company, title, hq, niche, email, website, linkedin, potential_value, status, confidence, source, pain_point, added_on)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (company) DO NOTHING;
                        """, (
                            lead.get("name") or f"{lead.get('first_name', 'Decision')} {lead.get('last_name', 'Maker')}".strip(),
                            company,
                            lead.get("title") or "Owner/Partner",
                            lead.get("location") or lead.get("hq") or "Unknown",
                            lead.get("niche") or "Target Profile",
                            lead.get("email") or (f"contact@{lead.get('domain')}" if lead.get("domain") else "info@company.com"),
                            lead.get("website") or (f"https://{lead.get('domain')}" if lead.get("domain") else ""),
                            lead.get("linkedin") or "",
                            lead.get("potential_value") or "$15,000+",
                            lead.get("status") or "Scouted",
                            float(lead.get("confidence") or lead.get("intelligence_score") or 0.5),
                            lead.get("source") or "Scout",
                            lead.get("pain_point") or lead.get("pain_points") or "Manual business vulnerabilities",
                            datetime.now().strftime("%Y-%m-%d")
                        ))
                        added += cur.rowcount
                    conn.commit()
                conn.close()
                print(f"[✔] Merged {added} new leads into Cloud SQL database.")
                return added
            except Exception as e:
                print(f"[!] Cloud SQL Merge Leads failed: {e}. Falling back to local...")

        # Local Fallback Write
        if not os.path.exists(self.leads_file):
            return 0
            
        try:
            with open(self.leads_file, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            existing = {l.get("company", "").lower() for l in db.get("lead_list", [])}
            added = 0
            for lead in new_leads:
                company = lead.get("company", "")
                if not company or company.lower() in existing: 
                    continue
                
                db["lead_list"].append({
                    "name": lead.get("name") or f"{lead.get('first_name', 'Decision')} {lead.get('last_name', 'Maker')}".strip(),
                    "company": company,
                    "title": lead.get("title") or "Owner/Partner",
                    "hq": lead.get("location") or lead.get("hq") or "Unknown",
                    "niche": lead.get("niche") or "Target Profile",
                    "email": lead.get("email") or (f"contact@{lead.get('domain')}" if lead.get("domain") else "info@company.com"),
                    "website": lead.get("website") or (f"https://{lead.get('domain')}" if lead.get("domain") else ""),
                    "linkedin": lead.get("linkedin") or "",
                    "potential_value": lead.get("potential_value") or "$15,000+",
                    "status": lead.get("status") or "Scouted",
                    "source": lead.get("source") or "Scout",
                    "confidence": lead.get("confidence") or lead.get("intelligence_score") or 0.5,
                    "pain_point": lead.get("pain_point") or lead.get("pain_points") or "Manual business vulnerabilities",
                    "added_on": datetime.now().strftime("%Y-%m-%d")
                })
                added += 1
                existing.add(company.lower())
                
            db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            db["metadata"]["total_leads"] = len(db["lead_list"])
            
            with open(self.leads_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2)
            print(f"[✔] Merged {added} new leads into local leads.json database.")
            return added
        except Exception as e:
            print(f"[!] Error loading/saving local database leads: {e}")
            return 0

    def get_summary(self):
        total_rev = 0.0
        ledger = self.get_ledger()
        for row in ledger:
            try:
                total_rev += float(row.get("Amount_USD", 0.0))
            except:
                pass
        
        leads = self.get_leads()
        
        return {
            "total_revenue": round(total_rev, 2),
            "active_leads": len(leads),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "systems_health": "100%"
        }

if __name__ == "__main__":
    os_sys = RagworthOS()
    summary = os_sys.get_summary()
    print(f"--- Ragworth Executive Summary ---")
    print(f"SQL Database Mode: {os_sys.is_sql_active}")
    print(f"Revenue: ${summary['total_revenue']}")
    print(f"Leads: {summary['active_leads']}")
