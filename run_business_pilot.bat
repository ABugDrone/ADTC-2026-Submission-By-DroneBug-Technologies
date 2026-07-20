@echo off
setlocal enabledelayedexpansion
title BusinessPilot AI - Launcher
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

cd /d "%~dp0"
set "ROOT=%CD%"
set "LLAMA_PORT=8033"
set "APP_PORT=8081"

cls
echo %ESC%[36m============================================%ESC%[0m
echo %ESC%[36m   BusinessPilot AI - Offline Business Copilot%ESC%[0m
echo %ESC%[36m============================================%ESC%[0m
echo.

:: --- 0. Clean up stale processes ---
echo %ESC%[90m[*] Cleaning up previous session...%ESC%[0m
taskkill /f /im python.exe /fi "WINDOWTITLE eq *BusinessPilot*" >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq *llama*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%LLAMA_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%APP_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
timeout /t 2 /nobreak >nul

:: --- 1. Start Tiny Aya Earth model server ---
echo %ESC%[33m[1/2]%ESC%[0m Starting local AI model...
echo       llama-server with tiny-aya-earth Q4_K_M on port %LLAMA_PORT%
start "BusinessPilot-LlamaServer" /min "%ROOT%\run tiny aya model.bat"

set "WAIT=0"
<nul set /p "=      waiting"
:wait_llama
timeout /t 1 /nobreak >nul
set /a WAIT+=1
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',%LLAMA_PORT%);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    if !WAIT! geq 60 (
        echo.
        echo %ESC%[91m[ERROR]%ESC%[0m Model server did not respond within 60s.
        echo         Check llama_stderr.log for details.
        pause
        exit /b 1
    )
    <nul set /p "=."
    goto wait_llama
)
echo.
echo %ESC%[32m      Model server is up on port %LLAMA_PORT%.%ESC%[0m

:: --- 2. Start the Gradio app ---
echo %ESC%[33m[2/2]%ESC%[0m Starting BusinessPilot app...
echo       Gradio dashboard on port %APP_PORT%
start "BusinessPilot-App" /min "%ROOT%\run_app.bat"

set "WAIT=0"
<nul set /p "=      waiting"
:wait_app
timeout /t 1 /nobreak >nul
set /a WAIT+=1
powershell -NoProfile -Command "try{(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',%APP_PORT%);exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    if !WAIT! geq 40 (
        echo.
        echo %ESC%[91m[ERROR]%ESC%[0m App did not respond within 40s.
        echo         Check app_stdout.log for details.
        pause
        exit /b 1
    )
    <nul set /p "=."
    goto wait_app
)
echo.
echo %ESC%[32m      App is up on port %APP_PORT%.%ESC%[0m

:: --- 3. Open browser to Gradio ---
echo %ESC%[33m[3/3]%ESC%[0m Opening browser...
start "" "http://localhost:%APP_PORT%"

echo.
echo %ESC%[32m============================================%ESC%[0m
echo %ESC%[32m  BusinessPilot AI is running.%ESC%[0m
echo %ESC%[32m============================================%ESC%[0m
echo.
echo   App:    http://localhost:%APP_PORT%
echo   Model:  http://127.0.0.1:%LLAMA_PORT%
echo.
echo   Press any key in THIS window to stop all servers.
pause >nul

:: --- Cleanup ---
echo.
echo %ESC%[90mStopping servers...%ESC%[0m
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%LLAMA_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%APP_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
echo Done.
timeout /t 1 /nobreak >nul
exit /b 0
