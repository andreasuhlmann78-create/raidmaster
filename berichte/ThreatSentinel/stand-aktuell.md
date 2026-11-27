# Stand ThreatSentinel

## Stand 27.11.2026 09:40 · Version 2.5.31
Veröffentlicht 27.11. 09:38 (download/, announce/; Commit ba47c4ff), Discord. Nicht auf CurseForge.
Bericht: berichte/ThreatSentinel/2026-11-27-0938-st1-spielertexte.txt ("umgesetzt, zur Prüfung").
2.5.31 = ST1 Spieler-Texte: ns:LoginLine (1 Zeile mit Version, Testmodus wie bisher), ns:DevPrint (Ini-Prüfung still), ns:HintOnce
(ThreatSentinelDB.hintsSeen), Fehler ERR_ONCE 1x je Sitzung in jedem Client, Abschnitt "Mithelfen" (id dev, für alle) mit diagSend,
m1Collect, dungeonCheck(+Raid), diagShow; Testzentrale/Bilder/Ini-Bericht nur Testmodus; "Tank-Sync" -> "Mit Tanks abstimmen".
Tests T-ST1 (neu), T-DEV1 angepasst. Dazu SHARED-T4: GoldSentinelTest 4 kopiert.
2.5.30 (TS-M1-b) angenommen 24.11. 18:56; Ingametest 2.5.30: OK 333 · FEHLER 0.

## Gerade in Arbeit
Nichts. Alle Aufträge bis Supervisor 27.11. 09:25 (ST1) umgesetzt.

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
- 27.11. 08:27–09:23 (über Supervisor, ST1): nur nützliche Spieler-Texte; Version beim Einloggen sichtbar; Befehle/Hilfe unverändert;
  Entwicklungs-Schalter in "Mithelfen"; Fehler 1 Zeile je Sitzung; Messwerte nur im Protokoll; Tipps einmal; Testmodus wie bisher.
- 24.11. 14:09: normale Spieler und Offiziere liefern die Messdaten über den Uploader (Messung für alle, abschaltbar).
- 24.11. 13:33–13:35 (über Supervisor): Aggro an Plaketten in Forever messen; alles messen, was möglich ist; selbst messen beim Spielen
  (Instanz/Kampf), aber nichts verändern; (a)/(c) nur auf Befehl im Entwicklermodus.

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo, ging am 27.11. verloren -> aus Zip entpackt; Inhalt = download/ThreatSentinel-2.5.31.zip – bei Verlust daraus entpacken).
- Veröffentlichen (Skript publish.sh im Scratchpad, bei Verlust so nachbauen): git fetch + reset auf origin/main; Zip aus dem Bauordner nach
  download/ThreatSentinel-<neu>.zip; addon_check (kein FEHLER); announce/threatsentinel__threatsentinel-<neu>.md + .ThreatSentinel.zip
  dazulegen (nichts in announce/ löschen); git rm download/ThreatSentinel-<alt>.zip; README-Version; Commit deutsch mit Co-Authored-By-
  und Claude-Session-Zeile; push; Ankunft mit git show origin/main prüfen; Zip schicken. Läuft > 2 min -> im Hintergrund starten. OK-Erkennung: Zeile "## ThreatSentinel-<neu>.zip: OK" (nicht nach "FEHLER" suchen – "FEHLER 0" steht auch in OK-Läufen).
- Version an zwei Stellen: ThreatSentinel.toc "## Version:" und Core.lua ns.version; CHANGELOG.md und CHANGELOG.de.md oben ergänzen.
- Offline-Routine (neuer Container: pip install --break-system-packages lupa): python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]
  (TS_FRAME_MS=0); 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133), sonst 0. Umgebungsmessung offline: Zeitlimit greift.
- Gegenproben-Prüfstände im Scratchpad: gp27/gp27.py (GP_MODE=halfup|env|stop|logout|strict – strict: SetValue/SetText lehnen userdata ab wie der Client), gp28/ (T-M1 mit Ausgabe der Zeilen).
- Prüfliste: höchstens 14 Punkte (T-PL1); M1 ersetzt LESBAR (Zeile LESBAR-PLAKETTEN wird weiter geschrieben).
- Messung.lua: ns.M1, ThreatSentinelDB.m1 (12 Durchläufe), Abschnitt im Diagnose-Protokoll, Test T-M1 (Bit-für-Bit-Vergleich).
- Rundung: alle Anzeigen über ns.SetGameText/ns.GameFormat (Formatierung des Spiels); Build-Text ns.BuildText/BuildLabel.
- Kampflog: in Forever/Retail nie anmelden (geblockt) – Alerts.cleuAllowed.
- Gemeinsame Dateien = shared/: Dev, Pruefliste, Game, Sync 3, Test 4, Markt 10, Takt 3 (Takt nur EnvMeasure/EnvLine).
- Hinweis an Supervisor offen: Kopf des Testberichts in shared/GoldSentinelTest.lua (Zeile 297) "Client x (Zahl)" – L6-Muster, nicht meine Datei.
- Aggrometer Stufe 3 aus (Formel nur M:MeasureS3); Rollen: ns.ROLE_UNKNOWN, ns:SecuredTank, NOTANK.
- Nutzer-Regeln: komplette Dateien, alles Deutsch, "repo" = pull, Aufträge umsetzen, veröffentlichen, Bericht, Ankunft prüfen, Zip schicken.
