@echo off
title GoldSentinel - neue Addon-Versionen automatisch installieren: AUS
cd /d "%~dp0"
rem UP-AUTO1 (ab 2.3.21): schaltet "addons_auto_installieren" in uploader_config.json aus. Danach den Uploader neu starten.
where py >nul 2>nul
if not errorlevel 1 (py -3 uploader.py --addons-auto aus) else (python uploader.py --addons-auto aus)
