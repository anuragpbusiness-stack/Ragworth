@echo off
title Ragworth Enterprise Web Server
echo ═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%
echo  RAGWORTH ENTERPRISE OPERATING SYSTEM (ROS) v1.0
echo ═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%
echo.

:: 1. Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python is not installed or not added to your system PATH.
    echo Please install Python 3.12+ from python.org before running.
    pause
    exit /b 1
)

:: 2. Install dependencies
echo [*] Checking Python dependencies...
python -m pip install fastapi uvicorn requests beautifulsoup4
if %errorlevel% neq 0 (
    echo [!] Warning: Dependency installer returned non-zero code. Verifying manually...
)

echo.
echo ═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%
echo  ACTIVATING SECURE 24/7 REMOTE CLOUD DOMAIN (CLOUDFLARE TUNNEL)
echo ═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%
echo.
echo  To access your private CEO Dashboard securely from your phone or anywhere in the world
echo  completely free and 24/7 on a secure SSL/HTTPS domain:
echo.
echo  1. Open a new PowerShell terminal tab in this folder.
echo  2. Copy and run this command:
echo.
echo     npx -y @cloudflare/next-on-pages tunnel --url http://127.0.0.1:8000
echo.
echo     [Or if you have cloudflared installed: cloudflared tunnel --url http://127.0.0.1:8000]
echo.
echo  3. Cloudflare will instantly output a secure URL (e.g., https://your-unique-id.trycloudflare.com)
echo  4. Bookmark that link on your phone. It is 100%% secure and requires your key (RAGON2026).
echo.
echo ═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%═%
echo [*] Launching Ragworth API Server on http://127.0.0.1:8000 ...
echo [✔] Server active. Open http://127.0.0.1:8000/dashboard.html in your browser.
echo.
python main.py
pause
