# BuffSentinel – Stand der Sitzung

## Stand 24.11.2026 14:09 · Version 0.9.64
Veröffentlicht (download/, announce/, Discord; nicht CurseForge). Bericht: berichte/BuffSentinel/2026-11-24-1408-0.9.64-bs-m1-reinigen-forever.txt.
0.9.64: BS-M1 Teil A Messung (Messung.lua, nur Entwicklermodus, nur lesen; /bsen reinigen messen) + Teil B Klick-Raster Forever
(Option dispel.foreverGrid, dev, Standard aus), BS-T1 Texte. Tests T268/T269 (Nachbau), T270 im Client.
Abgenommen: BS-L1 (0.9.62), BS-I2 (Ingametest 0.9.63 13:44: OK 224, FEHLER 0).

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.64 + T270 (Raster im Spiel: Klick reinigt, kein "Aktion blockiert") + /bsen reinigen messen in Gruppe/Instanz.
2. Messergebnisse BS-M1 auswerten (Diagnose-Protokoll, Zeilen "BS-M1"): lesbar im Kampf? -> Vorschläge 1–6 im Bericht 14:08.
3. Nach bestandenem T270 (Entscheid Supervisor/Nutzer): Raster für alle (dev weg, Standard?) – nur auf Entscheid.
4. BS-P1: T156 "Teile in ms", T25 "längster Klick" auswerten (Supervisor liest aus Testbericht).
5. T249 Zeilenmessung, Prüfliste von Hand; T149 PC zu Hause (6 Stellen).

## Offen beim Nutzer
- Ingametest 0.9.64 (Gruppe mit Debuff nötig für T270).
- Lesezugriff goldsentinel-daten (23.11.) – keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 13:52 (über Supervisor, BS-M1): "baue das… buffsentinel soll das prüfen… und was sonst noch möglich wäre".

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git). Skripte im scratchpad: rel.sh (bump+pub+Nachbau), pub.sh, rep.sh; Dateiliste
  für die Zip: scratchpad/list20.txt – NEUE DATEIEN DORT EINTRAGEN (0.9.64: Messung.lua vergessen, addon_check hat es gefangen).
  Nachbau nach pub: scratchpad/post.sh mit export S=<scratchpad>.
- Locales: scratchpad/loc (extra.json überschreibt auch bestehende Schlüssel), genloc.py; 1253 Schlüssel.
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet, nicht geändert.
- Attrappe mock_wow.lua (eigene Datei) kennt jetzt GetAlpha.
- Forever-Raster: BS:ForeverGridOn(), BS.dispelForever, ResolveDispelSpells(force) nur für Anzeige; Attribute nur ohne Kampfsperre.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 3. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
