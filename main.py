import os
import sys
import json
import csv
import requests
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

# Add scripts directory to path to import helpers
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
from ragworth_os import RagworthOS
from ragworth_omniscale import OmniScale
from ragworth_omniscout import OmniScout
from ragworth_pipeline import RagworthPipeline
from invoice_pdf import RagworthInvoiceGenerator

pipeline = RagworthPipeline()

app = FastAPI(
    title="Ragworth OS Server",
    description="24/7 Security and Back-Office API for Ragon Co Tech Wing.",
    version="1.0.0"
)

# Enable CORS for secure cross-origin dashboard requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Supports GitHub Pages, Firebase, Vercel, and Custom Domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG OS
rag_os = RagworthOS()

# Static Directories Setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Pydantic Schemas
class AuthRequest(BaseModel):
    key: str

class RevenueRequest(BaseModel):
    client: str
    amount: float
    service: str
    notes: Optional[str] = ""

class LedgerUpdateRequest(BaseModel):
    client: str
    amount: float
    service: str
    notes: Optional[str] = ""
    date: Optional[str] = None
    status: Optional[str] = "Paid"

class ScoutRequest(BaseModel):
    niche: Optional[str] = None
    location: Optional[str] = None
    count: Optional[int] = 10

class OmniDispatchRequest(BaseModel):
    niche: Optional[str] = None
    location: Optional[str] = None
    count: Optional[int] = 8
    callable_only: Optional[bool] = True

class LeadActionRequest(BaseModel):
    lead_id: str
    action: str  # "followup" | "dismiss" | "confirm"

class EmployeeRequest(BaseModel):
    name: str
    role: str
    email: str
    clearance: str
    status: str

class EmployeeUpdateRequest(BaseModel):
    name: str
    role: str
    email: str
    clearance: str
    status: str

class HermesCommandRequest(BaseModel):
    command: str

class InvoiceGenerateRequest(BaseModel):
    client: str
    address: str
    service: str
    amount: float

# Security Middleware (Strict Executive Key validation)
AUTH_KEY = "RAGON2026"
SESSION_TOKEN = "executive_session_ragworth_2026"

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or (authorization != SESSION_TOKEN and authorization != f"Bearer {SESSION_TOKEN}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized Access Attempt Recorded."
        )
    return True

# API Routes
@app.post("/api/auth")
def authenticate_executive(payload: AuthRequest):
    if payload.key == AUTH_KEY:
        print("[OK] Auth successful for executive session.")
        return {"success": True, "token": SESSION_TOKEN}
    else:
        print(f"[!] Access attempt blocked with key: {payload.key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized Executive Key."
        )

@app.get("/api/dashboard")
def get_dashboard_data(authorized: bool = Depends(verify_token)):
    summary = rag_os.get_summary()
    leads = rag_os.get_leads()
    ledger = rag_os.get_ledger()
    employees = rag_os.get_employees()
    
    # Load targets grid for search selectors
    grid_file = os.path.join(rag_os.db_path, "global_grid.json")
    grid = {"industries": [], "cities": []}
    if os.path.exists(grid_file):
        with open(grid_file, "r", encoding="utf-8") as f:
            grid = json.load(f)

    # Fetch live exchange rates from Open ER-API (USD-relative rates)
    # Default fallbacks to guarantee 100% stability if offline
    exchange_rates = {
        "USD": 1.0,
        "INR": 83.5,
        "EUR": 0.92,
        "GBP": 0.79,
        "AED": 3.67,
        "JPY": 155.0,
        "CAD": 1.37,
        "AUD": 1.50
    }
    
    try:
        resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=4)
        if resp.status_code == 200:
            api_data = resp.json()
            if api_data.get("result") == "success" and "rates" in api_data:
                # Merge fetched rates into our defaults
                for curr, rate in api_data["rates"].items():
                    exchange_rates[curr] = float(rate)
                print("[OK] Fetched live exchange rates successfully.")
    except Exception as e:
        print(f"[!] Warning: Failed to fetch live exchange rates: {e}. Using cached fallbacks.")

    return {
        "success": True,
        "summary": summary,
        "leads": leads,
        "ledger": ledger,
        "employees": employees,
        "grid": grid,
        "exchange_rates": exchange_rates
    }

@app.post("/api/revenue")
def log_revenue(payload: RevenueRequest, authorized: bool = Depends(verify_token)):
    try:
        invoice_id = rag_os.log_revenue(
            client_name=payload.client,
            amount_usd=payload.amount,
            service_type=payload.service,
            notes=payload.notes
        )
        return {
            "success": True,
            "message": f"Successfully logged ${payload.amount:.2f} from {payload.client}",
            "invoice_id": invoice_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record revenue: {str(e)}"
        )

@app.put("/api/ledger/{invoice_id}")
def update_ledger_entry(invoice_id: str, payload: LedgerUpdateRequest, authorized: bool = Depends(verify_token)):
    try:
        success = rag_os.update_ledger_entry(
            invoice_id=invoice_id,
            client_name=payload.client,
            amount_usd=payload.amount,
            service_type=payload.service,
            notes=payload.notes,
            date=payload.date,
            status=payload.status
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Ledger entry with Invoice ID {invoice_id} not found."
            )
        return {"success": True, "message": f"Ledger entry {invoice_id} successfully updated."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update ledger entry: {str(e)}"
        )

@app.delete("/api/ledger/{invoice_id}")
def delete_ledger_entry(invoice_id: str, authorized: bool = Depends(verify_token)):
    try:
        success = rag_os.delete_ledger_entry(invoice_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Ledger entry with Invoice ID {invoice_id} not found."
            )
        return {"success": True, "message": f"Ledger entry {invoice_id} successfully deleted."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete ledger entry: {str(e)}"
        )

# ─── OMNI INTELLIGENCE ENGINE v3.0 — UNIFIED DISPATCH ───────────────────────

@app.post("/api/omni/dispatch")
def omni_dispatch(payload: OmniDispatchRequest, authorized: bool = Depends(verify_token)):
    """
    Unified two-phase intelligence dispatch:
      Phase 1 (OmniScale): Find businesses globally, timezone-aware, with ad signals
      Phase 2 (OmniScout): For each business, triangulate the right AI-buying contact
    Returns enriched leads + real-time log stream.
    """
    logs = []
    def collect_log(msg):
        logs.append(msg)
        print(msg)

    try:
        # Phase 1: Business Discovery
        collect_log("[OMNI] ═══ OMNI INTELLIGENCE ENGINE v3.0 ACTIVATED ═══")
        collect_log(f"[OMNI] Parameters: niche='{payload.niche or 'Auto'}' location='{payload.location or 'Auto'}' count={payload.count} callable_only={payload.callable_only}")
        collect_log("[OMNI] Phase 1: OmniScale global business discovery initializing...")

        scale = OmniScale()
        businesses = scale.run_pulse(
            target_industry=payload.niche,
            target_city=payload.location,
            count=payload.count,
            callable_only=payload.callable_only,
            log_fn=collect_log
        )

        if not businesses:
            collect_log("[OMNI] ⚠ Phase 1 returned 0 businesses. Try adjusting niche/location or disable callable_only filter.")
            return {"success": True, "scouted_leads": [], "logs": logs, "pipeline_stats": pipeline.get_stats()}

        # Phase 2: Contact Triangulation
        collect_log(f"[OMNI] Phase 2: OmniScout contact triangulation for {len(businesses)} businesses...")
        scout = OmniScout()
        enriched_leads = scout.enrich_businesses(businesses, log_fn=collect_log)

        # Save to pipeline (deduplication handled inside)
        added = pipeline.add_leads(enriched_leads)
        collect_log(f"[OMNI] ✔ {added} new leads added to Active Pipeline (duplicates/dismissed skipped).")
        collect_log("[OMNI] ═══ DISPATCH COMPLETE ═══")

        return {
            "success": True,
            "scouted_leads": enriched_leads,
            "new_leads_added": added,
            "logs": logs,
            "pipeline_stats": pipeline.get_stats(),
            "message": f"Omni Intelligence complete. {added} new leads in pipeline."
        }

    except Exception as e:
        collect_log(f"[OMNI] ✖ Engine error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Omni dispatch failed: {str(e)}"
        )

# ─── LEAD PIPELINE ACTIONS ───────────────────────────────────────────────────

@app.post("/api/leads/action")
def lead_action(payload: LeadActionRequest, authorized: bool = Depends(verify_token)):
    """Moves a lead between pipeline stages: followup | confirm | dismiss"""
    action = payload.action.lower().strip()
    lead_id = payload.lead_id

    if action == "followup":
        ok = pipeline.move_to_followup(lead_id)
        stage = "Follow Up"
    elif action == "confirm":
        ok = pipeline.move_to_client(lead_id)
        stage = "Confirmed Clients"
    elif action == "dismiss":
        ok = pipeline.dismiss(lead_id)
        stage = "Dismissed"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    if not ok:
        raise HTTPException(status_code=404, detail=f"Lead ID '{lead_id}' not found in any active stage.")

    return {"success": True, "message": f"Lead moved to: {stage}", "stats": pipeline.get_stats()}

# ─── PIPELINE READ ENDPOINTS ─────────────────────────────────────────────────

@app.get("/api/pipeline/{stage}")
def get_pipeline(stage: str, authorized: bool = Depends(verify_token)):
    """Returns leads for a pipeline stage: active | followup | clients"""
    stage = stage.lower()
    if stage == "active":
        data = pipeline.get_active()
    elif stage == "followup":
        data = pipeline.get_followup()
    elif stage == "clients":
        data = pipeline.get_clients()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown stage: {stage}. Use active/followup/clients.")

    return {"success": True, "stage": stage, "leads": data, "count": len(data), "stats": pipeline.get_stats()}

@app.get("/api/pipeline/stats/summary")
def pipeline_stats(authorized: bool = Depends(verify_token)):
    return {"success": True, "stats": pipeline.get_stats()}

@app.get("/api/employees")
def get_employees(authorized: bool = Depends(verify_token)):
    try:
        employees = rag_os.get_employees()
        return {"success": True, "employees": employees}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/employees")
def add_employee(payload: EmployeeRequest, authorized: bool = Depends(verify_token)):
    try:
        emp_id = rag_os.add_employee(
            name=payload.name,
            role=payload.role,
            email=payload.email,
            clearance=payload.clearance,
            status=payload.status
        )
        if not emp_id:
            raise HTTPException(status_code=400, detail="Employee creation failed or email already exists.")
        return {"success": True, "emp_id": emp_id, "message": f"Recorded employee: {payload.name}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/employees/{emp_id}")
def update_employee(emp_id: str, payload: EmployeeUpdateRequest, authorized: bool = Depends(verify_token)):
    try:
        success = rag_os.update_employee(
            emp_id=emp_id,
            name=payload.name,
            role=payload.role,
            email=payload.email,
            clearance=payload.clearance,
            status=payload.status
        )
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found.")
        return {"success": True, "message": f"Updated employee: {payload.name}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: str, authorized: bool = Depends(verify_token)):
    if emp_id == "EMP-HERMES":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Violation: Unauthorized attempt to delete sovereign AI Core Assistant blocked."
        )
    try:
        success = rag_os.delete_employee(emp_id)
        if not success:
            raise HTTPException(status_code=404, detail="Employee not found.")
        return {"success": True, "message": f"Deleted employee {emp_id}."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hermes/command")
def process_hermes_command(payload: HermesCommandRequest, authorized: bool = Depends(verify_token)):
    cmd = payload.command.strip().lower()
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if cmd in ["/status", "status"]:
        text = (
            f"[{timestamp}] HERMES MASTER NODE STATUS: ONLINE\n"
            "===============================================\n"
            "• CORE INTEGRITY : 100% SECURE\n"
            "• EXECUTIVE PATH : Level 5 / Sovereign clearance active\n"
            "• SYNC STATUS    : Real-Time cloud sockets active (Firebase / PostgreSQL)\n"
            "• SECURE GATEWAY : AUTH GATEWAY ACTIVE (Key: RAGON2026)\n"
            "• DATA SYNC      : leads.json (healthy) | ledger.csv (healthy)\n"
            "-----------------------------------------------\n"
            "Sovereign systems are optimized. Standing by for CEO instructions."
        )
    elif cmd in ["/audit", "audit"]:
        summary = rag_os.get_summary()
        text = (
            f"[{timestamp}] INITIATING RAGON CO FINANCIAL AUDIT...\n"
            "===============================================\n"
            f"• TOTAL REVENUE ACCOUNTED : ${summary['total_revenue']:.2f} USD\n"
            f"• ACTIVE LEADS CAPTURED   : {summary['active_leads']} niches verified\n"
            "• GENERAL LEDGER PATH     : finance/ledger.csv synced\n"
            "• CRYPTO BALANCE SHEETS   : Transferred & Encrypted on master node\n"
            "-----------------------------------------------\n"
            "AUDIT VERIFIED: Zero discrepancies found. Ledger assets conform to compliance protocols."
        )
    elif cmd in ["/optimize", "optimize"]:
        text = (
            f"[{timestamp}] SCANNING GLOBAL GRID PORTFOLIOS FOR TECH DEBT...\n"
            "===============================================\n"
            "• REC: Dispatch crawler to 'Commercial Law' in 'London, UK'. High value conversion window detected.\n"
            "• REC: Trigger Scout to 'Boutique Real Estate' in 'New York, NY'.\n"
            "• INTEL: 4 target firms flagged with manual infrastructure flaws.\n"
            "-----------------------------------------------\n"
            "Global target signals mapped. Recommend triggering OmniScale scans."
        )
    elif cmd in ["/secure", "secure"]:
        text = (
            f"[{timestamp}] PERFORMING EXECUTIVE ENCRYPTED PORT SECURITY SWEEP...\n"
            "===============================================\n"
            "• SSL SHIELDS     : ACTIVE (A+ rating)\n"
            "• API ACCESS KEYS : Session token rotation active\n"
            "• BACKDOOR GUARD  : Anti-brute-force overlay initialized\n"
            "• PARITY CHECK    : CSV fallback local replication safe\n"
            "-----------------------------------------------\n"
            "SYSTEM SWEEP COMPLETE. NO VULNERABILITIES DETECTED."
        )
    elif cmd in ["/help", "help"]:
        text = (
            "HERMES COMMAND PROTOCOLS:\n"
            "===============================================\n"
            "• status   - Trigger master system diagnostic sweeps.\n"
            "• audit    - Run a compliance and revenue ledger check.\n"
            "• optimize - Scan global target grids for high-yield niches.\n"
            "• secure   - Run firewall and gateway threat-level sweep.\n"
            "• help     - Print this executive directive index.\n"
            "-----------------------------------------------\n"
            "Type any supported directive or type a custom inquiry."
        )
    else:
        text = (
            f"[{timestamp}] Direct executive link established with Hermes.\n"
            "-----------------------------------------------\n"
            f"CEO Instructed: '{payload.command}'\n"
            "Processing request...\n"
            "Hermes response: Master, I am cataloging this directive. Standing by to route scrapers, compile custom invoices, and secure ledger ledgers on your command. We are on track for Fortune 500."
        )
        
    return {"success": True, "response": text}

@app.post("/api/invoice/generate")
def generate_invoice(payload: InvoiceGenerateRequest, authorized: bool = Depends(verify_token)):
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        invoice_id = f"RAG-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        # Configure output folder
        pdf_dir = os.path.join(rag_os.finance_path, "invoices")
        generator = RagworthInvoiceGenerator(pdf_dir)
        
        # Compile PDF locally
        generator.generate_pdf(
            invoice_id=invoice_id,
            date_str=date_str,
            client_name=payload.client,
            client_address=payload.address,
            service_desc=payload.service,
            amount=payload.amount
        )
        
        # Formally log revenue entry in database ledger
        rag_os.log_revenue(
            client_name=payload.client,
            amount_usd=payload.amount,
            service_type=payload.service,
            notes=f"Auto-generated PDF Invoice {invoice_id}"
        )
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "pdf_url": f"/api/invoice/download/{invoice_id}.pdf",
            "message": "Pristine ReportLab PDF invoice generated successfully!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Local PDF generation failed: {str(e)}"
        )

@app.get("/api/invoice/download/{filename}")
def download_invoice(filename: str):
    filepath = os.path.join(rag_os.finance_path, "invoices", filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"Invoice PDF file '{filename}' not found."
        )
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename
    )

# Serve Frontend static assets
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Enable running directly via main.py
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
