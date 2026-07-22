@echo off
set BIN_DIR=C:\Users\pc\3D Objects\ADTC-2026-Submission-By-DroneBug-Technologies\llama-b9895-bin-win-cpu-x64
set MODEL_PATH=C:\Users\pc\3D Objects\ADTC-2026-Submission-By-DroneBug-Technologies\model\tiny-aya-earth-q4_k_m.gguf

"%BIN_DIR%\llama-server.exe" -m "%MODEL_PATH%" -c 4096 --context-shift -ctk q8_0 -ctv q8_0 -n -1 --host 127.0.0.1 --port 8033
pause