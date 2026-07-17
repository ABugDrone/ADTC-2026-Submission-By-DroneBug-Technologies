@echo off
cd /d "%~dp0llama-b9895-bin-win-cpu-x64" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not find llama-b9895-bin-win-cpu-x64 directory
    pause
    exit /b 1
)

set "ROOT=%~dp0"
echo Starting llama-server with tiny-aya-earth... > "%ROOT%llama_stdout.log"
llama-server.exe -m "%ROOT%model\tiny-aya-earth-q4_k_m.gguf" --jinja -c 2048 --host 127.0.0.1 --port 8033 >> "%ROOT%llama_stdout.log" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
echo LLAMA_SERVER_EXIT=%EXIT_CODE% >> "%ROOT%llama_stdout.log"
exit /b %EXIT_CODE%
