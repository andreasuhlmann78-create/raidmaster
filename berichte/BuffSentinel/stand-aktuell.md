# BuffSentinel – Stand der Sitzung

## Stand 24.11.2026 10:34 · Version 0.9.62
Veröffentlicht (download/, announce/, Discord). Bericht: berichte/BuffSentinel/2026-11-24-1033-0.9.62-bs-k1-l1-p1-shv3.txt.
Umgesetzt, zur Prüfung: SH-V3 (GoldSentinelTest 3), BS-K1 (Optionen weichen aus, T267), BS-L1 (Hinweisfarbe 6,4:1),
BS-P1 (Messungen T156 je Teil, T25 längster Klick; Portionen T16/T35/T37). Nachbau 8/8 PASS.

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Ingametest 0.9.62 abwarten (Nutzer): T141/T162/T266/T267 grün? Neue "nil statt true"-FEHLER (SH-NIL) einzeln zuordnen.
2. BS-P1: T156-Zeile "Teile in ms" auswerten – ist "markt" (GoldSentinelMarkt.DiagLines, gemeinsame Datei) teuer -> Befund an
   Supervisor; sonst eigenen Teil teilen. T25 "längster einzelner Klick" auswerten.
3. T149 (leere Anker, PC zu Hause): Lauf mit 0.9.61+ – Zeile je Anker Grösse/Ankerpunkte/Skalierung; Ursache belegen, Test TU1.
4. T249: Zeilenzahl der Prüfliste im Spiel messen (GetNumLines), nicht schätzen.
5. Danach: Prüfliste von Hand (JAEGER, ENTZ, OPT …), T247 Händler (läuft von selbst), T258 Messung.

## Offen beim Nutzer
- Ingametest mit 0.9.62 (Forever) und einmal auf dem PC zu Hause (T149).
- Lesezugriff auf goldsentinel-daten am 23.11. verweigert – Frage gestellt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (24.11. 10:22 nur "repo").

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
