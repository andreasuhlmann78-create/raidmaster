@echo off
title GoldSentinel - Daten-Repo fuer die Pruefung einrichten
cd /d "%~dp0"
rem ab 2.3.1: zuerst den Python-Starter py (sonst meldet der Store-Alias von python eine verwirrende Zeile)
where py >nul 2>nul
if not errorlevel 1 (py -3 uploader.py --daten-einrichten) else (python uploader.py --daten-einrichten)
