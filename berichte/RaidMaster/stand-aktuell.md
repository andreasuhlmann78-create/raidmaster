# Stand RaidMaster-Sitzung

## Stand 24.11.2026 22:00 · Addon 3.0.44 · Uploader 2.3.25
- Uploader 2.3.25 gepusht (UP-MSG2: eine Sperr-Zeile je PID; LIESMICH Entpacken). Bericht 2159 – zur Prüfung.
  Damit UP-UPD1 abnehmbar: PC mit 2.3.24 fragt j/n, Taste j.
- Uploader 2.3.24 auf PC installiert, liefert wieder; an Offiziere verschickt 21:55 (UP-UPD1: Update nur nach Taste j, Prüfung, _update/alt, Neustart mit Rückfall). Bericht 2142 – zur Prüfung.
- Uploader 2.3.23 angenommen 21:30 (UP-MIN1: Mindestversion aus RaidMasterUploader/mindestversion.txt = 2.3.20 statt "neueste").
  Bericht 2123 – zur Prüfung. 2.3.20–2.3.22 liefern erst nach Wechsel auf 2.3.23 (einmalig).
- Uploader 2.3.22 (UP-MSG1) und 2.3.21 (UP-AUTO1, PC abgenommen 20:55, Laptop offen) – vom Supervisor angenommen.
- Addon 3.0.44 (RM-UMG1, Zeile UMGEBUNG, T203) – angenommen 20:50, Ingametest offen. 3.0.43 im Ingametest 0 FEHLER.
- Addon 3.0.41–3.0.43: Platzhalter "?", Dev-Sicht, SB2-Adressbuch, Lesbarkeit L1/L8, Klassen-/Item-Farben, T116 je Addon.
  Offen aus 3.0.41: L2–L7 als Prüfungen, Taktik-"ca."-Zahlen (Entscheid Prüf-Sitzung).
- Uploader 2.3.20 (UP-ALT, "sicherung") angenommen 10:30.

## Gerade in Arbeit
- nichts

## Nächste Schritte (Reihenfolge)
1. Uploader 2.3.20 wurde vom Supervisor per Bot verteilt (Commit ca258023) – nichts mehr zu tun.
2. Nach Meldung "alle Rechner umgestellt": Daten-Repo lokal prüfen (Zweig "sicherung", uploader 2.3.20 bei 4 Rechnern,
   "tage", nur .lua.gz in aktuell/, main = sicherung) – Bericht.
3. Ingametest 3.0.44 auswerten: Zeile UMGEBUNG, T203; Abnahme UP-AUTO1 Laptop (PC abgenommen 20:55).
4. Nächste Addon-Version: L2–L7 als Prüfungen (L3 DKP gleich in Liste/Tooltip/!dkp, L4 Summen; L2/L5/L6 Prüfliste),
   Taktik-"ca."-Zahlen in RaidData.lua nach Entscheid der Prüf-Sitzung.

## Offen beim Nutzer
- PC: bei der Frage im Uploader-Fenster Taste j (Abnahme UP-UPD1). Laptop: 2.3.24/2.3.25 einmal von Hand, Addons-automatisch-an.bat. Auf PC und Laptop
  Addons-automatisch-an.bat ausführen, Uploader neu starten -> Abnahme UP-AUTO1.
- Uploader 2.3.20 auf allen 4 liefernden Rechnern ganz entpacken + neu starten (ältere werden abgewiesen, auch 2.3.19).
- RaidMaster 3.0.44 installieren und Ingametest: /gsdev an, /rm testroutine alles, /reload.
- Optional Uploader-Weg b) (neuer Token sperrt alte Uploader ganz aus) – Anleitung im Bericht 0737.
- Bot: PN an Besitzer alter Uploader und Bewerbungen aufräumen liegen beim Discord-Projekt.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 21:36 (über Supervisor): Uploader-Update nur auf Knopfdruck mit Rückfrage j/n, kein Selbst-Update (UP-UPD1).
- 24.11. 21:18 (über Supervisor): Mindestversion statt "neueste" (UP-MIN1), nur bei Daten/Format/Prüfung/Sicherheit erhöhen.
- 24.11. 20:52 Nutzer: "meine offiziere haben den neuen auch bekommen" – Uploader 2.3.21 an Offiziere verteilt.
- 24.11. 20:49: "das discord projekt soll den offiziere das seden" – Uploader 2.3.21 an Offiziere über das Discord-Projekt
  (Bericht 2049 an den Supervisor zum Weiterleiten).
- 24.11. 20:04 (über Supervisor): Umgebung/Bedienung in allen Testroutinen erkennen (RM-UMG1).
- 24.11. 20:28 (über Supervisor): Uploader installiert neue Addon-Versionen selbst, PC und Laptop (UP-AUTO1).
- 24.11. 20:29: "repo".
- 24.11. 10:29: D-CHK1 – fehlt im Discord wirklich etwas, entscheidet diese Sitzung über Nachposten; ältere Fassungen soll die Prüfung
  wie der Bot überspringen; gelöscht wird nichts. -> raid-addon-zusammenfassung-3.0.0.md: NICHT nachposten (Bericht 1030).
- 24.11. 07:46/10:06/10:22: "repo" – Aufträge aus dem Repo umsetzen (3.0.41–3.0.43).

## Wichtig zu wissen
- Leser des Daten-Repos: Zweig "sicherung", nur Rechner mit stand.json "uploader" nicht unter
  RaidMasterUploader/mindestversion.txt; .lua und .lua.gz lesen.
- Uploader-Tests: test_addons 25, test_daten 46, test_sync 53, test_uploader 23, test_umfassend 14 – grün. ZIP = Ordner (Workflow prüft).
- Addon-Nachbildung: berichte/RaidMaster/offline (lua5.1 run_routine.lua; SHOWID=T196,T197 zeigt einzelne; ADDONDIR=…
  für Gegenproben). Lua 5.1 ggf. neu installieren (apt-get install lua5.1).
- Bot-Versand: #gildenbank, /uploader + Tab, nur_programm:True bzw. an_offiziere:True; eingebauter Browser 1280x900, danach
  desktop. Nutzer loggt sich selbst ein.
- Echte Daten nur lokal (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Text RaidMasterBot/raid_addon_intro.md: je Teil ≤ 2000 Zeichen (jetzt 1692/1856).
