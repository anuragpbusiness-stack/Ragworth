import os
import sys
import json
import csv
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Add scripts directory to path to import helpers
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))
from ragworth_os import RagworthOS
from ragworth_omniscale import OmniScale
from ragworth_omniscout import OmniScout

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
        print("[✔] Auth successful for executive session.")
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
    
    # Load targets grid for search selectors
    grid_file = os.path.join(rag_os.db_path, "global_grid.json")
    grid = {"industries": [], "cities": []}
    if os.path.exists(grid_file):
        with open(grid_file, "r", encoding="utf-8") as f:
            grid = json.load(f)

    return {
        "success": True,
        "summary": summary,
        "leads": leads,
        "ledger": ledger,
        "grid": grid
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

@app.post("/api/scout/omniscale")
def run_omniscale_pulse(payload: ScoutRequest, authorized: bool = Depends(verify_token)):
    try:
        engine = OmniScale()
        leads = engine.run_pulse(
            target_industry=payload.niche,
            target_city=payload.location,
            count=payload.count
        )
        return {
            "success": True,
            "scouted_leads": leads,
            "message": f"Global scan complete. Discovered {len(leads)} opportunities."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OmniScale pulse failed: {str(e)}"
        )

@app.post("/api/scout/omniscout")
def run_omniscout_hunt(payload: ScoutRequest, authorized: bool = Depends(verify_token)):
    try:
        engine = OmniScout()
        leads = engine.hunt(
            niche=payload.niche or "Boutique Law Firm",
            location=payload.location or "London",
            count=payload.count
        )
        return {
            "success": True,
            "scouted_leads": leads,
            "message": f"OmniScout hunt complete. Captured {len(leads)} validated profiles."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OmniScout hunt failed: {str(e)}"
        )

# Serve Frontend static assets
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Enable running directly via main.py
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
