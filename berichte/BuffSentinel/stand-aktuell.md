# BuffSentinel – Stand der Sitzung

## Stand 24.11.2026 13:33 · Version 0.9.63
Veröffentlicht (download/, announce/, Discord). Bericht: berichte/BuffSentinel/2026-11-24-1333-0.9.63-bs-i2-t149.txt.
0.9.63: BS-I2 T149 Toleranz 0,01 für leere Anker (falscher FEHLER bei Skalierung 0,773, Wert 1,000x), 6 Stellen, Gegenprobe.
0.9.62 (Ingametest 24.11. Laptop): OK 222 · FEHLER 2 (T149, T162 = BS-I2) · keine nil-FEHLER; T141/T266 grün, BS-L1 erledigt.

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.63: T149/T162 grün? T267 im Client? Werte T156 "Teile in ms", T25 "längster Klick" (aus 0.9.62 nicht gemeldet).
2. BS-P1: T156-Zeile "Teile in ms" auswerten – ist "markt" (GoldSentinelMarkt.DiagLines, gemeinsame Datei) teuer -> Befund an
   Supervisor; sonst eigenen Teil teilen. T25 "längster einzelner Klick" auswerten.
3. T149 PC zu Hause: mit 0.9.63 nochmals laufen lassen (6 Stellen zeigen den genauen Wert).
4. T249: Zeilenzahl der Prüfliste im Spiel messen (GetNumLines), nicht schätzen.
5. Danach: Prüfliste von Hand (JAEGER, ENTZ, OPT …), T247 Händler (läuft von selbst), T258 Messung.

## Offen beim Nutzer
- Ingametest mit 0.9.63 (Laptop und PC zu Hause).
- Lesezugriff auf goldsentinel-daten am 23.11. verweigert – Frage gestellt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (24.11. 13:30 nur "repo").

## Wichtig zu wissen
- Quelle: /home/claude/BuffSentinel (kein Git). Veröffentlichen mit Skripten im Arbeitsordner der Sitzung (scratchpad):
  rel.sh <alt> <neu> <msg> (baut, Nachbau 8 Läufe, addon_check, pub.sh), rep.sh <thema> <msg> < Text (Bericht + Push);
  Eingaben en.md/de.md/ann.md. Vorher Repo sauber (pub.sh macht git pull --rebase). announce/ NIE löschen.
- Locales aus Generator (scratchpad/loc: keys/manual/extra.json, genloc.py), 1238 Schlüssel je Sprache.
- Nachbau: berichte/BuffSentinel/offline/run_offline.lua; erwartet rot: T13 T23 T28 T45 T51 T95. BS_SHOW=T267,T156 zeigt Ergebnisse.
  Lauf: BS_ROOT=/home/claude/BuffSentinel BS_FLAVOR=forever|era|tbc|retail BS_LOCALE=deDE|enUS python3 scratchpad/test/off.py.
- addon_check hier ohne lupa (nicht installierbar): WARNUNG Lua-Syntax – GitHub-Lauf prüft voll.
- Shared nur unverändert kopieren: Sync 3, Markt v10, Dev v2, Test 3.
- Ausweichen: BS.UIAvoidOthers (UICheck.lua) wie ThreatSentinel U.BestPlace; Donate.lua nutzt Namensraum "ns", nicht "BS".
- Lua 5.1: nie über pcall hinweg yielden (BS.DiagPart-Haken läuft nach dem pcall). Berichte nur "umgesetzt, zur Prüfung".
