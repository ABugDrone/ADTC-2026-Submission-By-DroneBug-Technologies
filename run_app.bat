@echo off
title BusinessPilot AI - Gradio App
cd /d "%~dp0"
set "ROOT=%~dp0"

:: Locate Python
where python >nul 2>&1
if errorlevel 1 (
    for %%p in ("%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%APPDATA%\Python\Python314\python.exe" "C:\Python314\python.exe") do (
        if exist "%%~p" set "PYTHON=%%~p" & goto :found_py
    )
    echo [ERROR] Python not found on PATH or any known location. >> "%ROOT%app_stdout.log"
    timeout /t 10 >nul
    exit /b 1
)
:found_py
if not defined PYTHON set "PYTHON=python"

:: Verify dependencies are installed
"%PYTHON%" -c "import gradio, pandas, plotly, httpx, plyer, sqlite_vec, numpy" 2>nul
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

"%PYTHON%" app_gradio.py >> "%ROOT%app_stdout.log" 2>&1
