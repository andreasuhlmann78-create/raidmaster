@echo off
title RaidMaster-Bot
cd /d "%~dp0"

set PY=python
where py >nul 2>nul && set PY=py -3

if not exist ".venv\Scripts\python.exe" (
    echo Richte den Bot beim ersten Start ein ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Python wurde nicht gefunden. Bitte Python 3.11 oder neuer installieren - siehe ANLEITUNG.md
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
".venv\Scripts\python.exe" launcher.py
echo.
echo Der Bot wurde beendet.
pause
