@echo off
title Qwen3.8-Flash-Next (Swift 1.5 fine-tune, Strata 0.1.45) - port 8080
rem One model at a time. Set STRATA_DIR if Strata 0.1.45 is not unpacked at D:\strata-0.1.45.
python "%~dp0guard.py" || (pause & exit /b 1)
if "%STRATA_DIR%"=="" set "STRATA_DIR=D:\strata-0.1.45"
if "%STRATA_PY%"=="" set "STRATA_PY=%STRATA_DIR%\.venv\Scripts\python.exe"
set "CFG=%~dp0..\qwen\strata-swift-iq3_s.json"
if /i "%~1"=="uncensored" set "CFG=%~dp0..\qwen\strata-swift-uncensored-iq3_s.json"
cd /d "%STRATA_DIR%" || (echo Strata not found at %STRATA_DIR% - see qwen\README.md & pause & exit /b 1)
echo Loading takes about 30 s. Then: http://127.0.0.1:8080 (dashboard) or http://127.0.0.1:8080/v1 (API).
"%STRATA_PY%" -u serve\server.py --engine strata --config "%CFG%" --port 8080
pause
