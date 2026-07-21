@echo off
title BusinessPilot - Gradio App
cd /d "%~dp0"

:: Offline mode env vars
set GRADIO_ANALYTICS_ENABLED=False
set HF_HUB_DISABLE_TELEMETRY=1

echo ============================================
echo   Starting Gradio Application
echo ============================================
echo.

:: 1. Activate Virtual Environment if present
if exist "%~dp0venv\Scripts\activate.bat" (
    echo Activating virtual environment (venv)...
    call "%~dp0venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    echo Activating virtual environment (.venv)...
    call "%~dp0.venv\Scripts\activate.bat"
)

:: 2. Launch Python script safely
if exist "%~dp0app.py" (
    python "%~dp0app.py"
) else if exist "%~dp0main.py" (
    python "%~dp0main.py"
) else (
    echo [ERROR] Could not find app.py or main.py in this folder!
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo [ERROR] Python application stopped or crashed. Check traceback above.
    pause
)
