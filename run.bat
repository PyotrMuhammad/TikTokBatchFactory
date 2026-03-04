@echo off
title TikTokBatchFactory - Batch Video Generator
echo.
echo ============================================
echo   TikTokBatchFactory - Starting...
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Download Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Run the main script
python "%~dp0main.py"

:: Keep window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Script exited with an error.
    pause
)
