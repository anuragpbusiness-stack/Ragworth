import os
import requests
from datetime import datetime, timedelta

class InvoiceNinjaConnector:
    def __init__(self):
        # Load API keys securely from environmental parameters
        self.api_key = os.getenv("INVOICE_NINJA_API_KEY", "").strip()
        self.base_url = os.getenv("INVOICE_NINJA_URL", "https://invoicing.co").strip()
        
        # Clean trailing slashes from base URL
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        self.headers = {
            "X-Api-Token": self.api_key,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        
    @property
    def is_configured(self):
        """Checks if the Invoice Ninja integration credentials are present."""
        return bool(self.api_key)

    def get_or_create_client(self, name, address=""):
        """Looks up a client by name on Invoice Ninja to prevent duplicate records, creating one if not found."""
        if not self.is_configured:
            raise ValueError("Invoice Ninja credentials are not configured in your .env file.")

        # Step 1: Search for existing client
        search_url = f"{self.base_url}/api/v1/clients"
        try:
            # Invoice Ninja find parameter matches names
            response = requests.get(
                f"{search_url}?find={requests.utils.quote(name)}",
                headers=self.headers,
                timeout=10
            )
            if response.ok:
                data = response.json().get("data", [])
                for client in data:
                    if client.get("name", "").lower() == name.lower():
                        print(f"[✔] Found existing Invoice Ninja client: {name} (ID: {client['id']})")
                        return client["id"]
        except Exception as e:
            print(f"[!] Warning: Client lookup failed: {e}. Attempting client registration...")

        # Step 2: Create new client if not found
        payload = {
            "name": name,
            "address1": address,
            "notes": "Merged dynamically from Ragworth OS Command Center"
        }
        
        response = requests.post(search_url, json=payload, headers=self.headers, timeout=10)
        if not response.ok:
            raise Exception(f"Invoice Ninja Client creation failed: {response.text}")
            
        client_data = response.json().get("data", {})
        print(f"[✔] Created new Invoice Ninja client: {name} (ID: {client_data['id']})")
        return client_data["id"]

    def create_invoice(self, client_name, client_address, service_desc, amount):
        """Creates a client profile and generates a formal invoice on Invoice Ninja, returning the direct viewing URL."""
        if not self.is_configured:
            raise ValueError("Invoice Ninja credentials are not configured in your .env file.")

        # Resolve Client ID
        client_id = self.get_or_create_client(client_name, client_address)

        # Dates setup (Standard Net-30 Terms)
        date_str = datetime.now().strftime("%Y-%m-%d")
        due_date_str = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Invoice payload
        payload = {
            "client_id": client_id,
            "date": date_str,
            "due_date": due_date_str,
            "line_items": [
                {
                    "notes": service_desc,
                    "cost": float(amount),
                    "qty": 1
                }
            ],
            "auto_bill": True
        }

        # Create Invoice
        invoice_url = f"{self.base_url}/api/v1/invoices"
        response = requests.post(invoice_url, json=payload, headers=self.headers, timeout=10)
        if not response.ok:
            raise Exception(f"Invoice Ninja Invoice creation failed: {response.text}")

        inv_data = response.json().get("data", {})
        
        # Extract direct viewer link (Client Invitation Portal URL)
        invitation_link = ""
        invitations = inv_data.get("invitations", [])
        if invitations:
            invitation_link = invitations[0].get("link", "")
            
        # Fallback view URL construction if invitation array is not populated
        if not invitation_link:
            hashed_id = inv_data.get("hashed_id") or inv_data.get("id", "")
            invitation_link = f"{self.base_url}/client/invoice/{hashed_id}"

        print(f"[✔] Successfully generated Invoice Ninja Invoice (ID: {inv_data.get('id')})")
        return invitation_link
