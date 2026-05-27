# Ragworth OS (Ragon Co. Tech Wing)

Welcome to the **Ragworth Executive Operating System (ROS) v1.0**. This is a highly premium, secure, and fully functional 24/7 web application designed to act as your CEO Command Center. 

ROS brings together your multi-agent infrastructure dispatches, global lead generation nodes, financial ledger accounting, and high-prestige invoice generation into a unified, minimal, "Quiet Luxury" web interface.

---

## 📂 System Architecture

The application is structured logically with strict separation of concerns, keeping your databases local and secure:

```
/Ragworth
├── /database
│   ├── leads.json          # Main active leads list
│   ├── global_grid.json    # Target industries & cities matrix
│   └── settings.json       # General configurations
├── /finance
│   ├── ledger.csv          # Confidential legal ledger (tracks ₹500/MRR)
│   └── /leads              # Storage directory for historical raw CSV crawls
├── /scripts
│   ├── scout.py            # Basic lead generation helper
│   ├── ragworth_os.py      # Core data access and MRR calculator class
│   ├── ragworth_omniscale.py # DuckDuckGo Tech-Debt Scraper (Zero-Key)
│   └── ragworth_omniscout.py # LinkedIn Public Persona Triangulator
├── /static
│   ├── index.html          # Cinematic public digital flagship landing page
│   ├── dashboard.html      # Secure CEO Command Center web app
│   ├── styles.css          # Premium Custom CSS Design System
│   └── dashboard.js        # Dynamic API hooks, logs simulator, invoice builder
├── main.py                 # Core Python FastAPI Backend Web Server
└── run_ragworth_server.bat # Windows double-click automation launcher
```

---

## 🚀 Activation & Execution Playbook

### Step 1: Double-Click the Launcher
Double-click `run_ragworth_server.bat` in the project root.
- The automation script will verify your Python environment.
- It will automatically install requirements: `fastapi`, `uvicorn`, `requests`, and `beautifulsoup4`.
- It will boot your backend server on `http://127.0.0.1:8000`.

### Step 2: Open your CEO Command Center
1. Open your browser and go to: [http://127.0.0.1:8000/dashboard.html](http://127.0.0.1:8000/dashboard.html).
2. Enter your Executive Access Key: **`RAGON2026`**.
3. *Welcome to your Empire.*

### Step 3: Establish 24/7 Secure Cloud Access (Cloudflare Tunnel)
If you want to access your dashboard from your phone or anywhere in the world completely free, securely, on a 24/7 HTTPS domain:
1. Open a new PowerShell terminal inside `/Ragworth`.
2. Run this command:
   ```powershell
   npx -y @cloudflare/next-on-pages tunnel --url http://127.0.0.1:8000
   ```
3. Cloudflare will instantly tunnel your local FastAPI server and generate a free SSL-encrypted web address (e.g. `https://your-custom-id.trycloudflare.com`).
4. Bookmark this URL on your phone. It is 100% secure, remote-ready, and requires your key (`RAGON2026`) to display any financial or lead data.

---

## 💼 Core Operating Features

### 1. Executive Dashboard (Tab 1)
- **Revenue Tracking (MRR):** Tracks your MRR. Converts your seed capital of **₹500.00** into **$6.25** and handles all multi-currency conversions using live exchange rates.
- **Priority Lead Pipeline:** Real-time database synchronizer pulling directly from `database/leads.json`.

### 2. Scout Engine Console (Tab 2)
- **Target selectors:** Dropdown menus populated dynamically from your `global_grid.json` target matrix.
- **Dispatch buttons:** Directly triggers `OmniScale` (crawling websites for CRM/AI tech debt) or `OmniScout` (publicly triangulating decision-makers).
- **Log Screen:** Real-time scrolling terminal logs displaying the exact progress of search crawls.

### 3. Ledger & Cash Flow (Tab 3)
- **Add Cash Entries:** Enter clients, amounts, and services to log payments. Updates `ledger.csv` in real-time, instantly refreshing MRR KPIs.
- **CSV Export:** Instantly compile your ledger entries and download them as an Excel-ready CSV sheet.

### 4. Invoice Hub (Tab 4)
- **Interactive Form:** Fill in billing names, service terms, SWIFT routing codes, and totals.
- **Prestige Print:** Layout compiles live as you type and renders as an ultra-premium Times-New-Roman print-ready PDF letterhead. Press `Ctrl + P` to print or save.
