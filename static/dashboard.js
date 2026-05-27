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
        employees: [],
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
            data._docId = doc.id; // Map doc ID for edits/deletes
            list.push(data);
            totalRev += parseFloat(data.Amount_USD || 0.0);
        });
        dashboardData.ledger = list;
        dashboardData.summary.total_revenue = totalRev;
        populateDashboard();
    }, err => {
        console.error("Firestore ledger subscription error: ", err);
    });

    // 3. Employees Snapshot (Real-time Firebase)
    db.collection("employees").onSnapshot(snapshot => {
        let list = [];
        snapshot.forEach(doc => {
            const data = doc.data();
            data._docId = doc.id;
            list.push(data);
        });
        
        // Failsafe: if Hermes is not in Firestore yet, add it
        if (!list.some(e => e.emp_id === "EMP-HERMES")) {
            const hermesObj = {
                emp_id: "EMP-HERMES",
                name: "Hermes",
                role: "Personal Assistant (AI Core)",
                email: "hermes@ragon.co",
                clearance: "FULL CONTROL (LEVEL 5)",
                status: "Online",
                joined_date: new Date().toISOString().slice(0, 10)
            };
            db.collection("employees").doc("EMP-HERMES").set(hermesObj);
            list.unshift(hermesObj);
        }
        
        dashboardData.employees = list;
        populateDashboard();
    }, err => {
        console.error("Firestore employees subscription error: ", err);
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
        ledgerBody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No payments recorded.</td></tr>`;
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
                <td style="white-space: nowrap; text-align: right;">
                    <button class="action-btn edit-btn" onclick="openEditModal('${entry.Invoice_ID}')" title="Edit Entry"><i class="fas fa-pencil-alt"></i></button>
                    <button class="action-btn delete-btn" onclick="deleteEntry('${entry.Invoice_ID}')" title="Delete Entry"><i class="fas fa-trash-alt"></i></button>
                </td>
            `;
            ledgerBody.appendChild(tr);
        });
    }
    
    // 5. Populate Corporate Personnel Registry
    const employees = dashboardData.employees || [];
    const empBody = document.getElementById("employees-table-body");
    if (empBody) {
        empBody.innerHTML = "";
        if (employees.length === 0) {
            empBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No employees registered in corporate directories.</td></tr>`;
        } else {
            employees.forEach(emp => {
                const tr = document.createElement("tr");
                
                const nameStyle = emp.emp_id === "EMP-HERMES" ? 'font-weight: 600; color: var(--text-gold);' : 'font-weight: 500;';
                const nameDisplay = emp.emp_id === "EMP-HERMES" ? `<i class="fas fa-shield-halved" style="color: var(--accent); margin-right: 0.4rem;"></i> ${emp.name}` : emp.name;
                
                const actionBtns = emp.emp_id === "EMP-HERMES" 
                    ? `<span style="font-size: 0.65rem; text-transform: uppercase; color: var(--accent); font-weight: bold; letter-spacing: 0.05em; padding-right: 0.5rem;"><i class="fas fa-lock"></i> SOVEREIGN SECURITY</span>`
                    : `
                        <button class="action-btn edit-btn" onclick="openEditEmployeeModal('${emp.emp_id}')" title="Edit Employee"><i class="fas fa-pencil-alt"></i></button>
                        <button class="action-btn delete-btn" onclick="deleteEmployee('${emp.emp_id}')" title="Delete Employee"><i class="fas fa-trash-alt"></i></button>
                    `;
                    
                tr.innerHTML = `
                    <td style="font-family: 'Courier New', monospace; font-size: 0.75rem;">${emp.emp_id}</td>
                    <td style="${nameStyle}">${nameDisplay}</td>
                    <td>${emp.role}</td>
                    <td><span class="badge ${emp.emp_id === 'EMP-HERMES' ? 'badge-priority' : 'badge-new'}" style="font-size: 0.55rem; padding: 0.2rem 0.4rem;">${emp.clearance}</span></td>
                    <td><span class="badge badge-paid" style="border-color: ${emp.status === 'Online' ? '#6F6961' : '#8D7859'}; color: ${emp.status === 'Online' ? '#6F6961' : '#8D7859'};">${emp.status}</span></td>
                    <td style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">${emp.email}</td>
                    <td>${emp.joined_date}</td>
                    <td style="white-space: nowrap; text-align: right;">${actionBtns}</td>
                `;
                empBody.appendChild(tr);
            });
        }
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
    else if (tabId === "tab-employees") title = "Employees & AI Assistant Hub";
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

// ==============================================
// LEDGER MANAGEMENT (EDIT & DELETE PROTOCOLS)
// ==============================================

// Open Edit Modal with Pre-populated Data
function openEditModal(invoiceId) {
    if (!dashboardData || !dashboardData.ledger) return;
    
    const entry = dashboardData.ledger.find(e => e.Invoice_ID === invoiceId);
    if (!entry) {
        alert("Ledger entry not found.");
        return;
    }
    
    document.getElementById("edit-invoice-id").value = entry.Invoice_ID;
    
    // Format Date for native input type="date" (YYYY-MM-DD)
    let dateVal = entry.Date;
    if (dateVal) {
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateVal)) {
            document.getElementById("edit-date").value = dateVal;
        } else {
            try {
                const parsed = new Date(dateVal);
                if (!isNaN(parsed.getTime())) {
                    document.getElementById("edit-date").value = parsed.toISOString().slice(0, 10);
                }
            } catch (e) {
                document.getElementById("edit-date").value = new Date().toISOString().slice(0, 10);
            }
        }
    } else {
        document.getElementById("edit-date").value = new Date().toISOString().slice(0, 10);
    }
    
    document.getElementById("edit-client").value = entry.Client_Name || "";
    document.getElementById("edit-service").value = entry.Service_Type || entry.Service_Provided || "";
    document.getElementById("edit-amount").value = entry.Amount_USD || "";
    
    const statusVal = entry.Status || "Paid";
    document.getElementById("edit-status").value = statusVal;
    document.getElementById("edit-notes").value = entry.Notes || "";
    
    // Trigger modal show (adds active class for transition)
    document.getElementById("edit-ledger-modal").classList.add("active");
}

// Close Edit Modal
function closeEditModal() {
    document.getElementById("edit-ledger-modal").classList.remove("active");
}

// Save Changes to either Firebase Firestore or FastAPI backend
async function saveLedgerEdit() {
    const invoiceId = document.getElementById("edit-invoice-id").value;
    const date = document.getElementById("edit-date").value;
    const client = document.getElementById("edit-client").value.trim();
    const service = document.getElementById("edit-service").value.trim();
    const amount = parseFloat(document.getElementById("edit-amount").value);
    const statusVal = document.getElementById("edit-status").value;
    const notes = document.getElementById("edit-notes").value.trim();
    
    if (!client || isNaN(amount) || !service || !date) {
        alert("Please specify Date, Client Name, Service, and Amount.");
        return;
    }
    
    // 1. Firebase direct sync if active
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            const docId = await findFirestoreDocIdByInvoice(invoiceId);
            if (docId) {
                await db.collection("ledger").doc(docId).update({
                    Date: date,
                    Client_Name: client,
                    Service_Type: service,
                    Amount_USD: amount.toFixed(2),
                    Status: statusVal,
                    Notes: notes
                });
                closeEditModal();
                return;
            } else {
                alert("Firestore document for this invoice not found.");
                return;
            }
        } catch (e) {
            alert("Firebase update failed: " + e.message);
            return;
        }
    }
    
    // 2. Local/Cloud SQL FastAPI API Endpoint
    try {
        const response = await fetch(`/api/ledger/${invoiceId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                client: client,
                amount: amount,
                service: service,
                notes: notes,
                date: date,
                status: statusVal
            })
        });
        
        if (response.ok) {
            closeEditModal();
            fetchDashboardData();
        } else {
            const err = await response.json();
            alert(`Failed to save changes: ${err.detail}`);
        }
    } catch (e) {
        alert("Error saving edit. Server is offline.");
    }
}

// Delete Entry
async function deleteEntry(invoiceId) {
    if (!confirm(`Are you sure you want to permanently delete Ledger Entry ${invoiceId}?`)) {
        return;
    }
    
    // 1. Firebase direct delete if active
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            const docId = await findFirestoreDocIdByInvoice(invoiceId);
            if (docId) {
                await db.collection("ledger").doc(docId).delete();
                return;
            } else {
                alert("Firestore document for this invoice not found.");
                return;
            }
        } catch (e) {
            alert("Firebase delete failed: " + e.message);
            return;
        }
    }
    
    // 2. Local/Cloud SQL FastAPI API Endpoint
    try {
        const response = await fetch(`/api/ledger/${invoiceId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${sessionToken}`
            }
        });
        
        if (response.ok) {
            fetchDashboardData();
        } else {
            const err = await response.json();
            alert(`Failed to delete: ${err.detail}`);
        }
    } catch (e) {
        alert("Error deleting entry. Server is offline.");
    }
}

// Helper to query firestore doc ID by Invoice ID if no direct binding is found
async function findFirestoreDocIdByInvoice(invoiceId) {
    if (!db) return null;
    
    // Check state first to save API roundtrips
    if (dashboardData && dashboardData.ledger) {
        const entry = dashboardData.ledger.find(e => e.Invoice_ID === invoiceId);
        if (entry && entry._docId) return entry._docId;
    }
    
    try {
        const q = await db.collection("ledger").where("Invoice_ID", "==", invoiceId).get();
        if (!q.empty) {
            return q.docs[0].id;
        }
    } catch (e) {
        console.error("Error querying Firestore: ", e);
    }
    return null;
}

// ==============================================
// EMPLOYEES & PERSONNEL DIRECTORY PROTOCOLS
// ==============================================

// Open Add Employee Modal
function openAddEmployeeModal() {
    document.getElementById("emp-modal-title").innerText = "Record New Employee";
    document.getElementById("edit-emp-id").value = "";
    document.getElementById("emp-name").value = "";
    document.getElementById("emp-role").value = "";
    document.getElementById("emp-email").value = "";
    document.getElementById("emp-clearance").value = "LEVEL 1 (VIEWER)";
    document.getElementById("emp-status").value = "Online";
    
    // Allow email editing for new employees
    document.getElementById("emp-email").disabled = false;
    document.getElementById("emp-email").style.opacity = "1";
    
    document.getElementById("employee-modal").classList.add("active");
}

// Open Edit Employee Modal
function openEditEmployeeModal(empId) {
    if (!dashboardData || !dashboardData.employees) return;
    
    const emp = dashboardData.employees.find(e => e.emp_id === empId);
    if (!emp) {
        alert("Employee not found.");
        return;
    }
    
    document.getElementById("emp-modal-title").innerText = `Update Employee: ${emp.name}`;
    document.getElementById("edit-emp-id").value = emp.emp_id;
    document.getElementById("emp-name").value = emp.name;
    document.getElementById("emp-role").value = emp.role;
    document.getElementById("emp-email").value = emp.email;
    document.getElementById("emp-clearance").value = emp.clearance;
    document.getElementById("emp-status").value = emp.status;
    
    // Disable email editing for existing employees
    document.getElementById("emp-email").disabled = true;
    document.getElementById("emp-email").style.opacity = "0.5";
    
    document.getElementById("employee-modal").classList.add("active");
}

// Close Employee Modal
function closeEmployeeModal() {
    document.getElementById("employee-modal").classList.remove("active");
}

// Save Employee (Add or Edit)
async function saveEmployee() {
    const empId = document.getElementById("edit-emp-id").value;
    const name = document.getElementById("emp-name").value.trim();
    const role = document.getElementById("emp-role").value.trim();
    const email = document.getElementById("emp-email").value.trim();
    const clearance = document.getElementById("emp-clearance").value;
    const statusVal = document.getElementById("emp-status").value;
    
    if (!name || !role || !email) {
        alert("Please fill in Name, Role, and Email.");
        return;
    }
    
    const isEdit = empId !== "";
    
    // 1. Firebase Firestore Direct Sync if active
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            if (isEdit) {
                const docRef = db.collection("employees").doc(empId);
                await docRef.update({
                    name: name,
                    role: role,
                    clearance: clearance,
                    status: statusVal
                });
            } else {
                const newId = `EMP-${Math.floor(100000 + Math.random() * 900000)}`;
                const newEmp = {
                    emp_id: newId,
                    name: name,
                    role: role,
                    email: email,
                    clearance: clearance,
                    status: statusVal,
                    joined_date: new Date().toISOString().slice(0, 10)
                };
                await db.collection("employees").doc(newId).set(newEmp);
            }
            closeEmployeeModal();
            return;
        } catch (e) {
            alert("Firebase save failed: " + e.message);
            return;
        }
    }
    
    // 2. FastAPI Backend API Write
    try {
        const method = isEdit ? "PUT" : "POST";
        const url = isEdit ? `/api/employees/${empId}` : "/api/employees";
        
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                name: name,
                role: role,
                email: email,
                clearance: clearance,
                status: statusVal
            })
        });
        
        if (response.ok) {
            closeEmployeeModal();
            fetchDashboardData();
        } else {
            const err = await response.json();
            alert(`Failed: ${err.detail}`);
        }
    } catch (e) {
        alert("Error saving registry. Server offline.");
    }
}

// Delete Employee
async function deleteEmployee(empId) {
    if (empId === "EMP-HERMES") {
        alert("Security Violation: Cannot delete sovereign AI Assistant!");
        return;
    }
    
    if (!confirm(`Are you sure you want to permanently remove employee ${empId}?`)) {
        return;
    }
    
    // 1. Firebase Direct Delete
    if (db && typeof USE_FIREBASE !== 'undefined' && USE_FIREBASE) {
        try {
            await db.collection("employees").doc(empId).delete();
            return;
        } catch (e) {
            alert("Firebase delete failed: " + e.message);
            return;
        }
    }
    
    // 2. FastAPI Local/SQL Endpoint
    try {
        const response = await fetch(`/api/employees/${empId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${sessionToken}`
            }
        });
        
        if (response.ok) {
            fetchDashboardData();
        } else {
            const err = await response.json();
            alert(`Failed: ${err.detail}`);
        }
    } catch (e) {
        alert("Error deleting employee. Server offline.");
    }
}

// ==============================================
// HERMES INTERACTIVE EXECUTIVE CLI TERMINAL
// ==============================================

async function sendHermesCommand() {
    const inputEl = document.getElementById("hermes-cmd-input");
    const cmd = inputEl.value.trim();
    if (!cmd) return;
    
    inputEl.value = "";
    
    const terminal = document.getElementById("hermes-terminal");
    
    // Print input line
    const userLine = document.createElement("div");
    userLine.className = "terminal-line success";
    userLine.innerText = `CEO> ${cmd}`;
    terminal.appendChild(userLine);
    terminal.scrollTop = terminal.scrollHeight;
    
    // Print immediate "Processing..." response
    const procLine = document.createElement("div");
    procLine.className = "terminal-line info";
    procLine.innerText = `[${new Date().toLocaleTimeString()}] Establishing secure path... routing command...`;
    terminal.appendChild(procLine);
    terminal.scrollTop = terminal.scrollHeight;
    
    try {
        const response = await fetch("/api/hermes/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({ command: cmd })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Premium typewriter/delay simulator
            setTimeout(() => {
                procLine.remove(); // Remove routing message
                
                const lines = data.response.split("\n");
                lines.forEach((line, index) => {
                    setTimeout(() => {
                        const lineEl = document.createElement("div");
                        lineEl.className = "terminal-line";
                        
                        // Parse status and highlights
                        if (line.includes("ONLINE") || line.includes("VERIFIED") || line.includes("COMPLETE")) {
                            lineEl.className = "terminal-line success";
                            lineEl.style.color = "#6F6961";
                        } else if (line.startsWith("•") || line.startsWith("CEO Instructed:")) {
                            lineEl.className = "terminal-line info";
                        }
                        
                        lineEl.innerText = line;
                        terminal.appendChild(lineEl);
                        terminal.scrollTop = terminal.scrollHeight;
                    }, index * 150); // Muted micro-animation delays
                });
            }, 600);
        } else {
            procLine.innerText = `[!] SECURE COM LINK ERROR: Directives rejected by master core.`;
        }
    } catch (e) {
        procLine.innerText = `[!] OFFLINE. Local AI Core stand-alone node running. type "/status" locally.`;
    }
}

// ==============================================
// SOVEREIGN PDF INVOICING ENGINE PROTOCOLS
// ==============================================

async function generateLocalPDFInvoice() {
    const client = document.getElementById("inv-client").value.trim() || "Sterling & Associates Law";
    const address = document.getElementById("inv-address").value.trim() || "London, United Kingdom";
    const service = document.getElementById("inv-service").value.trim() || "Agentic Compliance Workflow Setup & CRM Integration Services";
    const amountVal = parseFloat(document.getElementById("inv-amount").value) || 15000.00;

    const btn = document.getElementById("pdf-gen-btn");
    const statusEl = document.getElementById("ninja-sync-status");
    
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Compiling PDF...`;
    
    statusEl.style.display = "block";
    statusEl.className = "terminal-line info";
    statusEl.style.color = "#8D7859"; // Bronze style
    statusEl.innerHTML = `[${new Date().toLocaleTimeString()}] Accessing local PDF Compiler... seeding parameters...`;
    
    try {
        const response = await fetch("/api/invoice/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                client: client,
                address: address,
                service: service,
                amount: amountVal
            })
        });
        
        const resData = await response.json();
        
        if (response.ok && resData.success) {
            statusEl.className = "terminal-line success";
            statusEl.style.color = "#6F6961"; // Soft green
            statusEl.innerHTML = `
                <i class="fas fa-check-circle" style="margin-right: 0.5rem; color: #6F6961;"></i> 
                <strong>SUCCESS:</strong> Pristine PDF Invoice ${resData.invoice_id} generated locally! <br/>
                <span style="font-size: 0.65rem; color: var(--text-muted);">Revenue entry has been automatically recorded in your Financial Ledger.</span>
            `;
            // Instantly stream and preview compiled PDF in a new native browser tab
            window.open(resData.pdf_url, '_blank');
            // Refresh dashboard data to show the new ledger entry
            fetchDashboardData();
        } else {
            statusEl.className = "terminal-line warning";
            statusEl.style.color = "#8D7859";
            statusEl.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem; color: var(--accent);"></i>
                <strong>COMPILER FAILURE:</strong> ${resData.detail || "Verification failed."}
            `;
        }
    } catch (e) {
        statusEl.className = "terminal-line warning";
        statusEl.style.color = "#8D7859";
        statusEl.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem; color: var(--accent);"></i>
            <strong>CONNECTION OFFLINE:</strong> Could not connect to local back-office API server.
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-file-pdf"></i> Compile & Generate PDF Invoice`;
    }
}
