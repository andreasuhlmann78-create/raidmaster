# Stand ThreatSentinel

## Stand 24.11.2026 10:31 · Version 2.5.27
Veröffentlicht 24.11. 10:30 (download/, announce/; Commit 2c475f5f), addon_check OK ohne WARNUNG. Nicht auf CurseForge.
Bericht: berichte/ThreatSentinel/2026-11-24-1030-version-2.5.27-rundung-build-umgebung.txt ("umgesetzt, zur Prüfung").
Inhalt: TS-L3 (Rundung des Spiels überall: ns.SetGameText/ns.GameFormat), TS-L6 (Build beschriftet, ns.BuildText/BuildLabel),
TS-U1 (GoldSentinelTakt 3 kopiert, 10 s Umgebungsmessung vor jedem Lauf, Zeile "Umgebung", "Bild in Ruhe" in der Zusammenfassung),
SH-V3 (GoldSentinelTest 3 kopiert; offline keine nil-FEHLER).
Letzter Ingametest (2.5.26, 23.11. 15:37): OK 326 · FEHLER 3 (T-L3, TU6-R1, T187) · Sandbox OK · ganze Bilder > 40 ms: 0.

## Gerade in Arbeit
Nichts. Alle Aufträge bis Supervisor 24.11. 07:20 (SH-V3) umgesetzt.

## Nächste Schritte (Reihenfolge)
1. Bei "repo": git pull --rebase, offen-threatsentinel.txt ganz unten lesen, Prüfergebnis 2.5.27 abwarten -> NICHT warten, nächster Punkt.
2. Nach Ingametest 2.5.27: T-OPT7 (27,7 ms), TU7-S1 (19,8 ms), T133 (17,6 ms) gegen "Bild in Ruhe" neu bewerten (Verdacht, zu messen:
   Hauptstadt-Last). Erscheinen im Client nil-FEHLER (SH-NIL): jeden einzeln zuordnen und begründen, nie die Prüfung abschwächen.
3. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Ingametest 2.5.27: /gsdev, /ts testroutine alles (die ersten 10 s nicht bewegen – Umgebungsmessung). Erwartet T-L3, T-L6, TU6-R1 grün.
- Abnahme im Gruppenspiel: SYNC-ROLLE mit Mitspieler älterer Version (Prüfliste).
- Messung Stufe 3 sammelt sich nur in Era/TBC mit Entwicklermodus im Kampf (Zeile im Testbericht).
- Prüfliste OPT: OK/Nicht OK.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (24.11.: "repo" = Aufträge umsetzen und veröffentlichen wie bisher).

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo; Inhalt = download/ThreatSentinel-2.5.27.zip – bei Verlust daraus entpacken).
- Veröffentlichen (Skript publish.sh im Scratchpad, bei Verlust so nachbauen): git fetch + reset auf origin/main; Zip aus dem Bauordner nach
  download/ThreatSentinel-<neu>.zip; addon_check (kein FEHLER); announce/threatsentinel__threatsentinel-<neu>.md + .ThreatSentinel.zip
  dazulegen (nichts in announce/ löschen); git rm download/ThreatSentinel-<alt>.zip; README-Version; Commit deutsch mit Co-Authored-By-
  und Claude-Session-Zeile; push (bei Konflikt pull --rebase, erneut); Ankunft mit git show origin/main prüfen; Zip dem Nutzer schicken.
  Das Skript läuft > 2 min (addon_check) -> im Hintergrund starten.
- Version an zwei Stellen: ThreatSentinel.toc "## Version:" und Core.lua ns.version; CHANGELOG.md und CHANGELOG.de.md oben ergänzen.
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]
  (TS_FRAME_MS=0 = Pause vor jeder Prüfung); 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133), sonst 0.
  Offline läuft die Umgebungsmessung nicht (kein OnUpdate) -> Zeitlimit greift, Zeile "Messung abgebrochen: Zeitlimit" ist dort normal.
- Gegenproben-Prüfstand 2.5.27 (Scratchpad gp27/gp27.py, GP_MODE=halfup|env|stop|logout): halfup = SetFormattedText rundet ,5 auf wie im Client.
- Gemeinsame Dateien = shared/: Dev, Pruefliste, Game, Sync 3, Test 3, Markt 10, Takt 3 (Takt nur für EnvMeasure/EnvLine).
- Hinweis an Supervisor offen: Kopf des Testberichts in shared/GoldSentinelTest.lua (Zeile 297) zeigt "Client x (Zahl)" – L6-Muster, nicht meine Datei.
- Aggrometer: Stufe 3 aus (TS-S3a); Formel nur in M:MeasureS3 (Meter.lua), Messwerte ThreatSentinelDB.s3mess.
- Rollen (TS-R1/R1-a): ns.ROLE_UNKNOWN, ns:SecuredTank, Zustand NOTANK, Hinweis einmal je Gruppe; unbekannte Rolle sendet "V:<ver>".
- Livedaten-Prüfung T-LIVE; Lesbarkeit U.ReadRules/U.Readable (UICheck.lua, T187, T-L6); Rundung T-L3 (35 Vergleiche gegen eigenen FontString).
- Nutzer-Regeln: komplette Dateien, alles Deutsch, "repo" = pull, Aufträge umsetzen, veröffentlichen, Bericht, Ankunft prüfen, Zip schicken.
