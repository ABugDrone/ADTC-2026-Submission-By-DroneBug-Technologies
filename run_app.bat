@echo off
title BusinessPilot AI - Streamlit App
cd /d "%~dp0"
set "PYTHON_SCRIPTS=%APPDATA%\Python\Python314\Scripts"
set "PATH=%PYTHON_SCRIPTS%;%PATH%"

:: Verify dependencies are installed (offline check only)
python -c "import streamlit, pandas, plotly, requests, httpx, plyer, sqlite_vec, numpy" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing Python packages.
    echo Run: pip install streamlit pandas plotly requests httpx plyer sqlite-vec
    timeout /t 10 >nul
    exit /b 1
)

echo ============================================
echo  BusinessPilot AI - Offline Business Copilot
echo ============================================
echo.
echo Starting Streamlit app on port 8081...
echo.
echo   Open in browser: http://localhost:8081
echo   Press Ctrl+C to stop
echo.
"%PYTHON_SCRIPTS%\streamlit.exe" run app.py --server.port 8081
