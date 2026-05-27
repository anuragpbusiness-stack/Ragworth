# Ragworth: 24/7 Serverless Firebase & Free Domain Playbook

This document is your dead-simple operational guide to bringing your CEO Command Center online **24/7** and connecting it to a completely **free web serverless host** using **Firebase Hosting** and **Firebase Firestore** (real-time cloud database).

---

## 🛠️ Step 1: Create a Free Firebase Project & Cloud Database
*Time required: 3 minutes | Cost: $0*

Firebase offers a completely free, 24/7 real-time NoSQL database (Firestore) and premium static hosting.

1. Go to the **[Firebase Console](https://console.firebase.google.com)** (Sign in with your Google account).
2. Click **"Add Project"**:
   - **Project Name:** `Ragworth-2026` (or similar)
   - Click "Continue". Toggle off Google Analytics (not needed for admin OS) and click **"Create Project"**.
3. Once ready, click "Continue".
4. In the left-hand sidebar menu, click **Build → Firestore Database** and click **"Create database"**:
   - Select your database region (e.g. *nam5 (us-central)* or *europe-west*). Click Next.
   - Select **"Start in test mode"** (allows immediate read/write). Click **Create**.
5. Once the Firestore database is ready, go to the left menu and click **Build → Rules** tab. Ensure your rules allow reads and writes (they should look like this under test mode):
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if true;
       }
     }
   }
   ```
   *(Note: You can secure these rules later using standard Firebase Auth or session key validations if required.)*

---

## 🚀 Step 2: Register Web App & Grab Config Credentials
*Time required: 1 minute | Cost: $0*

1. Click the **Gear Icon (Settings) → Project Settings** in the top left sidebar.
2. Under "Your apps" at the bottom of the page, click the **Web Icon (</>)**:
   - **App nickname:** `Ragworth-CEO-Dashboard`
   - Check the box **"Also set up Firebase Hosting for this app"** and click **Register App**.
3. Skip the SDK scripts setup and click Next.
4. Copy the `firebaseConfig` credentials displayed in the settings code block. It will look like this:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "ragworth-2026.firebaseapp.com",
     projectId: "ragworth-2026",
     storageBucket: "ragworth-2026.appspot.com",
     messagingSenderId: "...",
     appId: "..."
   };
   ```
5. Open your local [static/firebase_config.js](file:///d:/Coding/Projects/Ragworth/static/firebase_config.js) file and **paste these credentials** inside the config dictionary!
6. **Set `const USE_FIREBASE = true;`** at the bottom of that file. 
7. *That's it!* Your frontend dashboard is now immediately armed to read and write directly to the Cloud Firestore database in real-time, completely serverless!

---

## 🌐 Step 3: Deploy 24/7 on Firebase Hosting (Free Domain)
*Time required: 2 minutes | Cost: $0*

Deploying takes one command and automatically provisions a secure, free HTTPS domain.

1. Open PowerShell inside `d:\Coding\Projects\Ragworth`.
2. Install the global Firebase command line tool:
   ```powershell
   npm install -g firebase-tools
   ```
3. Log into your Google / Firebase account from the terminal:
   ```powershell
   firebase login
   ```
   *(This will open a browser tab. Click your Google account and click "Allow".)*
4. Initialize the project directory:
   ```powershell
   firebase init
   ```
   - Use the arrow keys to scroll to **Hosting: Configure files for Firebase Hosting...**, press the **Spacebar** to select it, and press **Enter**.
   - Select **"Use an existing project"** and press Enter.
   - Choose your `ragworth-2026` project and press Enter.
   - For **What do you want to use as your public directory?**, type **`static`** and press Enter.
   - For **Configure as a single-page app?**, type **`N`** (No) and press Enter.
   - For **Set up automatic builds and deploys with GitHub?**, type **`N`** (No) and press Enter.
   - For **File static/index.html already exists. Overwrite?**, type **`N`** (No) and press Enter.
5. Deploy your platform:
   ```powershell
   firebase deploy
   ```
6. *Firebase CLI will instantly upload your Quiet Luxury dashboard and serve it under two secure, free, 24/7 SSL-encrypted domains:*
   - **`https://ragworth-2026.web.app`**
   - **`https://ragworth-2026.firebaseapp.com`**

---

## 👑 Step 4: Map Your Custom DNS Domain (GoDaddy, Namecheap, etc.)
*Time required: 2 minutes | Cost: $0 on Firebase*

To bind your own domain (e.g. `dashboard.ragon.co`) completely free:

1. Open your Firebase Console and go to **Build → Hosting**.
2. Click **"Add Custom Domain"**.
3. Type in your custom domain and follow the simple on-screen DNS instructions:
   - Add the specified **TXT record** in GoDaddy/Namecheap to prove ownership.
   - Add the specified **A records** pointing to Firebase's global IPs.
4. *Firebase will automatically provision a Let's Encrypt SSL certificate and serve it on your custom domain with zero maintenance!*
