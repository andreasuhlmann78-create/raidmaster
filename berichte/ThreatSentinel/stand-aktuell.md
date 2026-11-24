# Stand ThreatSentinel

## Stand 24.11.2026 18:47 · Version 2.5.30
Veröffentlicht 24.11. 18:46 (download/, announce/; Commit e48db583), Discord. Nicht auf CurseForge.
Bericht: berichte/ThreatSentinel/2026-11-24-1845-version-2.5.30-ts-m1-b.txt ("umgesetzt, zur Prüfung").
2.5.30 = TS-M1-b: automatische Messung (nur lesen) für ALLE Spieler, Option ns.db.m1Collect ("Messdaten sammeln", Standard EIN),
Ablage ThreatSentinelDB.m1 = { head, env, runs (Ringpuffer 20, Kampf kurz als Texte q/ev/k/p), sum, cost }, ≤ 20 KB (gemessen 17,3 KB),
Befehle (a)/(c) weiter nur Entwicklermodus. Test T-M1b neu.
2.5.29 (TS-M1-a) vom Supervisor angenommen 14:15. Ingametest 2.5.28: OK 330 · FEHLER 2 (T-M1 Testaufbau, in 2.5.29 behoben).

## Gerade in Arbeit
Nichts. Alle Aufträge bis Supervisor 24.11. 14:11 (TS-M1-b) umgesetzt.

## Nächste Schritte (Reihenfolge)
1. Bei "repo": git pull --rebase, offen-threatsentinel.txt ganz unten lesen.
2. Sobald Messdaten da sind (GSDIAG1-Protokoll mit "== Messung TS-M1" in testberichte/): Tabelle (a)–(f) im Bericht mit echten Werten
   füllen (geht / geht nicht / nicht vorhanden + Belegzeile + Aufwand). Danach entscheidet der Nutzer über einen Umbau – vorher NICHTS an
   der Anzeige ändern.
3. Neu-Bewertung T-OPT7/TU7-S1/T133 gegen "Bild in Ruhe" (Ingametest 2.5.27 lieferte die Zeile; Supervisor hat nichts verlangt).
4. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Prüflisten-Punkt M1 in WoW Forever: /ts messung kampf, EIN Gegner 5 s, dann /ts messung kampf + 3 oder mehr Gegner, dann /reload.
- Abnahme SYNC-ROLLE im Gruppenspiel mit älterer Version; Stufe-3-Messung (Era/TBC, Entwicklermodus, Kampf); Prüfliste OPT.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 14:09: normale Spieler und Offiziere liefern die Messdaten über den Uploader (Messung für alle, abschaltbar).
- 24.11. 13:33–13:35 (über Supervisor): Aggro an Plaketten in Forever messen; alles messen, was möglich ist; selbst messen beim Spielen
  (Instanz/Kampf), aber nichts verändern; (a)/(c) nur auf Befehl im Entwicklermodus.

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo; Inhalt = download/ThreatSentinel-2.5.30.zip – bei Verlust daraus entpacken).
- Veröffentlichen (Skript publish.sh im Scratchpad, bei Verlust so nachbauen): git fetch + reset auf origin/main; Zip aus dem Bauordner nach
  download/ThreatSentinel-<neu>.zip; addon_check (kein FEHLER); announce/threatsentinel__threatsentinel-<neu>.md + .ThreatSentinel.zip
  dazulegen (nichts in announce/ löschen); git rm download/ThreatSentinel-<alt>.zip; README-Version; Commit deutsch mit Co-Authored-By-
  und Claude-Session-Zeile; push; Ankunft mit git show origin/main prüfen; Zip schicken. Läuft > 2 min -> im Hintergrund starten.
- Version an zwei Stellen: ThreatSentinel.toc "## Version:" und Core.lua ns.version; CHANGELOG.md und CHANGELOG.de.md oben ergänzen.
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]
  (TS_FRAME_MS=0); 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133), sonst 0. Umgebungsmessung offline: Zeitlimit greift.
- Gegenproben-Prüfstände im Scratchpad: gp27/gp27.py (GP_MODE=halfup|env|stop|logout|strict – strict: SetValue/SetText lehnen userdata ab wie der Client), gp28/ (T-M1 mit Ausgabe der Zeilen).
- Prüfliste: höchstens 14 Punkte (T-PL1); M1 ersetzt LESBAR (Zeile LESBAR-PLAKETTEN wird weiter geschrieben).
- Messung.lua: ns.M1, ThreatSentinelDB.m1 (12 Durchläufe), Abschnitt im Diagnose-Protokoll, Test T-M1 (Bit-für-Bit-Vergleich).
- Rundung: alle Anzeigen über ns.SetGameText/ns.GameFormat (Formatierung des Spiels); Build-Text ns.BuildText/BuildLabel.
- Kampflog: in Forever/Retail nie anmelden (geblockt) – Alerts.cleuAllowed.
- Gemeinsame Dateien = shared/: Dev, Pruefliste, Game, Sync 3, Test 3, Markt 10, Takt 3 (Takt nur EnvMeasure/EnvLine).
- Hinweis an Supervisor offen: Kopf des Testberichts in shared/GoldSentinelTest.lua (Zeile 297) "Client x (Zahl)" – L6-Muster, nicht meine Datei.
- Aggrometer Stufe 3 aus (Formel nur M:MeasureS3); Rollen: ns.ROLE_UNKNOWN, ns:SecuredTank, NOTANK.
- Nutzer-Regeln: komplette Dateien, alles Deutsch, "repo" = pull, Aufträge umsetzen, veröffentlichen, Bericht, Ankunft prüfen, Zip schicken.
