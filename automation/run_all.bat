@echo off
REM Windows batch script to run the full pipeline
cd /d "%~dp0\.."

set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo ============================================================
echo Starting Crop Price Data & Indicator Pipeline (Northern Region)
echo Using Python: %PYTHON_CMD%
echo ============================================================

%PYTHON_CMD% automation\run_all.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pipeline failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo Pipeline finished successfully.
pause
