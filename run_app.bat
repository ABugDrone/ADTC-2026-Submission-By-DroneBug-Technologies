@echo off
title BusinessPilot AI - Gradio App
cd /d "%~dp0"
set "ROOT=%~dp0"

:: Disable telemetry (fully offline)
set GRADIO_ANALYTICS_ENABLED=False
set HF_HUB_DISABLE_TELEMETRY=1
set NO_PROXY=localhost,127.0.0.1,::1
set HTTPS_PROXY=
set HTTP_PROXY=

:: Free port 8081 and 8082 before starting
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8081" ^| find "LISTENING" 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8082" ^| find "LISTENING" 2^>nul') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Locate Python
where python >nul 2>&1
if errorlevel 1 (
    for %%p in ("%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "C:\Python313\python.exe" "C:\Python312\python.exe" "C:\Python311\python.exe") do (
        if exist "%%~p" set "PYTHON=%%~p" & goto :found_py
    )
    echo [ERROR] Python not found >> "%ROOT%app_stdout.log"
    timeout /t 10 >nul
    exit /b 1
)
:found_py
if not defined PYTHON set "PYTHON=python"

echo ============================================ >> "%ROOT%app_stdout.log"
echo  BusinessPilot AI - Offline Business Copilot >> "%ROOT%app_stdout.log"
echo ============================================ >> "%ROOT%app_stdout.log"
echo. >> "%ROOT%app_stdout.log"
echo Starting Gradio app on port 8081... >> "%ROOT%app_stdout.log"
echo   Open: http://localhost:8081 >> "%ROOT%app_stdout.log"
echo. >> "%ROOT%app_stdout.log"

"%PYTHON%" app_gradio.py >> "%ROOT%app_stdout.log" 2>&1
