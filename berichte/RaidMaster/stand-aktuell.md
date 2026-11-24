# Stand RaidMaster-Sitzung

## Stand 24.11.2026 20:47 · Addon 3.0.44 · Uploader 2.3.21
- Addon 3.0.44 gepusht (RM-UMG1: Testroutine erkennt Umgebung/Bedienung, Zeile UMGEBUNG, T203; T111 bereinigt vorher).
  Bericht 2026-11-24-2046 – zur Prüfung.
- Uploader 2.3.21 (UP-AUTO1, vom Supervisor 20:50 angenommen; an Offiziere verteilt 20:52) HOCH: installiert neue Addon-Versionen selbst, Schalter Standard aus,
  Addons-automatisch-an/-aus.bat). Bericht 2026-11-24-2037 – zur Prüfung. Addon 3.0.43 im Ingametest 0 FEHLER (RM-I2 erledigt).
- Addon 3.0.43 gepusht (RM-I2 Rest: Item-Qualitätsfarben über RM.ReadableText lesbar, Nummer im Discord-Leitfaden;
  T202). Bericht 2026-11-24-1024 – zur Prüfung. Ingametest 3.0.42 (10:17): 147 OK, 1 FEHLER (T199) -> in 3.0.43; RM-I1 erledigt.
- Addon 3.0.42 gepusht (RM-I1: T116 misst Speicher je Addon; RM-I2: Klassenfarben/Grau/Rot heller, T201). Bericht
  2026-11-24-1010 – zur Prüfung. Ingametest 3.0.41 (09:09): 145 OK, 2 FEHLER (RM-I1, RM-I2) -> in 3.0.42.
- Addon 3.0.41 (download/RaidMaster-3.0.41.zip, -latest.zip, Discord-Text raid_addon_intro.md; der Bot postet
  #raid-addon beim Update selbst). addon_check OK. Bericht 2026-11-24-0758 – zur Prüfung.
  Inhalt: SH-V3 (Test v3) + Sync aus shared/, Platzhalter "?" mit Tooltip (T197), Dev-Sicht geprüft (T196), gemeinsames
  Adressbuch im Livedaten-Wächter (SB2, Gegenprobe T198), Lesbarkeit L1/L8 (T199, Gegenprobe T200, 2 Farben heller,
  Schrift nie unter GameFontNormalSmall), 11 Schätz-Zeitangaben in der Prüfliste entfernt, Realm-Prüfung: nichts getrennt.
- Uploader 2.3.20 (UP-ALT + UP-TAGE-a) gepusht, Bericht 2026-11-24-0737 (mit Nachtrag) – zur Prüfung. 2.3.19 vom
  Supervisor 07:40 angenommen. 2.3.16–2.3.18 zur Prüfung.

## Gerade in Arbeit
- nichts

## Nächste Schritte (Reihenfolge)
1. Uploader 2.3.20 wurde vom Supervisor per Bot verteilt (Commit ca258023) – nichts mehr zu tun.
2. Nach Meldung "alle Rechner umgestellt": Daten-Repo lokal prüfen (Zweig "sicherung", uploader 2.3.20 bei 4 Rechnern,
   "tage", nur .lua.gz in aktuell/, main = sicherung) – Bericht.
3. Ingametest 3.0.44 auswerten: Zeile UMGEBUNG, T203; Abnahme UP-AUTO1 (PC/Laptop).
4. Nächste Addon-Version: L2–L7 als Prüfungen (L3 DKP gleich in Liste/Tooltip/!dkp, L4 Summen; L2/L5/L6 Prüfliste),
   Taktik-"ca."-Zahlen in RaidData.lua nach Entscheid der Prüf-Sitzung.

## Offen beim Nutzer
- Uploader 2.3.21 auf allen liefernden Rechnern (UP-ALT: 2.3.20 wird jetzt abgewiesen). Auf PC und Laptop
  Addons-automatisch-an.bat ausführen, Uploader neu starten -> Abnahme UP-AUTO1.
- Uploader 2.3.20 auf allen 4 liefernden Rechnern ganz entpacken + neu starten (ältere werden abgewiesen, auch 2.3.19).
- RaidMaster 3.0.44 installieren und Ingametest: /gsdev an, /rm testroutine alles, /reload.
- Optional Uploader-Weg b) (neuer Token sperrt alte Uploader ganz aus) – Anleitung im Bericht 0737.
- Bot: PN an Besitzer alter Uploader und Bewerbungen aufräumen liegen beim Discord-Projekt.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 20:52 Nutzer: "meine offiziere haben den neuen auch bekommen" – Uploader 2.3.21 an Offiziere verteilt.
- 24.11. 20:49: "das discord projekt soll den offiziere das seden" – Uploader 2.3.21 an Offiziere über das Discord-Projekt
  (Bericht 2049 an den Supervisor zum Weiterleiten).
- 24.11. 20:04 (über Supervisor): Umgebung/Bedienung in allen Testroutinen erkennen (RM-UMG1).
- 24.11. 20:28 (über Supervisor): Uploader installiert neue Addon-Versionen selbst, PC und Laptop (UP-AUTO1).
- 24.11. 20:29: "repo".
- 24.11. 10:29: D-CHK1 – fehlt im Discord wirklich etwas, entscheidet diese Sitzung über Nachposten; ältere Fassungen soll die Prüfung
  wie der Bot überspringen; gelöscht wird nichts. -> raid-addon-zusammenfassung-3.0.0.md: NICHT nachposten (Bericht 1030).
- 24.11. 10:22: "repo" – RM-I2 Rest umgesetzt.
- 24.11. 10:06: "repo" – RM-I1/RM-I2 umgesetzt.
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
