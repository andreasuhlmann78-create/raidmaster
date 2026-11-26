# Stand RaidMaster-Sitzung

## Stand 26.11.2026 09:46 · Addon 3.0.50 · Uploader 2.3.28
- Addon 3.0.50: SHARED-T4 (GoldSentinelTest v4), Testwerkzeug weicht aus, RM-P1 Messung Speicherbereinigung je Bild. Bericht 0946.
- 3.0.49 angenommen; im Spiel RM-K2 und Einstellungen/Esc abgenommen (25.11.). RM-CI2 beim Discord-Projekt (D-CI2).
- Ganze Prüfung rot durch AHSentinel-0.65.393.zip (nicht meins).
- Addon 3.0.47: 3.0.46 (Taktik-Zahlen) zurückgenommen – Entscheid des Nutzers 08:24 "nicht löschen, auf korrekte Angaben warten".
  Taktik-Zahlen erst ändern, wenn der Supervisor bestätigte Werte überträgt (Prüfliste research/raidmaster-taktikzahlen.md, ab 09.12.).
- Addon 3.0.45 gepusht (L3/L4 als Prüfungen T204/T205, nur Testroutine). Uploader 2.3.27/2.3.28 und RM-CI1 vom Supervisor angenommen 06:53.
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
- Addon 3.0.44 (RM-UMG1, Zeile UMGEBUNG, T203) – angenommen 20:50, Ingametest offen. 3.0.43 im Ingametest 0 FEHLER.
- Addon 3.0.41–3.0.43: Platzhalter "?", Dev-Sicht, SB2-Adressbuch, Lesbarkeit L1/L8, Klassen-/Item-Farben, T116 je Addon.
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
- RaidMaster 3.0.50: /rm testroutine alles -> PORTIONEN-Zeile zeigt beim längsten Bild die Speicheränderung (RM-P1)
- RM-CI2: Token erstellt 13:58 (Nutzer verwahrt ihn); Auftrag an Discord-Sitzung gegeben 14:00 – Eintrag auf dem Bot-Server folgt dort Ingametest: /gsdev an, /rm testroutine alles, /reload.

## Entscheide des Nutzers seit letztem Stand
- 25.11. ~13:50: RM-CI2 – GitHub-Token (nur raidmaster, Actions) auf dem Bot-Server; Bot löst Testberichte-Abholung aus (Discord-Projekt).
- 25.11. 11:39 (über Supervisor): Offiziere schalten Addons-automatisch ein (UP-DOC2, nur Doku, Standard bleibt AUS).
- 25.11. 08:24: Taktik-Zahlen NICHT löschen/ändern; geplante Aufgabe prüft (ab 09.12.), bestätigte Werte über Supervisor einsetzen.
- 25.11. 06:29: Einstellungsdateien aus dem Download-Ordner übernehmen, "mit Schutz" (UP-CFG1) – nach Hinweis auf die Risiken.
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
