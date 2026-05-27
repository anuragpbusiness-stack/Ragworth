# Ragworth: 24/7 Cloud Hosting & Custom Domain Playbook

This document is your step-by-step operational guide to bringing your CEO Command Center online **24/7** and connecting it to a prestigious **custom domain** (e.g., `dashboard.ragon.co` or `ragon.co`) using 100% free, enterprise-grade cloud tools.

---

## 🛠️ Step 1: Secure a Free 24/7 Cloud Database (Supabase)
*Time required: 3 minutes | Cost: $0*

Because free cloud servers have ephemeral storage (wiping local files like `leads.json` on restart), we must use a persistent cloud database. **Supabase** offers a completely free, 24/7 enterprise-grade PostgreSQL database.

1. Go to **[https://supabase.com](https://supabase.com)** and click **"Start your Project"** (Sign in with your Google account).
2. Click **"New Project"** and select/create an organization.
3. Configure the Project:
   - **Name:** `Ragworth-DB`
   - **Database Password:** *Choose a secure password (write it down).*
   - **Region:** Choose a region close to your target clients (e.g., *East US* or *London/Europe*).
   - **Plan:** Choose the **Free Plan** ($0/month).
4. Wait 1 minute for the database to provision.
5. In the left-hand sidebar, click the **Settings (Gear Icon) → Database**.
6. Scroll down to **Connection string**, select the **URI** tab, and copy the string. It will look like this:
   ```
   postgresql://postgres.[your-project-id]:[your-password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
7. **Replace `[your-password]`** with the secure password you chose in step 3.
8. Open your local [.env](file:///d:/Coding/Projects/Ragworth/.env) file and add a new line:
   ```env
   DATABASE_URL=postgresql://postgres.your-project-id:your-password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
9. *That's it!* On startup, the FastAPI server will automatically detect this URL, connect securely, and build the database schemas inside the cloud database automatically.

---

## 🚀 Step 2: Push Your Code to a Private GitHub Repo
*Time required: 2 minutes | Cost: $0*

To deploy to a cloud server, you need to sync your `/Ragworth` folder with your GitHub account.

1. Open PowerShell inside `d:\Coding\Projects\Ragworth`.
2. Initialize Git and commit your files:
   ```powershell
   git init
   git add .
   git commit -m "Initialize secure Ragworth OS"
   ```
3. Go to **[https://github.com](https://github.com)** and create a new **Private Repository** named `Ragworth-OS`.
4. Copy the remote URL commands provided by GitHub (under "push an existing repository") and paste them into your PowerShell:
   ```powershell
   git remote add origin https://github.com/your-username/Ragworth-OS.git
   git branch -M main
   git push -u origin main
   ```
   *(Note: Since `.env` and `/finance/leads/` are pre-configured in `.gitignore`, your private keys and raw CSVs will never be exposed on GitHub.)*

---

## 🌐 Step 3: Deploy 24/7 on Render (Free Web Service)
*Time required: 3 minutes | Cost: $0*

**Render** is an elite cloud platform that allows you to host web servers 24/7 for free.

1. Go to **[https://render.com](https://render.com)** and sign up free (using your GitHub account).
2. On your Render Dashboard, click **"New +" → "Web Service"**.
3. Select **"Build and deploy from a Git repository"** and click Next.
4. Search for your private `Ragworth-OS` repository and click **Connect**.
5. Configure the Web Service:
   - **Name:** `ragworth`
   - **Region:** *Oregon (US West), Frankfurt (Europe), or Singapore* (select close to your database region).
   - **Branch:** `main`
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Select **Free** ($0/mo).
6. Click **"Advanced"** and click **"Add Environment Variable"**:
   - Add Key: `DATABASE_URL` | Value: *Paste your Supabase PostgreSQL URI string here.*
   - Add Key: `RAGWORTH_EXEC_KEY` | Value: `RAGON2026`
   - Add Key: `FIRECRAWL_API_KEY` | Value: `fc-47989bf78871437fa6820af6907a1f73`
7. Click **"Create Web Service"**.
8. *Render will immediately pull your code from GitHub, install the requirements, start your FastAPI backend, and deploy it to a secure public URL (e.g. `https://ragworth.onrender.com`) running 24/7!*

---

## 👑 Step 4: Map Your Premium Custom Domain
*Time required: 2 minutes | Cost: $0 on Render (Domain bought separately)*

To make your agency look prestigious, you want to access the dashboard on a custom domain (e.g., `dashboard.ragon.co` or `secure.ragon.co`).

1. Open your Web Service on the Render Dashboard.
2. In the left-hand menu, click **"Settings"**.
3. Scroll down to **"Custom Domains"** and click **"Add Custom Domain"**.
4. Type in your desired domain (e.g., `dashboard.ragon.co`) and click **Save**.
5. Render will supply you with a target host record (e.g. `ragworth.onrender.com`).
6. Log into your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.) and open your domain's **DNS Management / DNS Zone Editor**:
   - Add a new **CNAME Record**:
     - **Host/Name:** `dashboard` (or `secure` depending on sub-domain)
     - **Value/Points To:** `ragworth.onrender.com`
     - **TTL:** `Auto` or `3600`
7. Once saved, click **Verify** on the Render dashboard.
8. *Render will instantly verify the CNAME, provision a free SSL certificate from Let's Encrypt, configure auto-renewals, and map your secure HTTPS custom domain (`https://dashboard.ragon.co`) to your 24/7 live CEO dashboard!*
