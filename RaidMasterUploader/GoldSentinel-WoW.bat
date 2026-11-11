@echo off
title GoldSentinel - WoW mit Abgleich starten
cd /d "%~dp0"
python uploader.py --wow-start
if errorlevel 9009 py -3 uploader.py --wow-start
