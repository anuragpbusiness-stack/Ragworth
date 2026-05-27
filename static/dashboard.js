// State Management
let sessionToken = localStorage.getItem('ragworth_token') || "";
let dashboardData = null;
let db = null; // Firebase Firestore instance
let currentCurrency = localStorage.getItem('ragworth_currency') || "USD";
let globalRates = { "USD": 1.0, "INR": 83.5, "EUR": 0.92, "GBP": 0.79, "AED": 3.67, "JPY": 155.0, "CAD": 1.37, "AUD": 1.50 };

// ==============================================
// UNIVERSAL CURRENCY INPUT RESOLVER ENGINE
// ==============================================
// Maps any human input (words, symbols, short codes) → ISO 4217 code → USD

const CURRENCY_ALIAS_MAP = {
    // US Dollar
    "$": "USD", "usd": "USD", "dollar": "USD", "dollars": "USD", "us dollar": "USD", "us dollars": "USD", "buck": "USD", "bucks": "USD",
    // Indian Rupee
    "₹": "INR", "inr": "INR", "rupee": "INR", "rupees": "INR", "indian rupee": "INR", "rs": "INR", "re": "INR",
    // Euro
    "€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR",
    // British Pound
    "£": "GBP", "gbp": "GBP", "pound": "GBP", "pounds": "GBP", "sterling": "GBP", "quid": "GBP",
    // UAE Dirham
    "د.إ": "AED", "aed": "AED", "dirham": "AED", "dirhams": "AED", "dhs": "AED", "dh": "AED",
    // Japanese Yen
    "¥": "JPY", "jpy": "JPY", "yen": "JPY",
    // Chinese Yuan
    "cny": "CNY", "yuan": "CNY", "rmb": "CNY", "renminbi": "CNY",
    // Canadian Dollar
    "cad": "CAD", "canadian dollar": "CAD", "canadian dollars": "CAD", "c$": "CAD", "ca$": "CAD",
    // Australian Dollar
    "aud": "AUD", "australian dollar": "AUD", "australian dollars": "AUD", "a$": "AUD",
    // Swiss Franc
    "chf": "CHF", "franc": "CHF", "francs": "CHF", "swiss franc": "CHF",
    // Singapore Dollar
    "sgd": "SGD", "singapore dollar": "SGD", "s$": "SGD",
    // Hong Kong Dollar
    "hkd": "HKD", "hong kong dollar": "HKD", "hk$": "HKD",
    // South Korean Won
    "krw": "KRW", "won": "KRW", "₩": "KRW",
    // Saudi Riyal
    "sar": "SAR", "riyal": "SAR", "riyals": "SAR", "saudi riyal": "SAR",
    // Brazilian Real
    "brl": "BRL", "real": "BRL", "reais": "BRL", "r$": "BRL",
    // Mexican Peso
    "mxn": "MXN", "mexican peso": "MXN", "peso": "MXN", "pesos": "MXN",
    // Russian Ruble
    "rub": "RUB", "ruble": "RUB", "rubles": "RUB", "₽": "RUB",
    // Turkish Lira
    "try": "TRY", "lira": "TRY", "liras": "TRY", "₺": "TRY",
    // South African Rand
    "zar": "ZAR", "rand": "ZAR",
    // Nigerian Naira
    "ngn": "NGN", "naira": "NGN", "₦": "NGN",
    // Pakistani Rupee
    "pkr": "PKR", "pakistani rupee": "PKR",
    // Bangladeshi Taka
    "bdt": "BDT", "taka": "BDT", "৳": "BDT",
    // Indonesian Rupiah
    "idr": "IDR", "rupiah": "IDR", "rp": "IDR",
    // Thai Baht
    "thb": "THB", "baht": "THB", "฿": "THB",
    // Malaysian Ringgit
    "myr": "MYR", "ringgit": "MYR", "rm": "MYR",
    // Philippine Peso
    "php": "PHP", "philippine peso": "PHP", "₱": "PHP",
    // Vietnamese Dong
    "vnd": "VND", "dong": "VND", "₫": "VND",
    // Egyptian Pound
    "egp": "EGP", "egyptian pound": "EGP",
    // Ukrainian Hryvnia
    "uah": "UAH", "hryvnia": "UAH", "₴": "UAH",
    // Czech Koruna
    "czk": "CZK", "koruna": "CZK",
    // Polish Zloty
    "pln": "PLN", "zloty": "PLN", "zł": "PLN",
    // Swedish Krona
    "sek": "SEK", "krona": "SEK", "kronor": "SEK",
    // Norwegian Krone
    "nok": "NOK", "krone": "NOK", "kr": "NOK",
    // Danish Krone
    "dkk": "DKK",
    // Israeli Shekel
    "ils": "ILS", "shekel": "ILS", "shekels": "ILS", "₪": "ILS",
    // Argentine Peso
    "ars": "ARS", "argentine peso": "ARS",
    // Colombian Peso
    "cop": "COP", "colombian peso": "COP",
    // Chilean Peso
    "clp": "CLP", "chilean peso": "CLP",
    // New Zealand Dollar
    "nzd": "NZD", "new zealand dollar": "NZD", "nz$": "NZD",
    // Qatari Riyal
    "qar": "QAR", "qatari riyal": "QAR",
    // Kuwaiti Dinar
    "kwd": "KWD", "dinar": "KWD", "dinars": "KWD",
};

/**
 * Parses a free-text currency input into { amount (number), currency (ISO code), usd (number), label (string) }
 * Accepts formats: "500 inr", "₹500", "500 rupees", "€200", "2000 dollars", "$1500", "15000yen", "100 GBP"
 * Returns null if unparseable.
 */
function parseCurrencyInput(rawInput) {
    if (!rawInput || !rawInput.trim()) return null;
    const str = rawInput.trim();

    // --- Step 1: Extract numeric amount and currency text ---
    // Patterns: symbol+number, number+symbol, number+space+text, text+number
    // e.g.  "₹500", "$1,200.50", "500 inr", "500 rupees", "€ 200", "15000yen"
    let amount = null;
    let currencyText = "";

    // Try: symbol/text prefix + number  ("₹500", "€200", "$1,500")
    const prefixMatch = str.match(/^([^\d\s,.-]+)\s*([\d,]+(?:\.\d+)?)$/);
    if (prefixMatch) {
        currencyText = prefixMatch[1].trim();
        amount = parseFloat(prefixMatch[2].replace(/,/g, ""));
    }

    // Try: number + suffix text  ("500 inr", "500 rupees", "15000yen", "200 euros")
    if (amount === null) {
        const suffixMatch = str.match(/^([\d,]+(?:\.\d+)?)\s*([^\d\s,.]*)$/);
        if (suffixMatch) {
            amount = parseFloat(suffixMatch[1].replace(/,/g, ""));
            currencyText = suffixMatch[2].trim();
        }
    }

    // Fallback: pure number = assume USD
    if (amount === null) {
        const pureNum = parseFloat(str.replace(/,/g, ""));
        if (!isNaN(pureNum)) {
            amount = pureNum;
            currencyText = "";
        }
    }

    if (amount === null || isNaN(amount) || amount <= 0) return null;

    // --- Step 2: Resolve currency text → ISO code ---
    let isoCode = "USD"; // default
    if (currencyText) {
        const key = currencyText.toLowerCase();
        // Direct alias lookup
        if (CURRENCY_ALIAS_MAP[key]) {
            isoCode = CURRENCY_ALIAS_MAP[key];
        } else if (currencyText.length === 3 && /^[a-zA-Z]+$/.test(currencyText)) {
            // Treat 3-letter codes as ISO directly (e.g. "CHF", "SGD")
            isoCode = currencyText.toUpperCase();
        } else {
            // Partial word match — find first alias containing the key
            const keys = Object.keys(CURRENCY_ALIAS_MAP);
            const partial = keys.find(k => k.includes(key) || key.includes(k));
            if (partial) isoCode = CURRENCY_ALIAS_MAP[partial];
        }
    }

    // --- Step 3: Convert to USD using live rates ---
    // globalRates is { CODE: rate_per_usd }, so USD = amount / rate
    const rate = globalRates[isoCode] || null;
    const usd = rate ? amount / rate : null;

    return { amount, currency: isoCode, usd, rate, label: `${amount.toLocaleString()} ${isoCode}` };
}

// Dynamic Multi-Currency Conversion Helpers
function convertCurrency(amountUsd, targetCurrency) {
    const usdAmount = parseFloat(amountUsd || 0.0);
    const rate = parseFloat(globalRates[targetCurrency] || 1.0);
    return usdAmount * rate;
}

function getCurrencySymbol(currencyCode) {
    const symbols = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
        "AED": "د.إ",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$"
    };
    return symbols[currencyCode] || currencyCode;
}

function changeDisplayCurrency() {
    const selector = document.getElementById("currency-selector");
    if (selector) {
        currentCurrency = selector.value;
        localStorage.setItem('ragworth_currency', currentCurrency);
        console.log(`[OK] Changed display currency to: ${currentCurrency}`);
        populateDashboard();
    }
}

function updateLogAmountHelper() {
    const amountInput = document.getElementById("log-amount");
    const helperEl = document.getElementById("log-amount-inr-helper");
    if (!amountInput || !helperEl) return;

    const raw = amountInput.value.trim();
    if (!raw) { helperEl.style.display = "none"; return; }

    const parsed = parseCurrencyInput(raw);
    if (!parsed) {
        helperEl.style.display = "block";
        helperEl.style.color = "#e05c5c";
        helperEl.innerText = "⚠ Could not parse currency. Try: '500 inr', '€200', '1500 dollars'";
        return;
    }

    helperEl.style.display = "block";
    if (parsed.usd !== null) {
        const displayConverted = convertCurrency(parsed.usd, currentCurrency);
        const symbol = getCurrencySymbol(currentCurrency);
        const usdNote = parsed.currency !== "USD" ? ` = $${parsed.usd.toFixed(2)} USD` : "";
        helperEl.style.color = "var(--accent)";
        helperEl.innerText = `✓ ${parsed.label}${usdNote}  →  ${symbol}${displayConverted.toLocaleString('en-US', { minimumFractionDigits: 2 })} ${currentCurrency}`;
    } else {
        helperEl.style.color = "#e0a05c";
        helperEl.innerText = `✓ Detected ${parsed.currency} — rate not in cache, will store as-is in USD`;
    }
}

function formatLeadPotential(valStr) {
    if (!valStr) return "";
    // Extract numeric digits
    const matches = valStr.match(/\d+[,.\d]*/);
    if (!matches) return valStr;
    const numStr = matches[0].replace(/,/g, '');
    const usdAmount = parseFloat(numStr);
    if (isNaN(usdAmount)) return valStr;
    const converted = convertCurrency(usdAmount, currentCurrency);
    const symbol = getCurrencySymbol(currentCurrency);
    return `${symbol}${converted.toLocaleString('en-US', { maximumFractionDigits: 0 })}+`;
}

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
    // Set Header Date
    const options = { day: 'numeric', month: 'short', year: 'numeric' };
    document.getElementById("top-date-display").innerText = new Date().toLocaleDateString('en-US', options).toUpperCase() + " | EXECUTIVE SESSION";
    
    // Set currency selector state
    const selector = document.getElementById("currency-selector");
    if (selector) {
        selector.value = currentCurrency;
    }
    
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
        setInterval(fetchDashboardData, 10000);
    }
    // Always load pipeline stats on startup
    loadPipelineStats();
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
            if (resData.exchange_rates) {
                globalRates = resData.exchange_rates;
            }
            populateDashboard();
        }
    } catch (e) {
        console.warn("FastAPI offline. Dashboard loaded with cached records.");
    }
}

// Populate UI components with data
function populateDashboard() {
    if (!dashboardData) return;
    
    // Update live ticker rate
    const ticker = document.getElementById("live-rate-ticker");
    if (ticker) {
        const rate = parseFloat(globalRates[currentCurrency] || 1.0);
        ticker.innerHTML = `<i class="fas fa-chart-line" style="margin-right: 0.25rem;"></i> USD/${currentCurrency}: ${rate.toFixed(4)}`;
    }
    
    const summary = dashboardData.summary;
    const leads = dashboardData.leads;
    const ledger = dashboardData.ledger;
    const grid = dashboardData.grid;
    
    // 1. KPI Updates
    const totalRevenueUSD = parseFloat(summary.total_revenue || 0.0);
    const convertedRevenue = convertCurrency(totalRevenueUSD, currentCurrency);
    const displaySymbol = getCurrencySymbol(currentCurrency);
    
    document.getElementById("kpi-revenue").innerText = `${displaySymbol}${convertedRevenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    // Subtext shows alternate secondary currency
    if (currentCurrency === "USD") {
        const inrEquivalent = convertCurrency(totalRevenueUSD, "INR");
        document.getElementById("kpi-revenue-inr").innerText = `₹${inrEquivalent.toLocaleString('en-IN', { minimumFractionDigits: 2 })} | Capitalization Active`;
    } else {
        document.getElementById("kpi-revenue-inr").innerText = `$${totalRevenueUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })} USD | Base standardized rate`;
    }
    
    document.getElementById("kpi-leads").innerText = summary.active_leads;
    document.getElementById("ledger-total-value").innerText = `${displaySymbol}${convertedRevenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    // Update Ledger dynamic header
    const ledgerHeader = document.getElementById("ledger-amount-header");
    if (ledgerHeader) {
        ledgerHeader.innerText = `Amount (${currentCurrency})`;
    }
    
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
                <td style="font-weight: 600;">${formatLeadPotential(lead.potential_value || '$10,000+')}</td>
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
                <td style="font-weight: 600; color: var(--text-gold);">
                    <div>${getCurrencySymbol(currentCurrency)}${convertCurrency(entry.Amount_USD, currentCurrency).toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    ${currentCurrency !== "USD" ? `<div style="font-size: 0.65rem; color: var(--text-muted); font-weight: normal; margin-top: 0.1rem;">$${parseFloat(entry.Amount_USD).toFixed(2)} USD</div>` : ''}
                </td>
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
    const rawAmountInput = document.getElementById("log-amount").value.trim();
    const service = document.getElementById("log-service").value.trim();
    const successEl = document.getElementById("revenue-log-success");

    if (!client || !rawAmountInput || !service) {
        alert("Please specify Client Name, Amount, and Service.");
        return;
    }

    // Parse universal currency input → USD
    const parsed = parseCurrencyInput(rawAmountInput);
    if (!parsed) {
        alert("Could not parse the amount. Try formats like: '500 inr', '€200', '$1500', '2000 rupees', '15000 yen'");
        return;
    }
    // Use converted USD if available, otherwise use raw amount (assume USD)
    const amount = parsed.usd !== null ? parseFloat(parsed.usd.toFixed(2)) : parsed.amount;
    const originalCurrencyNote = parsed.currency !== "USD"
        ? `Original: ${parsed.label} @ rate ${parsed.rate}` : "";

    if (isNaN(amount) || amount <= 0) {
        alert("Invalid amount. Please enter a positive number with a currency (e.g. '500 inr', '€200').");
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

// ==============================================
// OMNI INTELLIGENCE ENGINE v3.0 — FRONTEND
// ==============================================

// Terminal log helper — appends a line to the scout terminal
function logTerminal(message, type = "info") {
    const terminal = document.getElementById("scout-terminal");
    if (!terminal) return;
    const div = document.createElement("div");
    div.className = `terminal-line ${type}`;
    div.innerText = `[${new Date().toLocaleTimeString()}] ${message}`;
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;
}

let currentPipelineView = "active";


function updatePipelineStats(stats) {
    if (!stats) return;
    const s = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    s("stat-active",   stats.active   || 0);
    s("stat-followup", stats.followup || 0);
    s("stat-clients",  stats.clients  || 0);
}

async function dispatchOmniIntelligence() {
    const niche    = document.getElementById("scout-niche").value;
    const location = document.getElementById("scout-location").value;
    const count    = parseInt(document.getElementById("scout-count").value) || 5;
    const callable = document.getElementById("scout-callable").checked;

    const btn = document.getElementById("omni-dispatch-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-circle-notch fa-spin"></i>&nbsp; SCANNING...`;

    document.getElementById("terminal-section").style.display = "block";
    const terminal = document.getElementById("scout-terminal");
    terminal.innerHTML = "";

    logTerminal("╔══ OMNI INTELLIGENCE ENGINE v3.0 ══╗", "success");
    logTerminal(`PARAMS — niche: '${niche || 'Auto'}' · loc: '${location || 'Auto'}' · vol: ${count} · callable_only: ${callable}`, "info");
    logTerminal("Phase 1: OmniScale global business discovery initializing...", "warning");

    try {
        const response = await fetch("/api/omni/dispatch", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                niche: niche || null,
                location: location || null,
                count: count,
                callable_only: callable
            })
        });

        const data = await response.json();

        // Stream backend logs into terminal
        if (data.logs && Array.isArray(data.logs)) {
            for (const line of data.logs) {
                const type = line.includes("✔") || line.includes("COMPLETE") ? "success"
                           : line.includes("⚠") || line.includes("✖") ? "warning"
                           : "info";
                logTerminal(line.replace(/^\[.*?\]\s*/, ""), type);
            }
        }

        if (response.ok && data.success) {
            const leads = data.scouted_leads || [];
            const added = data.new_leads_added || 0;
            logTerminal(`╚══ DISPATCH COMPLETE — ${leads.length} leads enriched · ${added} new in pipeline ══╝`, "success");
            updatePipelineStats(data.pipeline_stats);
            loadPipelineView("active");
            // Show follow-up reminder banner
            if (added > 0) showFollowUpReminder(added);
        } else {
            logTerminal(`✖ ERROR: ${data.detail || "Dispatch failed."}`, "warning");
        }
    } catch (e) {
        logTerminal("✖ CONNECTION ERROR — Is the server running?", "warning");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-satellite-dish"></i>&nbsp; DISPATCH OMNI INTELLIGENCE`;
    }
}

// Follow-up reminder banner
function showFollowUpReminder(count) {
    let existing = document.getElementById("followup-reminder");
    if (existing) existing.remove();
    const banner = document.createElement("div");
    banner.id = "followup-reminder";
    banner.className = "followup-reminder-banner";
    banner.innerHTML = `
        <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
            <span style="font-size:1.1rem;">🔔</span>
            <span><strong>${count} new lead${count > 1 ? 's' : ''} added!</strong> Don't forget to follow up — consistency is what converts.</span>
            <button class="reminder-followup-btn" onclick="loadPipelineView('followup');document.getElementById('tab-scout').scrollIntoView({behavior:'smooth'});this.closest('#followup-reminder').remove();">
                <i class="fas fa-bookmark"></i> View Follow Up List
            </button>
            <button class="reminder-close-btn" onclick="this.closest('#followup-reminder').remove();" title="Dismiss">✕</button>
        </div>
    `;
    // Insert below the terminal section
    const terminal = document.getElementById("terminal-section");
    if (terminal && terminal.parentNode) {
        terminal.parentNode.insertBefore(banner, terminal.nextSibling);
    } else {
        document.querySelector("#tab-scout").prepend(banner);
    }
    // Auto-dismiss after 30s
    setTimeout(() => { if (banner.parentNode) banner.remove(); }, 30000);
}

// Load a pipeline stage view (active / followup / clients)
async function loadPipelineView(stage) {
    currentPipelineView = stage;

    // Update sub-tab active states
    ["active", "followup", "clients"].forEach(s => {
        const btn = document.getElementById(`ptab-${s}`);
        if (btn) btn.classList.toggle("active", s === stage);
    });

    try {
        const response = await fetch(`/api/pipeline/${stage}`, {
            headers: { "Authorization": `Bearer ${sessionToken}` }
        });
        const data = await response.json();
        if (data.success) {
            updatePipelineStats(data.stats);
            renderLeadCards(data.leads || [], stage);
        }
    } catch (e) {
        console.error("Pipeline load error:", e);
    }
}

// Render lead cards grid
function renderLeadCards(leads, stage) {
    const empty = document.getElementById("lead-cards-empty");
    const grid  = document.getElementById("lead-cards-grid");

    if (!leads || leads.length === 0) {
        empty.style.display = "block";
        const stageLabels = { active: "ACTIVE PIPELINE", followup: "FOLLOW UP LIST", clients: "CONFIRMED CLIENTS" };
        empty.innerHTML = `${stageLabels[stage] || stage.toUpperCase()} EMPTY`;
        grid.style.display = "none";
        return;
    }

    empty.style.display = "none";
    grid.style.display  = "grid";
    grid.innerHTML = "";

    leads.forEach(lead => {
        const card = document.createElement("div");
        card.className = "lead-card";
        card.setAttribute("data-id", lead.id);

        const score = parseFloat(lead.intelligence_score || 0);
        const scorePct = Math.round(score * 100);
        const scoreColor = scorePct >= 70 ? "#c9a84c" : scorePct >= 45 ? "#e0a05c" : "#6F6961";

        const callable = lead.is_callable_now;
        const callBadge = callable
            ? `<span class="tz-badge tz-open">🟢 OPEN ${lead.local_time_now || ""}</span>`
            : `<span class="tz-badge tz-closed">🔴 AFTER HOURS ${lead.local_time_now || ""}</span>`;

        const services = Array.isArray(lead.services_needed) ? lead.services_needed : (lead.services_needed || "").split(",");
        const serviceChips = services.map(s => s.trim()).filter(Boolean)
            .map(s => `<span class="service-chip">${s}</span>`).join("");

        const adSignal = lead.recent_ad_signal
            ? `<div class="lead-ad-signal">📡 ${lead.recent_ad_signal}</div>` : "";

        // Pitch angle — the exact opening line to use on the call
        const pitchAngle = lead.pitch_angle
            ? `<div class="lead-pitch-angle"><span class="pitch-label">📞 PITCH ANGLE</span><span class="pitch-text">${lead.pitch_angle}</span></div>` : "";

        const sources = Array.isArray(lead.sources) ? lead.sources : [];
        const sourceLinks = sources.slice(0, 5).map(src =>
            `<a href="${src.url || '#'}" target="_blank" class="source-link" title="${src.label}">
                <i class="fas fa-external-link-alt"></i> ${src.label.substring(0, 32)}
            </a>`
        ).join("");

        const signalCount = lead.signal_types_hit || 0;
        const signalBar = signalCount > 0
            ? `<div class="signal-bar"><span class="signal-bar-label">SIGNAL STRENGTH</span>${[1,2,3,4,5].map(i => `<span class="signal-dot ${i <= signalCount ? 'active' : ''}"></span>`).join('')}</div>`
            : "";

        const contactSection = lead.contact_name && lead.contact_name !== "Decision Maker"
            ? `<div class="lead-contact">
                <div class="contact-name">${lead.contact_name}</div>
                <div class="contact-title">${lead.contact_title || ""}</div>
                <div class="contact-email"><i class="fas fa-envelope"></i> ${lead.contact_email || ""}</div>
                ${lead.contact_linkedin ? `<a href="${lead.contact_linkedin}" target="_blank" class="contact-linkedin"><i class="fab fa-linkedin"></i> LinkedIn Profile</a>` : ""}
               </div>`
            : `<div class="lead-contact muted"><i class="fas fa-user-circle"></i> Contact triangulation in progress</div>`;

        // Action buttons depending on current stage
        let actionBtns = "";
        if (stage === "active") {
            actionBtns = `
                <button class="action-btn btn-followup" onclick="leadAction('${lead.id}', 'followup')"><i class="fas fa-bookmark"></i> FOLLOW UP</button>
                <button class="action-btn btn-dismiss"  onclick="leadAction('${lead.id}', 'dismiss')">NOT NEEDED</button>
                <button class="action-btn btn-confirm"  onclick="leadAction('${lead.id}', 'confirm')"><i class="fas fa-check"></i> CONFIRMED</button>
            `;
        } else if (stage === "followup") {
            actionBtns = `
                <button class="action-btn btn-confirm"  onclick="leadAction('${lead.id}', 'confirm')"><i class="fas fa-user-check"></i> CLIENT</button>
                <button class="action-btn btn-dismiss"  onclick="leadAction('${lead.id}', 'dismiss')">NOT NEEDED</button>
            `;
        } else if (stage === "clients") {
            actionBtns = `<span style="color:var(--accent);font-size:0.65rem;font-family:monospace;">✔ ACTIVE CLIENT</span>`;
        }

        card.innerHTML = `
            <div class="lead-card-header">
                <div>
                    <div class="lead-company">${lead.company}</div>
                    <div class="lead-meta">
                        <i class="fas fa-globe" style="color:var(--text-muted);margin-right:0.3rem;"></i>
                        <a href="${lead.website || '#'}" target="_blank" class="lead-website">${lead.domain || lead.website || "—"}</a>
                        <span style="margin:0 0.4rem;color:var(--border)">·</span>
                        <i class="fas fa-map-marker-alt" style="color:var(--text-muted);margin-right:0.3rem;"></i>
                        <span style="color:var(--text-muted)">${lead.location || "—"}</span>
                    </div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    ${callBadge}
                    <div class="lead-score" style="color:${scoreColor};">${scorePct}<span style="font-size:0.55rem;">% FIT</span></div>
                </div>
            </div>
            ${contactSection}
            ${signalBar}
            <div class="lead-services">${serviceChips || '<span class="service-chip">General AI Services</span>'}</div>
            ${pitchAngle}
            ${adSignal}
            <div class="lead-sources">${sourceLinks || '<span style="color:var(--text-muted);font-size:0.65rem;">No sources recorded</span>'}</div>
            <div class="lead-actions">${actionBtns}</div>
        `;

        grid.appendChild(card);
    });
}

// Perform a lead action (followup / dismiss / confirm)
async function leadAction(leadId, action) {
    const card = document.querySelector(`.lead-card[data-id="${leadId}"]`);
    if (card) {
        card.style.opacity = "0.4";
        card.style.pointerEvents = "none";
    }

    try {
        const response = await fetch("/api/leads/action", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionToken}`
            },
            body: JSON.stringify({ lead_id: leadId, action: action })
        });
        const data = await response.json();
        if (data.success) {
            updatePipelineStats(data.stats);
            // Remove card with animation
            if (card) {
                card.style.transform = "scale(0.95)";
                card.style.transition = "all 0.3s ease";
                setTimeout(() => {
                    card.remove();
                    // Check if grid is now empty
                    const grid = document.getElementById("lead-cards-grid");
                    if (grid && grid.children.length === 0) {
                        grid.style.display = "none";
                        document.getElementById("lead-cards-empty").style.display = "block";
                    }
                }, 300);
            }
        } else {
            if (card) { card.style.opacity = "1"; card.style.pointerEvents = "auto"; }
        }
    } catch (e) {
        console.error("Lead action error:", e);
        if (card) { card.style.opacity = "1"; card.style.pointerEvents = "auto"; }
    }
}

// Load pipeline stats on startup
async function loadPipelineStats() {
    try {
        const response = await fetch("/api/pipeline/stats/summary", {
            headers: { "Authorization": `Bearer ${sessionToken}` }
        });
        const data = await response.json();
        if (data.success) updatePipelineStats(data.stats);
    } catch (e) { /* silent */ }
}

// Keep backward compatibility alias
async function dispatchScout(mode) {
    dispatchOmniIntelligence();
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
            procLine.remove();

            const lines = data.response.split("\n");
            lines.forEach((line, index) => {
                setTimeout(() => {
                    const lineEl = document.createElement("div");
                    lineEl.className = "terminal-line";

                    if (line.includes("ONLINE") || line.includes("VERIFIED") || line.includes("COMPLETE")) {
                        lineEl.className = "terminal-line success";
                        lineEl.style.color = "#6F6961";
                    } else if (line.startsWith("•") || line.startsWith("CEO Instructed:") || line.startsWith("Hermes")) {
                        lineEl.className = "terminal-line info";
                    }

                    lineEl.innerText = line;
                    terminal.appendChild(lineEl);
                    terminal.scrollTop = terminal.scrollHeight;
                }, index * 30);
            });
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
