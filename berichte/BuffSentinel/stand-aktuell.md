# BuffSentinel – Stand der Sitzung

## Stand 25.11.2026 09:09 · Version 0.9.65
Veröffentlicht (download/, announce/, Discord; nicht CurseForge). Bericht: berichte/BuffSentinel/2026-11-25-0909-0.9.65-bs-m1b-messung-alle.txt.
0.9.65: BS-M1-b – Messung für ALLE Spieler (Option "Messdaten sammeln", Teilen, Standard ein), BuffSentinelDB.m1 ver 2
(head/runs 20/dict/sum/cost, ≤ 20 KB); T269 erweitert; T179 misst GM.DiagLines.
Angenommen: 0.9.64 Teil B (Klick-Raster) + BS-T1; Ingametest 0.9.64 0 FEHLER (25.11. 08:54).

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.65 abwarten; Messdaten aus BuffSentinel.lua (Uploader) – Auswertung macht der Supervisor, Fragen beantworten.
2. Nutzer: T270 Klick-Raster im Spiel (Gruppe, Entwicklermodus), T134, T106 (Raid 40).
3. Danach Nutzer-Entscheid zur Liste 1–6 (Bericht 24.11. 14:08) anhand der Kampfmessungen.
4. BS-P1: Befund GoldSentinelMarkt.DiagLines (gemeinsame Datei) liegt beim Supervisor; eigener Teil erledigt.
5. T249 Zeilenmessung, Prüfliste von Hand; T149 PC zu Hause.

## Offen beim Nutzer
- Ingametest 0.9.65; T270 in einer Gruppe.
- Lesezugriff goldsentinel-daten (23.11.) – keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 14:09 (über Supervisor): Messung durch normale Spieler/Offiziere, Daten über den Uploader.

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git). scratchpad: rel.sh (bump+pub+Nachbau aus der Zip), rep.sh, Dateiliste list20.txt
  (neue Dateien eintragen!), post.sh (export S=<scratchpad>). Locales: scratchpad/loc/extra.json + genloc.py (1256 Schlüssel).
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet.
- Messung: Messung.lua (M1), Allowed = Option + nicht Testroutine (testAllow nur für T269); Befehl dev.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 3. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
