# Ragworth Lead Engine — Activation Guide
**Time required: 8 minutes.**

The software is built. You just need to plug in the keys.

---

## STEP 1 — Install Dependencies (2 min)

Open PowerShell in the project folder and run:

```powershell
pip install requests python-dotenv
```

---

## STEP 2 — Get Your Apollo.io Key (3 min) ⭐ PRIMARY

**Apollo gives you 50 verified decision-maker leads/day on the free plan.**

1. Go to **https://app.apollo.io/#/signup**
2. Sign up with your work email (use `anurag@ragworth.com` style — or any email you control).
3. Skip the onboarding (click "Skip" on team invites).
4. In the left sidebar: **Settings → Integrations → API**
5. Click **"Create New Key"** → name it `Ragworth-RLE`.
6. Copy the key (starts with something like `xK_abc123...`).

---

## STEP 3 — Get Your Hunter.io Key (2 min) ✅ VERIFICATION

**Hunter verifies that the email you got actually exists.**

1. Go to **https://hunter.io/users/sign_up**
2. Sign up free (no credit card).
3. Top right → **API** menu.
4. Copy the key shown on the dashboard.

---

## STEP 4 — Plug Keys into Ragworth (1 min)

1. In your project folder, **copy `.env.example` to `.env`**:

```powershell
copy .env.example .env
```

2. Open `.env` in Notepad (or Cursor) and paste your keys:

```
APOLLO_API_KEY=xK_yourActualKeyHere
HUNTER_API_KEY=yourHunterKeyHere
```

3. Save the file.

---

## STEP 5 — Run It

### Option A — Direct (fastest):
```powershell
python scripts/ragworth_lead_engine.py --count 100
```

### Option B — Through the REI Command Center (preferred):
```powershell
python scripts/ragworth_rei.py
```
→ Enter key `RAGON2026` → press `3` → configure targeting → leads flow in.

---

## WHAT YOU'LL GET

For each lead:
- ✓ First & last name
- ✓ Job title (CEO, CTO, Managing Partner, etc.)
- ✓ Company + domain
- ✓ **Verified email**
- ✓ Phone (when available)
- ✓ LinkedIn URL
- ✓ Location
- ✓ Confidence score (0–1)

**Outputs land in:**
- `finance/leads/ragworth_leads_YYYYMMDD_HHMM.csv` ← open in Excel
- `database/leads.json` ← live CLI dashboard
- Visible in REI dashboard option [1]

---

## SCALING TO 100 LEADS/HOUR

| Apollo Plan | Leads/Day | Leads/Hour | Cost |
|---|---|---|---|
| Free | 50 | ~10 | $0 |
| Basic | 2,000 | ~80 | $49/mo |
| Professional | 12,000 | **500+** | $99/mo |

The code is identical — only the API key tier changes. Upgrade after first client.

---

## SECURITY NOTES

- ✅ `.env` is in `.gitignore` — keys never reach GitHub.
- ✅ Apollo communications are HTTPS only.
- ✅ Rate-limiting built in (1-second delays between calls).
- ✅ Dedup logic prevents duplicate billing.
- ⚠️ Never share your `.env` file. If exposed, regenerate keys immediately.

---

**Once you've got the keys plugged in, tell me and I'll fire the first scout for you live.**
