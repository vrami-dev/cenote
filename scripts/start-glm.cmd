@echo off
title GLM-5.3-Flash (Project Maya 1.1.15, Maya-S24) - port 8090
rem One model at a time: Maya keeps most of the model in pinned RAM. Set MAYA_DIR if Maya is elsewhere.
python "%~dp0guard.py" || (pause & exit /b 1)
if "%MAYA_DIR%"=="" set "MAYA_DIR=D:\project-maya-1.1.15"
cd /d "%MAYA_DIR%" || (echo Project Maya not found at %MAYA_DIR% - see glm\README.md & pause & exit /b 1)
echo Loading takes a minute or two. Then: http://127.0.0.1:8090 (dashboard) or http://127.0.0.1:8090/v1 (API).
"%MAYA_DIR%\.venv\Scripts\python.exe" maya.py --config "%~dp0..\glm\maya-maya-s24.json" --port 8090
pause
