@echo off
REM Cloudflare Tunnel Setup Helper for Windows
REM This script automates the tunnel creation and configuration

setlocal enabledelayedexpansion

echo.
echo ===================================
echo ClassAlert Cloudflare Tunnel Setup
echo ===================================
echo.

REM Check if cloudflared is installed
where cloudflared >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ERROR: cloudflared is not installed or not in PATH
    echo.
    echo Please download it from:
    echo https://github.com/cloudflare/cloudflared/releases
    echo.
    echo Then add it to your PATH or run:
    echo   npm install -g cloudflare-cli
    echo.
    pause
    exit /b 1
)

echo [OK] cloudflared is installed
cloudflared --version

echo.
echo Step 1: Authenticate with Cloudflare
echo -----------------------------------
echo Logging in to Cloudflare...
cloudflared tunnel login
if %errorlevel% neq 0 (
    echo ERROR: Failed to authenticate
    pause
    exit /b 1
)

echo.
echo Step 2: Create Tunnel
echo -----------------------------------
set /p TUNNEL_NAME="Enter tunnel name (default: classalert-db): "
if "!TUNNEL_NAME!"=="" set "TUNNEL_NAME=classalert-db"

cloudflared tunnel create !TUNNEL_NAME!
if %errorlevel% neq 0 (
    echo ERROR: Failed to create tunnel
    pause
    exit /b 1
)

echo.
echo Step 3: Get Tunnel ID
echo -----------------------------------
set /p DOMAIN="Enter your domain (e.g., yourdomain.com): "

echo.
echo Creating DNS route: db.!DOMAIN!
cloudflared tunnel route dns !TUNNEL_NAME! db.!DOMAIN!
if %errorlevel% neq 0 (
    echo ERROR: Failed to create DNS route
    pause
    exit /b 1
)

echo.
echo Step 4: Create Config File
echo -----------------------------------

REM Get tunnel credentials file
for /f "delims=" %%F in ('dir /b %USERPROFILE%\.cloudflared\*.json') do (
    set "CRED_FILE=%%F"
    goto :found
)
:found

set "CONFIG_PATH=%USERPROFILE%\.cloudflared\config.yml"
set "TUNNEL_ID=!CRED_FILE:.json=!"

(
echo tunnel: !TUNNEL_NAME!
echo credentials-file: %USERPROFILE%\.cloudflared\!CRED_FILE!
echo.
echo ingress:
echo   - hostname: db.!DOMAIN!
echo     service: tcp://localhost:5432
echo   - service: http_status:404
) > "!CONFIG_PATH!"

echo Created config file: !CONFIG_PATH!
echo.
type "!CONFIG_PATH!"

echo.
echo Step 5: Test Tunnel
echo -----------------------------------
echo.
echo Starting tunnel... (Press Ctrl+C to stop)
echo.
cloudflared tunnel run !TUNNEL_NAME!

pause
