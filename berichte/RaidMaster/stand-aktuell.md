# Stand RaidMaster-Sitzung

## Stand 24.11.2026 07:59 · Addon 3.0.41 · Uploader 2.3.20
- Addon 3.0.41 gepusht (download/RaidMaster-3.0.41.zip, -latest.zip, Discord-Text raid_addon_intro.md; der Bot postet
  #raid-addon beim Update selbst). addon_check OK. Bericht 2026-11-24-0758 – zur Prüfung.
  Inhalt: SH-V3 (Test v3) + Sync aus shared/, Platzhalter "?" mit Tooltip (T197), Dev-Sicht geprüft (T196), gemeinsames
  Adressbuch im Livedaten-Wächter (SB2, Gegenprobe T198), Lesbarkeit L1/L8 (T199, Gegenprobe T200, 2 Farben heller,
  Schrift nie unter GameFontNormalSmall), 11 Schätz-Zeitangaben in der Prüfliste entfernt, Realm-Prüfung: nichts getrennt.
- Uploader 2.3.20 (UP-ALT + UP-TAGE-a) gepusht, Bericht 2026-11-24-0737 (mit Nachtrag) – zur Prüfung. 2.3.19 vom
  Supervisor 07:40 angenommen. 2.3.16–2.3.18 zur Prüfung.

## Gerade in Arbeit
- nichts

## Nächste Schritte (Reihenfolge)
1. Nach Freigabe des Nutzers: Uploader 2.3.20 per Bot verteilen (/uploader nur_programm:True an ihn, an_offiziere:True).
2. Nach Meldung "alle Rechner umgestellt": Daten-Repo lokal prüfen (Zweig "sicherung", uploader 2.3.20 bei 4 Rechnern,
   "tage", nur .lua.gz in aktuell/, main = sicherung) – Bericht.
3. Ingametest 3.0.41 auswerten (Testbericht in #testberichte): T199 echt gemessen, SB2 mit echtem Adressbuch, T196/T197.
4. Nächste Addon-Version: L2–L7 als Prüfungen (L3 DKP gleich in Liste/Tooltip/!dkp, L4 Summen; L2/L5/L6 Prüfliste),
   Taktik-"ca."-Zahlen in RaidData.lua nach Entscheid der Prüf-Sitzung.

## Offen beim Nutzer
- Freigabe: Uploader 2.3.20 per Bot an ihn und die Offiziere schicken?
- Uploader 2.3.20 auf allen 4 liefernden Rechnern ganz entpacken + neu starten (ältere werden abgewiesen, auch 2.3.19).
- RaidMaster 3.0.41 installieren und Ingametest: /gsdev an, /rm testroutine alles, /reload.
- Optional Uploader-Weg b) (neuer Token sperrt alte Uploader ganz aus) – Anleitung im Bericht 0737.
- Bot: PN an Besitzer alter Uploader und Bewerbungen aufräumen liegen beim Discord-Projekt.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 07:46: "repo" – Aufträge aus dem Repo weiter umsetzen (keine neuen; nächster Punkt = Addon 3.0.41).

## Wichtig zu wissen
- Leser des Daten-Repos: Zweig "sicherung", nur Rechner mit stand.json "uploader" nicht älter als VERSION in
  RaidMasterUploader/uploader.py; .lua und .lua.gz lesen.
- Uploader-Tests: test_daten 46, test_sync 53, test_uploader 23, test_umfassend 14 – grün. ZIP = Ordner (Workflow prüft).
- Addon-Nachbildung: berichte/RaidMaster/offline (lua5.1 run_routine.lua; SHOWID=T196,T197 zeigt einzelne; ADDONDIR=…
  für Gegenproben). Lua 5.1 ggf. neu installieren (apt-get install lua5.1).
- Bot-Versand: #gildenbank, /uploader + Tab, nur_programm:True bzw. an_offiziere:True; eingebauter Browser 1280x900, danach
  desktop. Nutzer loggt sich selbst ein.
- Echte Daten nur lokal (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Text RaidMasterBot/raid_addon_intro.md: je Teil ≤ 2000 Zeichen (jetzt 1692/1785).
