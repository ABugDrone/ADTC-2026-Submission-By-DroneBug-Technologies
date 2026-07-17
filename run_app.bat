@echo off
title BusinessPilot AI - Gradio App
cd /d "%~dp0"
set "ROOT=%~dp0"
set "PYTHON_SCRIPTS=%APPDATA%\Python\Python314\Scripts"
set "PATH=%PYTHON_SCRIPTS%;%PATH%"

:: Verify dependencies are installed
python -c "import gradio, pandas, plotly, httpx, plyer, sqlite_vec, numpy" 2>nul
if errorlevel 1 (
    echo [ERROR] Missing Python packages. >> "%ROOT%app_stdout.log"
    echo Run: pip install gradio pandas plotly httpx plyer sqlite-vec numpy >> "%ROOT%app_stdout.log"
    timeout /t 10 >nul
    exit /b 1
)

echo ============================================ >> "%ROOT%app_stdout.log"
echo  BusinessPilot AI - Offline Business Copilot >> "%ROOT%app_stdout.log"
echo ============================================ >> "%ROOT%app_stdout.log"
echo. >> "%ROOT%app_stdout.log"
echo Starting Gradio app on port 8081... >> "%ROOT%app_stdout.log"
echo. >> "%ROOT%app_stdout.log"
echo   Open in browser: http://localhost:8081 >> "%ROOT%app_stdout.log"
echo   Press Ctrl+C to stop >> "%ROOT%app_stdout.log"
echo. >> "%ROOT%app_stdout.log"

python app_gradio.py >> "%ROOT%app_stdout.log" 2>&1
