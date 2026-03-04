@echo off
title TikTokBatchFactory - Installer
echo.
echo ============================================
echo   TikTokBatchFactory - Installing...
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python first:
    echo   1. Go to https://www.python.org/downloads/
    echo   2. Download Python 3.10 or newer
    echo   3. IMPORTANT: Check "Add Python to PATH" during install
    echo   4. Run this installer again
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Upgrade pip
echo [STEP 1/2] Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install requirements
echo [STEP 2/2] Installing dependencies...
python -m pip install -r "%~dp0requirements.txt"
echo.

if %errorlevel% neq 0 (
    echo [ERROR] Some packages failed to install.
    echo Try running this script as Administrator.
    pause
    exit /b 1
)

echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Place your service_account.json in the "credentials" folder
echo   2. Place your .ttf font file in the "fonts" folder
echo   3. Make sure your Google Sheet is named "TikTokBatchFactory"
echo   4. Double-click "run.bat" to start processing
echo.
pause
