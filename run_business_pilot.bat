@echo off
setlocal enabledelayedexpansion
title BusinessPilot AI Launcher

cd /d "%~dp0"
set "ROOT=%~dp0"
set "LLAMA_PORT=8083"
set "HTTP_PORT=8081"

cls
echo ============================================
echo   BusinessPilot AI - Fast Offline Launcher
echo ============================================
echo.

:: --- 1. Clean up stale processes ---
echo [*] Cleaning up previous sessions...
taskkill /f /im llama-server.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%LLAMA_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":%HTTP_PORT%" ^| find "LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1

:: --- 2. Verify paths ---
set "LLAMA_DIR=%ROOT%llama-b9895-bin-win-cpu-x64"
set "MODEL_PATH=%ROOT%model\tiny-aya-earth-q4_k_m.gguf"

if not exist "%LLAMA_DIR%\llama-server.exe" (
    echo [ERROR] llama-server.exe not found in "%LLAMA_DIR%"
    pause & exit /b 1
)
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model not found at "%MODEL_PATH%"
    pause & exit /b 1
)

:: --- 3. Start llama-server (RAM-optimized) ---
echo [1/3] Starting optimized llama-server on port %LLAMA_PORT%...
start "BusinessPilot-Llama" /d "%LLAMA_DIR%" /min llama-server.exe -m "%MODEL_PATH%" -c 2048 -t 4 -b 256 -ub 128 -np 1 --mmap --host 127.0.0.1 --port %LLAMA_PORT% --ui-mcp-proxy

:wait_llama
timeout /t 1 /nobreak >nul
netstat -ano | findstr /C:":%LLAMA_PORT% " | findstr /C:"LISTENING" >nul 2>&1
if errorlevel 1 goto wait_llama
echo      ^> Model server is READY on port %LLAMA_PORT%.

:: --- 4. Start HTTP server for frontend ---
echo [2/3] Starting HTTP server on port %HTTP_PORT%...
start "BusinessPilot-HTTP" /min python -m http.server %HTTP_PORT% --directory "%ROOT%static"

:wait_http
timeout /t 1 /nobreak >nul
netstat -ano | findstr /C:":%HTTP_PORT% " | findstr /C:"LISTENING" >nul 2>&1
if errorlevel 1 goto wait_http
echo      ^> HTTP server is READY on port %HTTP_PORT%.

:: --- 5. Open Browser ---
echo [3/3] Launching Browser...
start "" "http://localhost:%HTTP_PORT%/"

echo.
echo ============================================
echo   BusinessPilot AI is fully operational!
echo ============================================
echo   AI Server:  http://127.0.0.1:%LLAMA_PORT%
echo   Frontend:   http://localhost:%HTTP_PORT%/
echo ============================================
echo Press any key in THIS window to stop all servers...
pause >nul

:: --- Shutdown ---
echo Stopping servers...
taskkill /f /im llama-server.exe >nul 2>&1
taskkill /f /im python.exe /fi "WindowTitle eq *BusinessPilot*" >nul 2>&1
exit /b 0
