@echo off
title GoldSentinel - Daten-Repo fuer die Pruefung einrichten
cd /d "%~dp0"
python uploader.py --daten-einrichten
if errorlevel 9009 py -3 uploader.py --daten-einrichten
