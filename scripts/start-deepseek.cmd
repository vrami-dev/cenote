@echo off
title DeepSeek-V4.1-Flash-1017 (cenote, Xolotl engine) - port 8150
rem One model at a time: DeepSeek pins a 72 GiB RAM arena and most of a 24 GB GPU.
python "%~dp0guard.py" || (pause & exit /b 1)
rem Model names: deepseek-v4.1-flash-xolotl (light, default), ...-fast, ...-exact.
rem No plain-text copy of every answer in %%TEMP%%: serve_ds41.py reads this from its own environment.
set "STRATA_TEXT_LOG=0"
cd /d "%~dp0..\engines\xolotl"
if not exist ".venv-serve\Scripts\python.exe" (
  echo Missing engines\xolotl\.venv-serve - see deepseek\SETUP.md, step 5.
  pause
  exit /b 1
)
echo Loading takes about a minute. Then: http://127.0.0.1:8150 (dashboard) or http://127.0.0.1:8150/v1 (API).
".venv-serve\Scripts\python.exe" -I tools\v41\serve\serve_ds41.py --engine strata --config "%~dp0..\deepseek\strata-ds41-1017dsx-win.json" --port 8150
pause
