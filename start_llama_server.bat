@echo off
set "ROOT=%~dp0"

:: Ensure llama binaries exist
if not exist "%ROOT%llama-b9895-bin-win-cpu-x64\llama-server.exe" (
    echo ERROR: llama-server.exe not found
    echo ERROR: llama-server.exe not found > "%ROOT%llama_stdout.log"
    pause
    exit /b 1
)

:: Ensure model exists in model/ folder
if not exist "%ROOT%model\tiny-aya-earth-q4_k_m.gguf" (
    echo ERROR: Model not found at model\tiny-aya-earth-q4_k_m.gguf
    echo ERROR: Model not found > "%ROOT%llama_stdout.log"
    pause
    exit /b 1
)

cd /d "%ROOT%llama-b9895-bin-win-cpu-x64"

echo Starting llama-server... > "%ROOT%llama_stdout.log"
echo Model: %ROOT%model\tiny-aya-earth-q4_k_m.gguf >> "%ROOT%llama_stdout.log"
echo. >> "%ROOT%llama_stdout.log"

start "BusinessPilot-LlamaServer" /min cmd /c "llama-server.exe -m "..\model\tiny-aya-earth-q4_k_m.gguf" --jinja -c 2048 -t 2 -b 512 --host 127.0.0.1 --port 8033 --embedding --pooling mean >> "%ROOT%llama_stdout.log" 2>&1"
exit /b 0
