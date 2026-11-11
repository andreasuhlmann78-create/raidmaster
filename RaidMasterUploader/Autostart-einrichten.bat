@echo off
title RaidMaster-Uploader: Autostart einrichten
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut([Environment]::GetFolderPath('Startup')+'\RaidMaster-Uploader.lnk'); $s.TargetPath='%~dp0uploader.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.Description='RaidMaster-Uploader (Abgleich PC/Laptop)'; $s.Save()"
if errorlevel 1 (echo Fehler - Verknuepfung nicht angelegt.) else (echo Fertig: Der Uploader startet ab jetzt bei jeder Anmeldung automatisch, minimiert.)
pause
