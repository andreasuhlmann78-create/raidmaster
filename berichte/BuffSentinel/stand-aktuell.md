# BuffSentinel – Stand der Sitzung

## Stand 26.11.2026 12:03 · Version 0.9.67
Veröffentlicht (download/, announce/, Discord). Bericht: berichte/BuffSentinel/ (2026-11-26 …-0.9.67-bs-r1-echte-daten.txt).
0.9.67: BS-R1 mit ECHTEN Daten (goldsentinel-daten, 2 PCs) geprüft; Positionen (pos/btnPos/winPos) aus "Name-" gewinnen.
0.9.66: Realm leer -> stabiler Schlüssel + Zusammenführen + Sicherung profileMerged; GoldSentinelTest v4; Version in Hilfe.

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
- 26.11. 11:57 (Chat): "Du darfst das Daten-Repo goldsentinel-daten lesen".

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git; nach Neustart aus download/<letzte Zip> wiederherstellen!). Skripte im scratchpad:
  rel2.sh <alt> <neu> "<msg>" (Version, CHANGELOG, Zip, Nachbau 8×, addon_check, announce, push), rep2.sh <thema> "<msg>" < Text,
  test/off.py (lupa, Lua 5.1), echt/echt_r1.lua (echte Daten). Locales-Generator weg: neue Texte direkt in Locales.lua (EN+DE).
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet.
- Messung: Messung.lua (M1), Allowed = Option + nicht Testroutine (testAllow nur für T269); Befehl dev.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 4. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
