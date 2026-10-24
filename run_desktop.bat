@echo off
chcp 65001 > nul
echo =====================================================
echo    Salla Smart Excel Importer - Desktop Engine
echo =====================================================
echo.
cd /d "%~dp0"

if exist .\venv\Scripts\python.exe (
    set PY=.venv\Scripts\python.exe
) else if exist ..\salla\.venv\Scripts\python.exe (
    set PY=..\salla\.venv\Scripts\python.exe
) else (
    set PY=python
)

echo Starting engine on http://127.0.0.1:8585...
%PY% main.py
pause
