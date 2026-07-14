@echo off
cd /d "%~dp0llama-b9895-bin-win-cpu-x64"

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

:: Not found - list cache contents for diagnostics
echo MODEL_NOT_FOUND
echo DEBUG: Cache exists: %GGUF_CACHE%
dir /s "%GGUF_CACHE%" > "%~dp0llama_cache_debug.txt" 2>&1
echo DEBUG: Cache listing saved to llama_cache_debug.txt
exit /b 1

:found
echo MODEL_FOUND=%GGUF_PATH%
llama-server -m "%GGUF_PATH%" --jinja -c 4096 -t 2 -b 512 --host 127.0.0.1 --port 8033 --embedding --pooling mean
set "EXIT_CODE=%ERRORLEVEL%"
echo LLAMA_SERVER_EXIT=%EXIT_CODE%
if %EXIT_CODE% neq 0 (
    echo DEBUG: llama-server failed with exit code %EXIT_CODE%
    echo DEBUG: Check llama_stderr.log for details
)
exit /b %EXIT_CODE%
