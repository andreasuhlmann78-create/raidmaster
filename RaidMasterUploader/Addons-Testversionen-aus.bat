@echo off
title GoldSentinel - auch Testversionen (Discord) der Addons installieren: AUS
cd /d "%~dp0"
rem RM-UPD2 (ab 2.3.29): "addons_kanal" in uploader_config.json = "stabil" (nur stabile Versionen, Standard). Danach den Uploader neu starten.
where py >nul 2>nul
if not errorlevel 1 (py -3 uploader.py --addons-test aus) else (python uploader.py --addons-test aus)
