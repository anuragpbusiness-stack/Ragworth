// State Management
let sessionToken = localStorage.getItem('ragworth_token') || "";
let dashboardData = null;
let db = null; // Firebase Firestore instance

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
    // Set Header Date
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    document.getElementById("top-date-display").innerText = new Date().toLocaleDateString('en-US', options).toUpperCase() + " | EXECUTIVE SESSION";
    
    // Initialize Firebase if active
    if (typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            firebase.initializeApp(firebaseConfig);
            db = firebase.firestore();
            console.log("[✔] Firebase Real-Time Firestore Node Initialized.");
        } catch (e) {
            console.error("[!] Failed to initialize Firebase: ", e);
        }
    }

    // Check Session Auth
    if (sessionToken) {
        document.getElementById("login-overlay").style.display = "none";
        startDashboardSync();
    } else {
        document.getElementById("login-overlay").style.display = "flex";
    }

    // Connect Invoice live preview
    updateInvoicePreview();
});

// Authentication Protocols
async function attemptAuth() {
    const key = document.getElementById("pass-key").value;
    const errorEl = document.getElementById("auth-error");
    
    // Local API auth
    try {
        const response = await fetch("/api/auth", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ key: key })
        });
        
        if (response.ok) {
            const data = await response.json();
            sessionToken = data.token;
            localStorage.setItem('ragworth_token', sessionToken);
            errorEl.style.display = "none";
            successfulLogin();
        } else {
            // Check hardcoded fallback key if offline
            if (key === "RAGON2026") {
                sessionToken = "executive_session_ragworth_2026";
                localStorage.setItem('ragworth_token', sessionToken);
                errorEl.style.display = "none";
                successfulLogin();
            } else {
                errorEl.style.display = "block";
            }
        }
    } catch (e) {
        // Offline / Serverless authentication check
        if (key === "RAGON2026") {
            sessionToken = "executive_session_ragworth_2026";
            localStorage.setItem('ragworth_token', sessionToken);
            errorEl.style.display = "none";
            successfulLogin();
        } else {
            errorEl.style.display = "block";
        }
    }
}

function successfulLogin() {
    const overlay = document.getElementById("login-overlay");
    overlay.style.opacity = 0;
    setTimeout(() => {
        overlay.style.display = "none";
    }, 500);
    startDashboardSync();
}

// Start Syncing (Real-Time Firebase vs. REST API)
function startDashboardSync() {
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        subscribeFirebaseData();
    } else {
        fetchDashboardData();
        // Poll every 10 seconds locally to keep simulated updates
        setInterval(fetchDashboardData, 10000);
    }
}

// Real-Time Firebase Listeners
function subscribeFirebaseData() {
    console.log("[*] Establishing 24/7 Firebase Real-Time Synchronization...");
    
    // Initialize blank base structures
    dashboardData = {
        summary: { total_revenue: 0.0, active_leads: 0, last_update: "Real-Time Cloud", systems_health: "100%" },
        leads: [],
        ledger: [],
        grid: {
            industries: [
                "Commercial Law", "Maritime Logistics", "Boutique Real Estate", "Supply Chain Management",
                "Architecture Firms", "Private Equity", "Wealth Management", "Freight Forwarders"
            ],
            cities: [
                "London, UK", "New York, NY", "Dubai, UAE", "Singapore", "Sydney, Australia",
                "San Francisco, CA", "Bangalore, India", "Zurich, Switzerland"
            ]
        }
    };

    // 1. Leads Snapshot
    db.collection("leads").orderBy("added_on", "desc").onSnapshot(snapshot => {
        let list = [];
        snapshot.forEach(doc => {
            list.push(doc.data());
        });
        dashboardData.leads = list;
        dashboardData.summary.active_leads = list.length;
        populateDashboard();
    }, err => {
        console.error("Firestore leads subscription error: ", err);
    });

    // 2. Ledger Snapshot
    db.collection("ledger").orderBy("Date", "desc").onSnapshot(snapshot => {
        let list = [];
        let totalRev = 0.0;
        snapshot.forEach(doc => {
            const data = doc.data();
            list.push(data);
            totalRev += parseFloat(data.Amount_USD || 0.0);
        });
        dashboardData.ledger = list;
        dashboardData.summary.total_revenue = totalRev;
        populateDashboard();
    }, err => {
        console.error("Firestore ledger subscription error: ", err);
    });
}

// Fetch All Database Stats via FastAPI Local Server
async function fetchDashboardData() {
    try {
        const response = await fetch("/api/dashboard", {
            headers: { "Authorization": `Bearer ${sessionToken}` }
        });
        
        if (response.status === 401) {
            localStorage.removeItem('ragworth_token');
            document.getElementById("login-overlay").style.opacity = 1;
            document.getElementById("login-overlay").style.display = "flex";
            return;
        }
        
        const resData = await response.json();
        if (resData.success) {
            dashboardData = resData;
            populateDashboard();
        }
    } catch (e) {
        console.warn("FastAPI offline. Dashboard loaded with cached records.");
    }
}

// Populate UI components with data
function populateDashboard() {
    if (!dashboardData) return;
    
    const summary = dashboardData.summary;
    const leads = dashboardData.leads;
    const ledger = dashboardData.ledger;
    const grid = dashboardData.grid;
    
    // 1. KPI Updates
    const totalRevenueUSD = parseFloat(summary.total_revenue || 0.0);
    const exchangeRate = 80.0; // INR/USD standard
    const totalRevenueINR = totalRevenueUSD * exchangeRate;
    
    document.getElementById("kpi-revenue").innerText = `$${totalRevenueUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    document.getElementById("kpi-revenue-inr").innerText = `₹${totalRevenueINR.toLocaleString('en-IN', { minimumFractionDigits: 2 })} | Capitalization Active`;
    document.getElementById("kpi-leads").innerText = summary.active_leads;
    document.getElementById("ledger-total-value").innerText = `$${totalRevenueUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    // 2. Dashboard Leads Table
    const tableBody = document.getElementById("dashboard-leads-table");
    tableBody.innerHTML = "";
    
    if (leads.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No active target signals found.</td></tr>`;
    } else {
        leads.forEach(lead => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 500;">${lead.company || lead.name}</td>
                <td><i class="fas fa-map-marker-alt" style="margin-right: 0.4rem; font-size: 0.75rem; color: var(--text-muted);"></i> ${lead.hq}</td>
                <td>${lead.pain_point || lead.niche}</td>
                <td><i class="fas fa-star" style="color: var(--accent); font-size: 0.7rem; margin-right: 0.3rem;"></i> ${lead.confidence || '0.90'}</td>
                <td style="font-weight: 600;">${lead.potential_value || '$10,000+'}</td>
                <td><span class="badge badge-priority">${lead.status || 'Active Target'}</span></td>
            `;
            tableBody.appendChild(tr);
        });
    }
    
    // 3. Ledger Entries Table
    const ledgerBody = document.getElementById("ledger-table-body");
    ledgerBody.innerHTML = "";
    
    if (ledger.length === 0) {
        ledgerBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No payments recorded.</td></tr>`;
    } else {
        ledger.forEach(entry => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${entry.Date}</td>
                <td style="font-family: 'Courier New', monospace; font-size: 0.75rem;">${entry.Invoice_ID}</td>
                <td style="font-weight: 500;">${entry.Client_Name}</td>
                <td>${entry.Service_Type}</td>
                <td style="font-weight: 600; color: var(--text-gold);">$${parseFloat(entry.Amount_USD).toFixed(2)}</td>
                <td><span class="badge badge-paid">${entry.Status}</span></td>
                <td>${entry.Payment_Method}</td>
                <td style="color: var(--text-muted); font-size: 0.75rem;">${entry.Notes || 'None'}</td>
            `;
            ledgerBody.appendChild(tr);
        });
    }
    
    // 4. Populate Scout Selectors
    const nicheSelect = document.getElementById("scout-niche");
    const locSelect = document.getElementById("scout-location");
    
    if (nicheSelect.children.length <= 1 && grid.industries) {
        grid.industries.forEach(niche => {
            const opt = document.createElement("option");
            opt.value = niche;
            opt.innerText = niche;
            nicheSelect.appendChild(opt);
        });
    }
    
    if (locSelect.children.length <= 1 && grid.cities) {
        grid.cities.forEach(city => {
            const opt = document.createElement("option");
            opt.value = city;
            opt.innerText = city;
            locSelect.appendChild(opt);
        });
    }
}

// Navigation switch
function switchTab(tabId, element) {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    element.classList.add("active");
    
    document.querySelectorAll(".tab-content").forEach(tab => tab.classList.remove("active"));
    document.getElementById(tabId).classList.add("active");
    
    let title = "CEO Command Center";
    if (tabId === "tab-scout") title = "Prospect Scout Engine";
    else if (tabId === "tab-ledger") title = "Financial Ledger";
    else if (tabId === "tab-invoice") title = "Invoice Hub";
    
    document.getElementById("tab-title-display").innerText = title;
}

// Log manual revenue
async function logNewRevenue() {
    const client = document.getElementById("log-client").value.trim();
    const amount = parseFloat(document.getElementById("log-amount").value);
    const service = document.getElementById("log-service").value.trim();
    const successEl = document.getElementById("revenue-log-success");
    
    if (!client || isNaN(amount) || !service) {
        alert("Please specify Client Name, Amount, and Service.");
        return;
    }

    const date = new Date().toISOString().slice(0, 10);
    const invoice_id = `RAG-${Date.now().toString().slice(-8)}`;

    // Write to Firebase Firestore directly if active
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            await db.collection("ledger").add({
                Date: date,
                Invoice_ID: invoice_id,
                Client_Name: client,
                Service_Type: service,
                Amount_USD: amount.toFixed(2),
                Status: "Paid",
                Payment_Method: "Wire Transfer",
                Tax_ID: "N/A",
                Notes: "Logged via Serverless Firebase Dashboard"
            });
            
            successEl.style.display = "block";
            document.getElementById("log-client").value = "";
            document.getElementById("log-amount").value = "";
            document.getElementById("log-service").value = "";
            setTimeout(() => { successEl.style.display = "none"; }, 3000);
            return; // Firebase listener will auto-update
        } catch (e) {
            alert("Firebase write failed: " + e.message);
            return;
        }
    }
    
    // Fallback Local FastAPI API Write
    try {
        const response = await fetch("/api/revenue", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                client: client,
                amount: amount,
                service: service,
                notes: "Logged via CEO Dashboard Website"
            })
        });
        
        if (response.ok) {
            successEl.style.display = "block";
            document.getElementById("log-client").value = "";
            document.getElementById("log-amount").value = "";
            document.getElementById("log-service").value = "";
            
            setTimeout(() => { successEl.style.display = "none"; }, 3000);
            fetchDashboardData();
        } else {
            const err = await response.json();
            alert(`Failed: ${err.detail}`);
        }
    } catch (e) {
        alert("Error logging payment. Connection offline.");
    }
}

// Simulated real-time console logging
function logTerminal(message, type = "info") {
    const terminal = document.getElementById("scout-terminal");
    const div = document.createElement("div");
    div.className = `terminal-line ${type}`;
    div.innerText = `[${new Date().toLocaleTimeString()}] ${message}`;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
}

// Dispatch Scrapers
async function dispatchScout(mode) {
    const niche = document.getElementById("scout-niche").value;
    const location = document.getElementById("scout-location").value;
    const count = parseInt(document.getElementById("scout-count").value) || 5;
    
    document.getElementById("terminal-section").style.display = "block";
    const terminal = document.getElementById("scout-terminal");
    terminal.innerHTML = "";
    
    logTerminal("INITIALIZING CORE PROSPECT SEARCH ENGINE...", "success");
    logTerminal(`MODE: ${mode.toUpperCase()} TARGET PROTOCOL ACTIVE.`, "warning");
    logTerminal(`TARGET PARAMS: NICHE='${niche || 'Auto-Selected'}', REGION='${location || 'Auto-Selected'}', VOLUME=${count}`, "info");
    
    setTimeout(() => logTerminal("DISPATCHING SCRAWLER FLIGHT NODES...", "info"), 800);
    setTimeout(() => logTerminal("BYPASSING GEOLOCATION CAPTCHA SHIELDS...", "warning"), 1600);
    setTimeout(() => logTerminal("PARSING SEARCH DIRECTORY DORK SIGNATURES...", "info"), 2400);
    
    try {
        const endpoint = mode === "omniscale" ? "/api/scout/omniscale" : "/api/scout/omniscout";
        
        // Request scraper to local API (scrapers run locally)
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                niche: niche || null,
                location: location || null,
                count: count
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const leads = data.scouted_leads;
            
            setTimeout(async () => {
                logTerminal(`CRAWLER PULSE COMPLETE. DISCOVERED ${leads.length} LEADS.`, "success");
                
                // If Firebase active, push found leads directly into Firebase cloud from browser
                if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
                    logTerminal("SYNCHRONIZING LEADS INTO FIREBASE REAL-TIME CLOUD...", "warning");
                    for (let lead of leads) {
                        try {
                            const nameVal = lead.name || `${lead.first_name || 'Decision'} ${lead.last_name || 'Maker'}`.trim();
                            await db.collection("leads").doc(lead.company.replace(/\//g, "-").toLowerCase()).set({
                                name: nameVal,
                                company: lead.company,
                                title: lead.title || "Owner/Partner",
                                hq: lead.location || lead.hq || "Unknown",
                                niche: lead.niche || "Target Profile",
                                email: lead.email || `contact@${lead.domain || 'company.com'}`,
                                website: lead.website || `https://${lead.domain || ''}`,
                                linkedin: lead.linkedin || "",
                                potential_value: lead.potential_value || "$15,000+",
                                status: lead.status || "Scouted",
                                source: lead.source || "Scout",
                                confidence: lead.confidence || lead.intelligence_score || 0.5,
                                pain_point: lead.pain_point || lead.pain_points || "Manual business vulnerabilities",
                                added_on: new Date().toISOString().slice(0, 10)
                            }, { merge: true });
                        } catch (e) {
                            console.error("Firebase lead add error: ", e);
                        }
                    }
                    logTerminal("FIREBASE CLOUD WRITE COMPLETE.", "success");
                } else {
                    logTerminal("DEDUPLICATING LOCAL PIPELINES...", "info");
                    logTerminal("MERGING RECORDS INTO DATABASE (leads.json)...", "success");
                }
                
                displayScoutedLeads(leads);
                if (!db || !USE_FIREBASE) fetchDashboardData();
            }, 3200);
        } else {
            const err = await response.json();
            setTimeout(() => logTerminal(`[!] CRAWLER ERROR: ${err.detail}`, "warning"), 3200);
        }
    } catch (e) {
        setTimeout(() => logTerminal("[!] CRAWLER ENGINE CONNECTION FAILURE.", "warning"), 3200);
    }
}

// Display scouted results in sub-table
function displayScoutedLeads(leads) {
    const panel = document.getElementById("newly-scouted-panel");
    panel.style.display = "block";
    
    const tbody = document.getElementById("scouted-results-table");
    tbody.innerHTML = "";
    
    if (leads.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Scout finished but zero opportunities met quality debt criteria.</td></tr>`;
        return;
    }
    
    leads.forEach(lead => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="font-weight: 500;">${lead.company}</td>
            <td><a href="${lead.website}" target="_blank" style="color: var(--text-muted); text-decoration: none;"><i class="fas fa-external-link-alt" style="margin-right: 0.3rem;"></i> ${lead.domain || 'website'}</a></td>
            <td style="font-size: 0.75rem;">${lead.pain_points || lead.pain_point || lead.niche}</td>
            <td style="font-weight: bold; color: var(--accent);">${lead.intelligence_score || lead.confidence}</td>
            <td><i class="fas fa-map-marker-alt" style="color: var(--text-muted); margin-right: 0.3rem;"></i> ${lead.location}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Invoice preview card dynamic synchronization
function updateInvoicePreview() {
    const client = document.getElementById("inv-client").value.trim() || "Sterling & Associates Law";
    const address = document.getElementById("inv-address").value.trim() || "London, United Kingdom";
    const service = document.getElementById("inv-service").value.trim() || "Agentic Compliance Workflow Setup & CRM Integration Services";
    const amountVal = parseFloat(document.getElementById("inv-amount").value) || 15000.00;
    
    const formattedAmount = `$${amountVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    document.getElementById("preview-client-name").innerText = client;
    document.getElementById("preview-client-address").innerText = address;
    document.getElementById("preview-service-desc").innerText = service;
    document.getElementById("preview-service-cost").innerText = formattedAmount;
    document.getElementById("preview-subtotal").innerText = formattedAmount;
    document.getElementById("preview-grandtotal").innerText = formattedAmount;
    
    document.getElementById("preview-invoice-id").innerText = `RAG-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;
    document.getElementById("preview-invoice-date").innerText = new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });
}

// Export CSV
function downloadLedgerCSV() {
    if (!dashboardData || !dashboardData.ledger) {
        alert("No ledger database records loaded yet.");
        return;
    }
    
    const ledger = dashboardData.ledger;
    const headers = ["Date", "Invoice_ID", "Client_Name", "Service_Type", "Amount_USD", "Status", "Payment_Method", "Notes"];
    
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += headers.join(",") + "\n";
    
    ledger.forEach(entry => {
        const row = headers.map(header => {
            const cell = entry[header] ? entry[header].toString().replace(/"/g, '""') : "";
            return `"${cell}"`;
        });
        csvContent += row.join(",") + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ragworth_ledger_export_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
