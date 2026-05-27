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
        self.employees_file = os.path.join(self.db_path, "employees.json")
        
        # Determine database connection string (from environment)
        self.db_url = os.getenv("DATABASE_URL", "").strip()
        self.is_sql_active = False
        
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                # Test connection and initialize tables
                self._init_sql_tables()
                self.is_sql_active = True
                print("[OK] Persistent Cloud SQL Database Connected.")
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
            
            # 3. Employees Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    emp_id VARCHAR(100) UNIQUE,
                    name VARCHAR(255),
                    role VARCHAR(255),
                    email VARCHAR(255),
                    clearance VARCHAR(100),
                    status VARCHAR(100),
                    joined_date DATE
                );
            """)
            
            # Auto-seed Hermes Personal Assistant
            cur.execute("SELECT COUNT(*) FROM employees WHERE emp_id = 'EMP-HERMES';")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO employees (emp_id, name, role, email, clearance, status, joined_date)
                    VALUES ('EMP-HERMES', 'Hermes', 'Personal Assistant (AI Core)', 'hermes@ragon.co', 'FULL CONTROL (LEVEL 5)', 'Online', CURRENT_DATE);
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
                print(f"[OK] Recorded ${amount_usd:.2f} cloud revenue from {client_name}.")
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
            
        print(f"[OK] Recorded ${amount_usd:.2f} local revenue from {client_name}.")
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
                    print(f"[OK] Deleted cloud ledger entry {invoice_id}.")
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
                    print(f"[OK] Deleted local ledger entry {invoice_id}.")
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
                    print(f"[OK] Updated cloud ledger entry {invoice_id}.")
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
                    print(f"[OK] Updated local ledger entry {invoice_id}.")
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
                print(f"[OK] Merged {added} new leads into Cloud SQL database.")
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
            print(f"[OK] Merged {added} new leads into local leads.json database.")
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

    def get_employees(self):
        """Retrieves employee lists from SQL DB or fallback local employees.json."""
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                employees = []
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM employees ORDER BY id ASC;")
                    rows = cur.fetchall()
                    for r in rows:
                        employees.append({
                            "emp_id": r["emp_id"],
                            "name": r["name"],
                            "role": r["role"],
                            "email": r["email"],
                            "clearance": r["clearance"],
                            "status": r["status"],
                            "joined_date": str(r["joined_date"])
                        })
                conn.close()
                return employees
            except Exception as e:
                print(f"[!] Cloud SQL Fetch Employees failed: {e}. Falling back to local...")

        # Local Fallback
        if not os.path.exists(self.employees_file):
            # Seed local file
            default_data = {
                "employees": [
                    {
                        "emp_id": "EMP-HERMES",
                        "name": "Hermes",
                        "role": "Personal Assistant (AI Core)",
                        "email": "hermes@ragon.co",
                        "clearance": "FULL CONTROL (LEVEL 5)",
                        "status": "Online",
                        "joined_date": datetime.now().strftime("%Y-%m-%d")
                    }
                ],
                "metadata": {
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "total_employees": 1
                }
            }
            try:
                os.makedirs(os.path.dirname(self.employees_file), exist_ok=True)
                with open(self.employees_file, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, indent=2)
            except Exception as ex:
                print(f"[!] Failed to seed local employees.json: {ex}")
            return default_data["employees"]

        try:
            with open(self.employees_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Failsafe check to ensure Hermes is seeded in local list if empty
            emp_list = data.get("employees", [])
            if not any(emp.get("emp_id") == "EMP-HERMES" for emp in emp_list):
                emp_list.insert(0, {
                    "emp_id": "EMP-HERMES",
                    "name": "Hermes",
                    "role": "Personal Assistant (AI Core)",
                    "email": "hermes@ragon.co",
                    "clearance": "FULL CONTROL (LEVEL 5)",
                    "status": "Online",
                    "joined_date": datetime.now().strftime("%Y-%m-%d")
                })
                data["employees"] = emp_list
                data["metadata"]["total_employees"] = len(emp_list)
                with open(self.employees_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            return emp_list
        except Exception as e:
            print(f"[!] Error loading local employees: {e}")
            return []

    def add_employee(self, name, role, email, clearance, status):
        """Adds a new employee record."""
        emp_id = f"EMP-{datetime.now().strftime('%M%S%f')[:6]}"
        date = datetime.now().strftime("%Y-%m-%d")

        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO employees (emp_id, name, role, email, clearance, status, joined_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (emp_id, name, role, email, clearance, status, date))
                    conn.commit()
                conn.close()
                print(f"[OK] Recorded cloud employee: {name} ({emp_id}).")
            except Exception as e:
                print(f"[!] Cloud SQL Add Employee failed: {e}. Writing local fallback...")

        # Sync to local
        try:
            if os.path.exists(self.employees_file):
                with open(self.employees_file, "r", encoding="utf-8") as f:
                    db = json.load(f)
            else:
                db = {"employees": [], "metadata": {}}

            # Deduplicate by email
            existing_emails = {emp.get("email", "").lower() for emp in db.get("employees", [])}
            if email.lower() in existing_emails:
                print(f"[!] Employee email {email} already exists.")
                return False

            db.setdefault("employees", []).append({
                "emp_id": emp_id,
                "name": name,
                "role": role,
                "email": email,
                "clearance": clearance,
                "status": status,
                "joined_date": date
            })
            db.setdefault("metadata", {})
            db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            db["metadata"]["total_employees"] = len(db["employees"])

            with open(self.employees_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2)
            print(f"[OK] Recorded local employee: {name} ({emp_id}).")
            return emp_id
        except Exception as e:
            print(f"[!] Error writing local employee: {e}")
            return False

    def update_employee(self, emp_id, name, role, email, clearance, status):
        """Updates employee records (blocks changes that alter Hermes clearance/identity)."""
        if emp_id == "EMP-HERMES":
            # Hardcoded identity lock for sovereign AI Core
            name = "Hermes"
            role = "Personal Assistant (AI Core)"
            email = "hermes@ragon.co"
            clearance = "FULL CONTROL (LEVEL 5)"

        updated = False
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE employees
                        SET name = %s, role = %s, email = %s, clearance = %s, status = %s
                        WHERE emp_id = %s;
                    """, (name, role, email, clearance, status, emp_id))
                    if cur.rowcount > 0:
                        updated = True
                    conn.commit()
                conn.close()
                if updated:
                    print(f"[OK] Updated cloud employee {emp_id}.")
            except Exception as e:
                print(f"[!] Cloud SQL Update Employee failed: {e}. Attempting local update...")

        # Local Update
        if os.path.exists(self.employees_file):
            try:
                with open(self.employees_file, "r", encoding="utf-8") as f:
                    db = json.load(f)
                
                local_found = False
                for emp in db.get("employees", []):
                    if emp.get("emp_id") == emp_id:
                        emp["name"] = name
                        emp["role"] = role
                        emp["email"] = email
                        emp["clearance"] = clearance
                        emp["status"] = status
                        local_found = True
                        break
                
                if local_found:
                    db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    with open(self.employees_file, "w", encoding="utf-8") as f:
                        json.dump(db, f, indent=2)
                    print(f"[OK] Updated local employee {emp_id}.")
                    updated = True
            except Exception as e:
                print(f"[!] Error updating local employee: {e}")
        return updated

    def delete_employee(self, emp_id):
        """Deletes an employee record (explicitly blocks deleting Hermes)."""
        if emp_id == "EMP-HERMES":
            print("[!] Security Violation: Unauthorized attempt to delete sovereign AI Core Assistant blocked.")
            return False

        deleted = False
        if self.is_sql_active:
            try:
                conn = self._get_sql_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM employees WHERE emp_id = %s;", (emp_id,))
                    if cur.rowcount > 0:
                        deleted = True
                    conn.commit()
                conn.close()
                if deleted:
                    print(f"[OK] Deleted cloud employee {emp_id}.")
            except Exception as e:
                print(f"[!] Cloud SQL Delete Employee failed: {e}. Attempting local delete...")

        # Local Delete
        if os.path.exists(self.employees_file):
            try:
                with open(self.employees_file, "r", encoding="utf-8") as f:
                    db = json.load(f)
                
                emp_list = db.get("employees", [])
                initial_len = len(emp_list)
                filtered_list = [emp for emp in emp_list if emp.get("emp_id") != emp_id]
                
                if len(filtered_list) < initial_len:
                    db["employees"] = filtered_list
                    db["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    db["metadata"]["total_employees"] = len(filtered_list)
                    with open(self.employees_file, "w", encoding="utf-8") as f:
                        json.dump(db, f, indent=2)
                    print(f"[OK] Deleted local employee {emp_id}.")
                    deleted = True
            except Exception as e:
                print(f"[!] Error deleting local employee: {e}")
        return deleted

if __name__ == "__main__":
    os_sys = RagworthOS()
    summary = os_sys.get_summary()
    print(f"--- Ragworth Executive Summary ---")
    print(f"SQL Database Mode: {os_sys.is_sql_active}")
    print(f"Revenue: ${summary['total_revenue']}")
    print(f"Leads: {summary['active_leads']}")
