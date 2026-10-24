@echo off
title RaidMaster-Uploader
cd /d "%~dp0"
python uploader.py
if errorlevel 9009 py -3 uploader.py
pause
