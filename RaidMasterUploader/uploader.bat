@echo off
title RaidMaster-Uploader
cd /d "%~dp0"
rem ab 2.3.1: zuerst den Python-Starter py (sonst meldet der Store-Alias von python eine verwirrende Zeile)
where py >nul 2>nul
if not errorlevel 1 (py -3 uploader.py) else (python uploader.py)
pause
