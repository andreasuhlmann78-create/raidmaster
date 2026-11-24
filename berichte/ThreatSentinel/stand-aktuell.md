# Stand ThreatSentinel

## Stand 24.11.2026 06:40 · Version 2.5.26
Veröffentlicht 23.11. (download/, announce/), addon_check OK ohne WARNUNG. Letzter Bericht: berichte/ThreatSentinel/2026-11-23-1035-version-2.5.26-rollen.txt.
Ingametest 2.5.26 (Nutzer 23.11. 15:37): OK 326 · FEHLER 3 · Sandbox OK · Livedaten unverändert · ganze Bilder > 40 ms: 0.

## Gerade in Arbeit
Nichts angefangen. Neue Punkte aus offen-threatsentinel.txt (Supervisor 23.11. 13:03 und 15:38) noch NICHT umgesetzt.

## Nächste Schritte (Reihenfolge)
1. git pull --rebase, offen-threatsentinel.txt ganz unten lesen.
2. TS-L3 MITTEL: im Spiel rundet das Aggrometer ,5 auf (0,5->1; 2,5->3; 72,5->73), DD-Ansicht ab (0; 2; 72). Verdacht, zu messen: der
   geschützte Weg (SetFormattedText "%.0f%%" in Meter.lua) rundet im Client anders als Lua string.format (offline: halb-gerade). Ziel: eine
   Rundung für alle Anzeigen (wie das Spiel) – z. B. DD-Ansicht ebenfalls über SetFormattedText, oder eigene Rundung überall; T-L3 und
   TU6-R1 grün. Ursache zuerst im Code belegen (welcher Weg lief im Spiel: Meter Display-Modus?).
3. TS-L6 NIEDRIG: Testzentrale "Client: 1.60.1 (71037)" -> "Build 71037" (L6 Klammerzahl ohne Wort, T187).
4. TS-U1 NIEDRIG: Umgebungsmessung wie GuildSentinel/ProfessionSentinel ("Bild in Ruhe", Median/95 %, 10 s, Zeile "Umgebung";
   GoldSentinelTakt.EnvMeasure aus shared/ unverändert kopieren, falls ThreatSentinel sie nutzt), dann T-OPT7 (27,7 ms), TU7-S1 (19,8 ms),
   T133 (17,6 ms) mit eigener Rechenzeit je Bild neu bewerten.
5. Alles als EINE Version 2.5.27 bündeln (Nutzung sparen), Bericht "umgesetzt, zur Prüfung", stand-aktuell.md neu.
6. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Ingametest der nächsten Version (/gsdev, /ts testroutine alles).
- Abnahme im Gruppenspiel: SYNC-ROLLE mit Mitspieler älterer Version (Prüfliste).
- Messung Stufe 3 sammelt sich nur in Era/TBC mit Entwicklermodus im Kampf (Zeile im Testbericht).
- Prüfliste OPT: OK/Nicht OK.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 12:43: Neue Version ersetzt im Discord den Beitrag der vorherigen Version wie bisher (Bot unverändert).
- 23.11. 11:36/12:03: in announce/ nie etwas löschen, keine alte Version neu hineinlegen. Publish-Ablauf hält das ein (löscht nur die
  alte Zip in download/). Einzige Löschung in announce/threatsentinel* war am 02.11. (vor der Regel).

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo; Inhalt = download/ThreatSentinel-2.5.26.zip – bei Verlust daraus entpacken).
- Veröffentlichen (Skript im Scratchpad der Sitzung, bei Verlust so nachbauen): git fetch + reset auf origin/main; Zip aus dem Bauordner nach
  download/ThreatSentinel-<neu>.zip; addon_check (kein FEHLER); announce/threatsentinel__threatsentinel-<neu>.md + .ThreatSentinel.zip
  dazulegen (nichts in announce/ löschen); git rm download/ThreatSentinel-<alt>.zip; README-Version; Commit deutsch mit Co-Authored-By-
  und Claude-Session-Zeile; push (bei Konflikt pull --rebase, erneut); Ankunft mit git show origin/main prüfen; Zip dem Nutzer schicken.
- Version an zwei Stellen: ThreatSentinel.toc "## Version:" und Core.lua ns.version; CHANGELOG.md und CHANGELOG.de.md oben ergänzen.
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]
  (TS_FRAME_MS=0 = Pause vor jeder Prüfung); 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133), sonst 0.
- Gemeinsame Dateien aktuell (Sync 3, Markt 10, Game 3, Test 2, Dev 2, Prüfliste 1). Takt nutzt ThreatSentinel bisher nicht.
- Aggrometer: Stufe 3 aus (TS-S3a); Formel nur in M:MeasureS3 (Meter.lua), Messwerte ThreatSentinelDB.s3mess.
- Rollen (TS-R1/R1-a): ns.ROLE_UNKNOWN, ns:SecuredTank, Zustand NOTANK, Hinweis einmal je Gruppe; unbekannte Rolle sendet "V:<ver>".
- Livedaten-Prüfung T-LIVE (R.LiveTables in TestRoutine.lua, gsTest ausgenommen); Lesbarkeit U.ReadRules/U.Readable (UICheck.lua, T187).
- Nutzer-Regeln: komplette Dateien, alles Deutsch, "repo" = pull, Aufträge umsetzen, veröffentlichen, Bericht, Ankunft prüfen, Zip schicken.
