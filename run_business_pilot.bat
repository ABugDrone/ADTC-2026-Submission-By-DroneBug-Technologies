@echo off
setlocal enabledelayedexpansion
title BusinessPilot AI - Fast Launcher

cd /d "%~dp0"
set "ROOT=%CD%"
set "LLAMA_PORT=8033"
set "APP_PORT=8081"

cls
echo ============================================
echo   BusinessPilot AI - Launching System
echo ============================================
echo.

:: --- 1. Clean up old processes ^& wait for sockets to free ---
echo [*] Cleaning up previous sessions...
taskkill /f /im llama-server.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq *BusinessPilot*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%LLAMA_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%APP_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8082" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1

:: Pause 3 seconds so Windows fully releases sockets
timeout /t 3 /nobreak >nul

:: --- 2. Paths Verification ---
set "LLAMA_DIR=%ROOT%\llama-b9895-bin-win-cpu-x64"
set "MODEL_PATH=%ROOT%\model\tiny-aya-earth-q4_k_m.gguf"

if not exist "%LLAMA_DIR%\llama-server.exe" (
    echo [ERROR] llama-server.exe not found in %LLAMA_DIR%
    pause & exit /b 1
)
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model not found at %MODEL_PATH%
    pause & exit /b 1
)

:: --- 3. Launch llama-server with wider context, K/V cache quant, and embedding ---
echo [1/2] Starting llama-server on port %LLAMA_PORT%...
start "BusinessPilot-Llama" /d "%LLAMA_DIR%" /min llama-server.exe -m "%MODEL_PATH%" --jinja -c 4096 --context-shift -ctk q8_0 -ctv q8_0 -n -1 -t 4 -b 512 --host 127.0.0.1 --port %LLAMA_PORT% --embedding --pooling mean

:wait_llama
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',%LLAMA_PORT%);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto wait_llama
echo     ^> Model server is READY on port %LLAMA_PORT%

:: --- 4. Launch Gradio App ---
echo [2/2] Starting Gradio App on port %APP_PORT%...
start "BusinessPilot-App" /min "%ROOT%\run_app.bat"

:wait_app
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',%APP_PORT%);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto wait_app
echo     ^> Gradio App is READY on port %APP_PORT%

:: --- 5. Open Browser ---
echo Launching Browser...
start "" "http://localhost:%APP_PORT%"

echo.
echo ============================================
echo   BusinessPilot AI Running Successfully!
echo   App:   http://localhost:%APP_PORT%
echo   Model: http://127.0.0.1:%LLAMA_PORT%
echo ============================================
echo Press any key to stop all servers...
pause >nul

:: --- Shutdown ---
echo Stopping servers...
taskkill /f /im llama-server.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq *BusinessPilot*" >nul 2>&1
exit /b 0
