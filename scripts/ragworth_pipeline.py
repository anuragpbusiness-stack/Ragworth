"""
RAGWORTH PIPELINE v1.0 — 3-STAGE CRM ENGINE
============================================
Manages the full lead lifecycle:
  Active → Follow Up → Confirmed Client
  Active → Dismissed (hidden forever)
"""

import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

PIPELINE_FILE  = DB_DIR / "pipeline.json"   # Active scouted leads
FOLLOWUP_FILE  = DB_DIR / "followup.json"   # Leads marked for follow-up
CLIENTS_FILE   = DB_DIR / "clients.json"    # Confirmed paying clients
DISMISSED_FILE = DB_DIR / "dismissed.json"  # Never show again

def _load(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except:
            return []

def _save(path: Path, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _load_dismissed() -> set:
    if not DISMISSED_FILE.exists():
        return set()
    with open(DISMISSED_FILE, "r", encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except:
            return set()

def _save_dismissed(s: set):
    with open(DISMISSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(s), f, indent=2)


class RagworthPipeline:

    def add_leads(self, leads: list) -> int:
        """Add new leads to active pipeline, skip duplicates and dismissed."""
        existing = _load(PIPELINE_FILE)
        dismissed = _load_dismissed()
        followup_companies = {l.get("company","").lower() for l in _load(FOLLOWUP_FILE)}
        client_companies   = {l.get("company","").lower() for l in _load(CLIENTS_FILE)}
        pipeline_companies = {l.get("company","").lower() for l in existing}

        added = 0
        for lead in leads:
            company_key = lead.get("company", "").lower().strip()
            if not company_key:
                continue
            # Skip if dismissed, already in pipeline, followup, or clients
            if company_key in dismissed:
                continue
            if company_key in pipeline_companies or company_key in followup_companies or company_key in client_companies:
                continue
            lead["pipeline_status"] = "active"
            lead["pipeline_added"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            existing.append(lead)
            pipeline_companies.add(company_key)
            added += 1

        _save(PIPELINE_FILE, existing)
        return added

    def get_active(self) -> list:
        return _load(PIPELINE_FILE)

    def get_followup(self) -> list:
        return _load(FOLLOWUP_FILE)

    def get_clients(self) -> list:
        return _load(CLIENTS_FILE)

    def move_to_followup(self, lead_id: str) -> bool:
        """Move a lead from active pipeline to follow-up."""
        pipeline = _load(PIPELINE_FILE)
        followup = _load(FOLLOWUP_FILE)

        target = None
        remaining = []
        for lead in pipeline:
            if lead.get("id") == lead_id:
                target = lead
            else:
                remaining.append(lead)

        if not target:
            return False

        target["pipeline_status"] = "followup"
        target["followup_added"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        followup.append(target)
        _save(PIPELINE_FILE, remaining)
        _save(FOLLOWUP_FILE, followup)
        return True

    def move_to_client(self, lead_id: str) -> bool:
        """Move a lead to confirmed clients (from active or followup)."""
        clients = _load(CLIENTS_FILE)
        target = None

        for source_file in [PIPELINE_FILE, FOLLOWUP_FILE]:
            source = _load(source_file)
            remaining = []
            for lead in source:
                if lead.get("id") == lead_id:
                    target = lead
                else:
                    remaining.append(lead)
            if target:
                _save(source_file, remaining)
                break

        if not target:
            return False

        target["pipeline_status"] = "client"
        target["confirmed_on"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        clients.append(target)
        _save(CLIENTS_FILE, clients)
        return True

    def dismiss(self, lead_id: str) -> bool:
        """Permanently dismiss a lead — it will never appear again."""
        dismissed = _load_dismissed()
        target = None

        for source_file in [PIPELINE_FILE, FOLLOWUP_FILE]:
            source = _load(source_file)
            remaining = []
            for lead in source:
                if lead.get("id") == lead_id:
                    target = lead
                else:
                    remaining.append(lead)
            if target:
                _save(source_file, remaining)
                break

        if not target:
            return False

        company_key = target.get("company", "").lower().strip()
        if company_key:
            dismissed.add(company_key)
            _save_dismissed(dismissed)
        return True

    def get_stats(self) -> dict:
        return {
            "active":   len(_load(PIPELINE_FILE)),
            "followup": len(_load(FOLLOWUP_FILE)),
            "clients":  len(_load(CLIENTS_FILE)),
            "dismissed": len(_load_dismissed()),
        }
