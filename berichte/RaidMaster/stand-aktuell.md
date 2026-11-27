# Stand RaidMaster-Sitzung

## Stand 27.11.2026 10:27 · Addon 3.0.53 · Uploader 2.3.30
- DL-ABN: neue Versionen erst announce/ (Addon) bzw. Zweig pruefung/uploader-<V> (Uploader); download/ nur nach ANGENOMMEN. Ablauf veroeffentlichen.md.
- Addon 3.0.53 (ST1 Spieler-Texte): 1 Einlog-Zeile, Hinweise einmal, Fehler 1 Zeile, Optionen 'Mithelfen', T209. Bericht 0937. Angenommen 10:30 (Abnahme im Spiel offen).
- Uploader 2.3.30 (RM-UPD3): Einstellungsdateien automatisch, nur gleicher Bot + gleicher Discord-Server; keine j/n-Frage mehr. Bericht 0759.
- 2.3.29/3.0.51 angenommen 07:50; 2.3.30/3.0.52 angenommen 08:12 (Abnahme im Betrieb offen). 
- Uploader 2.3.29 (RM-UPD2): Update ohne j, Addons Standard an, Kanal stabil (nur download/) / test. Bericht 0721.
- Addon 3.0.51: Anleitung-Tipp angepasst. 3.0.50 angenommen 26.11. (RM-P1 offen bis Ingametest).
- LevelPilot: Nutzer entschied 27.11. ~07:25 "nach Abnahme nach download/" -> LevelPilot-Sitzung (über Supervisor).
  Taktik-Zahlen erst ändern, wenn der Supervisor bestätigte Werte überträgt (Prüfliste research/raidmaster-taktikzahlen.md, ab 09.12.).
- RM-CI1: alte RaidMaster-Zips 3.0.40–3.0.43 aus download/ entfernt, README-Link 3.0.44. Bericht 0646. Ablauf: veroeffentlichen.md.
- Uploader 2.3.28 gepusht (UP-UPD1-c: "update" in stand.json trägt die NEUE Version ein; altes Fenster schickt nach Übergabe nichts mehr). Bericht 0643
  (beantwortet auch: sicherung = main = d10d6d9, kein Rückstand). Laptop UP-AUTO1 im Betrieb belegt (Supervisor 06:34).
- Uploader 2.3.27 (UP-CFG1: uploader_config/sync_config aus dem Download-Ordner nur nach j, mit Schutz). Bericht 0635.
- Uploader 2.3.26 angenommen (UP-UPD1-a: altes Fenster schliesst sich nach Update, uploader.bat darf mit ersetzt werden). Bericht 2204.
- Uploader 2.3.25 (UP-MSG2: eine Sperr-Zeile je PID; LIESMICH Entpacken). Bericht 2159 – zur Prüfung.
  Damit UP-UPD1 abnehmbar: PC mit 2.3.24 fragt j/n, Taste j.
- Uploader 2.3.24 auf PC installiert, liefert wieder; an Offiziere verschickt 21:55 (UP-UPD1: Update nur nach Taste j, Prüfung, _update/alt, Neustart mit Rückfall). Bericht 2142 – zur Prüfung.
- Uploader 2.3.23 angenommen 21:30 (UP-MIN1: Mindestversion aus RaidMasterUploader/mindestversion.txt = 2.3.20 statt "neueste").
  Bericht 2123 – zur Prüfung. 2.3.20–2.3.22 liefern erst nach Wechsel auf 2.3.23 (einmalig).
- Uploader 2.3.22 (UP-MSG1) und 2.3.21 (UP-AUTO1, PC abgenommen 20:55, Laptop offen) – vom Supervisor angenommen.
  L2–L7 mit 3.0.45; Taktik-Zahlen warten auf bestätigte Werte.

## Gerade in Arbeit
- nichts

## Nächste Schritte (Reihenfolge)
1. Uploader 2.3.20 wurde vom Supervisor per Bot verteilt (Commit ca258023) – nichts mehr zu tun.
2. Nach Meldung "alle Rechner umgestellt": Daten-Repo lokal prüfen (Zweig "sicherung", uploader 2.3.20 bei 4 Rechnern,
   "tage", nur .lua.gz in aktuell/, main = sicherung) – Bericht.
3. Ingametest 3.0.44 auswerten: Zeile UMGEBUNG, T203; Abnahme UP-AUTO1 Laptop (PC abgenommen 20:55).
4. Keine offenen Aufträge – bei "repo" neue Aufträge umsetzen.

## Offen beim Nutzer
- PC: bei der Frage im Uploader-Fenster Taste j (Abnahme UP-UPD1). Laptop UP-AUTO1 belegt.
  Beim nächsten Update (2.3.28) per j: altes Fenster schliesst sich -> Abnahme UP-UPD1-a/b und UP-UPD1-c (stand.json "update").
- Uploader 2.3.20 auf allen 4 liefernden Rechnern ganz entpacken + neu starten (ältere werden abgewiesen, auch 2.3.19).
- PC/Laptop: nach Update auf 2.3.29 einmal Addons-Testversionen-an.bat, Uploader neu starten; RaidMaster 3.0.51 /rm testroutine alles (RM-P1)
- RM-CI2: Token erstellt 13:58 (Nutzer verwahrt ihn); Auftrag an Discord-Sitzung gegeben 14:00 – Eintrag auf dem Bot-Server folgt dort Ingametest: /gsdev an, /rm testroutine alles, /reload.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 08:27–09:23 (über Supervisor): ST1 – nur nützliche Spieler-Texte ausserhalb des Testmodus.
- 27.11. 07:46: "alles vollautomatisch" – auch Einstellungsdateien ohne j/n (RM-UPD3).
- 27.11. ~07:25: stabile Versionen = nach Abnahme in download/ (LevelPilot ebenso).
- 27.11. 07:08–07:11: Uploader-Update automatisch; Addons Standard an; Mitspieler nur stabile Versionen (RM-UPD2).
  (Bericht 2049 an den Supervisor zum Weiterleiten).
  wie der Bot überspringen; gelöscht wird nichts. -> raid-addon-zusammenfassung-3.0.0.md: NICHT nachposten (Bericht 1030).

## Wichtig zu wissen
- VERÖFFENTLICHEN nur nach berichte/RaidMaster/veroeffentlichen.md (vorige Zip weg, README, Workflow-Status success).
- Leser des Daten-Repos: Zweig "sicherung", nur Rechner mit stand.json "uploader" nicht unter
  RaidMasterUploader/mindestversion.txt; .lua und .lua.gz lesen.
- Uploader-Tests: test_selfupdate 25, test_einstellungen 15, test_addons 25, test_daten 48, test_sync 55, test_uploader 23, test_umfassend 14 – grün. ZIP = Ordner (Workflow prüft).
- Addon-Nachbildung: berichte/RaidMaster/offline (lua5.1 run_routine.lua; SHOWID=T196,T197 zeigt einzelne; ADDONDIR=…
  für Gegenproben). Lua 5.1 ggf. neu installieren (apt-get install lua5.1).
- Bot-Versand: #gildenbank, /uploader + Tab, nur_programm:True bzw. an_offiziere:True; eingebauter Browser 1280x900, danach
  desktop. Nutzer loggt sich selbst ein.
- Echte Daten nur lokal (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Text RaidMasterBot/raid_addon_intro.md: je Teil ≤ 2000 Zeichen (jetzt 1692/1856).
