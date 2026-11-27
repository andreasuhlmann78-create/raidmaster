# BuffSentinel – Stand der Sitzung

## Stand 27.11.2026 09:38 · Version 0.9.69
Veröffentlicht (download/ nur 0.9.69.zip, README, announce/, Discord). Bericht: berichte/BuffSentinel/2026-11-27-0935-0.9.69-st1-spielertexte.txt.
0.9.69: ST1 Spieler-Texte – Einlog-Zeile "BuffSentinel <v> – /bsen …", Fehler 1×/Sitzung (BS.ErrorOnce), Tipps 1× (BS.TipOnce, gdb.tipsSeen),
AnnounceSpec nur dev, Optionen-Abschnitt "Mithelfen" (shareServer, m1.collect, diagSend, Bericht/Fehler/Wer nutzt). T272.
0.9.68 angenommen; BS-DL1 erledigt. BS-M1-b: Supervisor wartet auf Messdaten (Offizier A braucht 0.9.68+, Kampf in Gruppe).

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
- 27.11. 08:27–09:23 (über Supervisor, ST1): nur nützliche Spieler-Texte (A Einlog-Zeile, B Mithelfen, C Fehler 1×, D Messwerte nur Protokoll, E Tipps 1×).
- 26.11. 11:57 (Chat): "Du darfst das Daten-Repo goldsentinel-daten lesen".

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git; nach Neustart aus download/<letzte Zip> wiederherstellen!). Skripte im scratchpad:
  rel2.sh <alt> <neu> "<msg>" (Version, CHANGELOG, Zip, Nachbau 8×, addon_check, announce, ältere BS-Zips raus + README-Link, push), rep2.sh <thema> "<msg>" < Text,
  test/off.py (lupa, Lua 5.1), echt/echt_r1.lua + echt/names.py (echte Daten; Dateien .lua UND .lua.gz! Realms nur als <Realm>, keine Rechner-/Kontonamen anderer Spieler in Berichte). Locales: scratchpad/loc.py <json {KEY:[en,de]}> schreibt direkt in Locales.lua.
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet.
- Messung: Messung.lua (M1), Allowed = Option + nicht Testroutine (testAllow nur für T269); Befehl dev.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 4. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
