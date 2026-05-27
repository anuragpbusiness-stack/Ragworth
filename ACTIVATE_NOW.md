# RAGWORTH — 6-Minute Activation Sequence
**Email to use for all 3: `anuragp.business@gmail.com`**

---

## ⏱ 0:00 — Open 3 Tabs (Ctrl+Click each)

| # | Service | Signup URL | What it gives you |
|---|---------|------------|-------------------|
| 1 | **Apollo.io** | https://app.apollo.io/#/signup | 50 verified decision-makers/day |
| 2 | **Hunter.io** | https://hunter.io/users/sign_up | 25 email verifications/mo |
| 3 | **Apify** | https://console.apify.com/sign-up | $5/mo credits → Google Maps + LinkedIn scraping |

---

## ⏱ 0:30 — Sign Up With Google (fastest)

All 3 support **"Sign up with Google"** — click that button on each tab and use `anuragp.business@gmail.com`. Skips email verification.

For Apollo, when asked:
- **Company:** Ragworth
- **Role:** Founder / CEO
- **Team size:** 1–10
- **Use case:** Sales prospecting
- Skip team invites.

---

## ⏱ 3:00 — Grab The 3 API Keys

### 🔑 Apollo Key
1. Click your profile (top-right) → **Settings**
2. Left sidebar → **Integrations**
3. Scroll to **API** → **Create New Key**
4. Name it: `Ragworth-RLE`
5. **Copy the key** (starts with letters/numbers ~40 chars)

### 🔑 Hunter Key
1. Top-right menu → **API**
2. Key is shown on the dashboard. **Copy it.**

### 🔑 Apify Token
1. Top-right avatar → **Settings**
2. Left sidebar → **Integrations**
3. Scroll to **Personal API tokens**
4. Click **Create token** → name it `Ragworth-Intelligence`
5. **Copy the token** (starts with `apify_api_...`)

---

## ⏱ 5:00 — Paste Into `.env` (one file, one paste)

Open PowerShell in the project folder:

```powershell
copy .env.example .env
notepad .env
```

Paste your keys into these 3 lines:

```env
APOLLO_API_KEY=paste_apollo_key_here
HUNTER_API_KEY=paste_hunter_key_here
APIFY_API_TOKEN=paste_apify_token_here
```

Save. Close Notepad.

---

## ⏱ 6:00 — Fire The First Hunt

```powershell
pip install requests python-dotenv
python scripts/ragworth_rei.py
```

→ Enter `RAGON2026`
→ Press `3` for Apollo scout, OR `4` for Google Maps Intelligence
→ Press Enter through the defaults
→ Watch the leads flow in

---

## When Done, Tell Me:
> "Keys are in."

I'll fire the first 50-lead live scout in this chat and we'll have your first batch of verified US/UK decision-maker contacts within 2 minutes.
