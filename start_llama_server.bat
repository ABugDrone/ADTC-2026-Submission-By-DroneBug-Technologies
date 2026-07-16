@echo off
cd /d "%~dp0llama-b9895-bin-win-cpu-x64" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not find llama-b9895-bin-win-cpu-x64 directory
    pause
    exit /b 1
)

set "ROOT=%~dp0"
set "GGUF_CACHE=%USERPROFILE%\.cache\huggingface\hub\models--medmekk--Qwen2.5-1.5B-Instruct.GGUF"
set "GGUF_PATH="

:: First try: dir /s (handles symlinks better than for /r)
if exist "%GGUF_CACHE%" (
    for /f "delims=" %%f in ('dir /s /b "%GGUF_CACHE%\*.gguf" 2^>nul') do set "GGUF_PATH=%%f" & goto :found
)

:: Second try: look directly in blobs/ (no symlinks)
if exist "%GGUF_CACHE%\blobs\" (
    for /f "delims=" %%f in ('dir /b "%GGUF_CACHE%\blobs\*.gguf" 2^>nul') do set "GGUF_PATH=%GGUF_CACHE%\blobs\%%f" & goto :found
)

:: Not found
echo MODEL_NOT_FOUND > "%ROOT%llama_stdout.log"
echo DEBUG: Cache exists: %GGUF_CACHE% >> "%ROOT%llama_stdout.log"
dir /s "%GGUF_CACHE%" > "%ROOT%llama_cache_debug.txt" 2>&1
echo MODEL_NOT_FOUND — run download_model.sh first
pause
exit /b 1

:found
echo MODEL_FOUND=%GGUF_PATH% > "%ROOT%llama_stdout.log"
echo Starting llama-server... >> "%ROOT%llama_stdout.log"
llama-server -m "%GGUF_PATH%" --jinja -c 4096 -t 2 -b 512 --host 127.0.0.1 --port 8033 --embedding --pooling mean >> "%ROOT%llama_stdout.log" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
echo LLAMA_SERVER_EXIT=%EXIT_CODE% >> "%ROOT%llama_stdout.log"
exit /b %EXIT_CODE%
