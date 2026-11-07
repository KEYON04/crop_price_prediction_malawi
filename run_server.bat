@echo off
title AgriPrice Malawi - National Crop Intelligence System
echo =========================================================================
echo   Starting AgriPrice Malawi - National Decision & Arbitrage Platform
echo   Backend: Django REST Framework | Districts: All 28 Districts
echo   Crops: Maize, Rice, Beans
echo =========================================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment (.venv)...
    ".venv\Scripts\python.exe" run_server.py
) else (
    python run_server.py
)
pause
