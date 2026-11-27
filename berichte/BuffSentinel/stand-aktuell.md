# BuffSentinel – Stand der Sitzung

## Stand 27.11.2026 10:27 · Version 0.9.69
0.9.69 ANGENOMMEN (ST1, 27.11. 10:30), Abnahme im Spiel offen; liegt in download/ (einzige BS-Zip). DL-ABN umgesetzt (Bericht 2026-11-27 …-dl-abn-ablauf.txt).
REGEL DL-ABN: neue Version zuerst NUR announce/ (Anhang …BuffSentinel.zip), download/ erst nach "ANGENOMMEN" für genau diese Version (prom.sh).

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.67 (Supervisor); Messdaten BS-M1 aus goldsentinel-daten (m1 in BuffSentinel.lua) – Auswertung Supervisor, ich kann mitlesen.
2. Nutzer: T270 Klick-Raster im Spiel (Gruppe, Entwicklermodus), T134, T106 (Raid 40).
3. Danach Nutzer-Entscheid zur Liste 1–6 (Bericht 24.11. 14:08) anhand der Kampfmessungen.
4. BS-P1: Befund GoldSentinelMarkt.DiagLines (gemeinsame Datei) liegt beim Supervisor; eigener Teil erledigt.
5. T249 Zeilenmessung, Prüfliste von Hand; T149 PC zu Hause.

## Offen beim Nutzer
- Ingametest 0.9.65; T270 in einer Gruppe.
- (erledigt) Lesezugriff goldsentinel-daten: Nutzer 26.11. 11:57 im Chat erlaubt; Klon /home/claude/goldsentinel-daten (nur lesen).

## Entscheide des Nutzers seit letztem Stand
- 27.11. ~07:25 (über Supervisor, DL-ABN): "Nach Abnahme nach download/".
- 27.11. 08:27–09:23 (über Supervisor, ST1): nur nützliche Spieler-Texte (A Einlog-Zeile, B Mithelfen, C Fehler 1×, D Messwerte nur Protokoll, E Tipps 1×).
- 26.11. 11:57 (Chat): "Du darfst das Daten-Repo goldsentinel-daten lesen".

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git; nach Neustart aus download/<letzte Zip> wiederherstellen!). Skripte im scratchpad:
  rel2.sh <alt> <neu> "<msg>" (Version, CHANGELOG, Zip als announce-Anhang, Nachbau 8×, addon_check, push – NICHT download/), prom.sh <v>
  (nach ANGENOMMEN: Zip nach download/, md5 gleich, ältere raus, README), rep2.sh <thema> "<msg>" < Text,
  test/off.py (lupa, Lua 5.1), echt/echt_r1.lua + echt/names.py (echte Daten; Dateien .lua UND .lua.gz! Realms nur als <Realm>, keine Rechner-/Kontonamen anderer Spieler in Berichte). Locales: scratchpad/loc.py <json {KEY:[en,de]}> schreibt direkt in Locales.lua.
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet.
- Messung: Messung.lua (M1), Allowed = Option + nicht Testroutine (testAllow nur für T269); Befehl dev.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 4. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
