import requests
import json
import os

def run_test():
    base_url = "http://127.0.0.1:8000"
    
    print("[*] Testing authentication gateway...")
    auth_resp = requests.post(f"{base_url}/api/auth", json={"key": "RAGON2026"})
    if auth_resp.status_code != 200:
        print(f"[!] Authentication failed: {auth_resp.text}")
        return
    
    token = auth_resp.json()["token"]
    print(f"[OK] Authenticated successfully. Token: {token}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "client": "Sterling & Associates Law",
        "address": "London, United Kingdom",
        "service": "Agentic Compliance Workflow Setup & CRM Integration Services",
        "amount": 15000.00
    }
    
    print("[*] Triggering local PDF invoice generation...")
    gen_resp = requests.post(f"{base_url}/api/invoice/generate", json=payload, headers=headers)
    if gen_resp.status_code != 200:
        print(f"[!] PDF Generation failed: {gen_resp.text}")
        return
        
    gen_data = gen_resp.json()
    print(f"[OK] Invoice generated: {json.dumps(gen_data, indent=2)}")
    
    pdf_url = gen_data["pdf_url"]
    invoice_id = gen_data["invoice_id"]
    
    print(f"[*] Downloading generated PDF from: {base_url}{pdf_url}")
    download_resp = requests.get(f"{base_url}{pdf_url}")
    if download_resp.status_code != 200:
        print(f"[!] Failed to download PDF: {download_resp.text}")
        return
        
    os.makedirs("test_outputs", exist_ok=True)
    pdf_path = f"test_outputs/{invoice_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(download_resp.content)
        
    print(f"[OK] PDF downloaded successfully and saved to: {pdf_path}")
    print(f"[OK] File size: {len(download_resp.content)} bytes.")
    
    print("[*] Verifying if ledger record is correctly synced...")
    dash_resp = requests.get(f"{base_url}/api/dashboard", headers=headers)
    if dash_resp.status_code == 200:
        ledger = dash_resp.json().get("ledger", [])
        matched = [entry for entry in ledger if entry.get("Invoice_ID") == invoice_id]
        if matched:
            print(f"[OK] Ledger successfully verified! Entry details: {json.dumps(matched[0], indent=2)}")
        else:
            print("[!] Ledger entry not found in active records.")
    else:
        print(f"[!] Failed to fetch dashboard metrics: {dash_resp.text}")

if __name__ == "__main__":
    run_test()
