# BuffSentinel – Stand der Sitzung

## Stand 24.11.2026 06:43 · Version 0.9.61
Veröffentlicht (download/, announce/, Discord). Letzte Berichte: berichte/BuffSentinel/2026-11-23-0843-0.9.61-livedaten-lesbarkeit.txt,
2026-11-23-1237-announce-nicht-loeschen.txt. Ingametest 0.9.61 (23.11. 13:19, Forever, Krieger 30): OK 220 · FEHLER 3 · Sandbox OK ·
echte Aktionen 0; BS-I1 erledigt (Supervisor).

## Gerade in Arbeit
Nichts angefangen. Neue Punkte aus offen-buffsentinel.txt (Supervisor 23.11. 13:20) noch NICHT bearbeitet:

## Nächste Schritte (Reihenfolge)
1. BS-K1 MITTEL: T141 rot "BuffSentinelOptions überdeckt Guide (LevelPilot)" – Optionsfenster muss dem LevelPilot-Fenster ausweichen
   wie den anderen (UICheck/BS.UI_FOREIGN_HUD, Platzierung der Optionen). Danach T141 und T162 grün belegen.
2. BS-L1 MITTEL: T266 Kontrast < 4,5:1 – Hinweistexte "Rechtsklick auf de…" 4,37:1, Platzhalter Suchfeld 4,32:1 (Seiten skill/proc/buff
   u. a.). Farben heller (GameFontDisableSmall 0.5 grau -> heller), bis alle >= 4,5:1; im Nachbau prüfbar machen falls möglich.
3. BS-P1 NIEDRIG: längste eigene Rechenzeit 27,5 ms (T156), Ziel <= 5 ms; Schritte > 16 ms: T25 285, T92 127, T27 108, T259 36, T18 28,
   T156 26, T179 24, T48 23. Je Fall Ursache belegen, Spielbetrieb ja/nein im Bericht, was im Spiel vorkommt in Portionen teilen.
4. T149 (leere Anker, PC zu Hause): Lauf auf dem PC zu Hause mit 0.9.61 abwarten – Zeile zeigt je Anker Grösse/Ankerpunkte/Skalierung;
   dann Ursache belegen und beheben (Test für genau diese Lage, TU1).
5. T249: Zeilenzahl der Prüfliste im Spiel messen (GetNumLines) statt Annahme 95 Zeichen/Zeile (Schätzen verboten).
6. Danach alte Punkte: Prüfliste von Hand (JAEGER, ENTZ, OPT …), T247 Händler (läuft von selbst), T258 Messung.

## Offen beim Nutzer
- Lesezugriff auf das private Daten-Repo goldsentinel-daten wurde dieser Sitzung am 23.11. verweigert (Desktop-Stand für T149).
  Frage an den Nutzer gestellt, keine Antwort.
- Ingametest auf dem PC zu Hause mit 0.9.61 (für T149).

## Entscheide des Nutzers seit letztem Stand
- 23.11. 11:36: in announce/ nie etwas löschen; 12:03: alte gelöschte Ankündigungen nicht wiederherstellen, keine alte Version posten.
  Umgesetzt: Skript pub.sh ersetzt nur download/, bricht bei vorgemerkter Löschung in announce/ ab.
- 23.11. 08:13: Stand je Sitzung in dieser Datei; 07:50: Nutzung sparen ohne Qualitätsverlust.
- 24.11. 06:42: Stand vor dem Zusammenfassen ganz neu sichern (diese Datei).

## Wichtig zu wissen
- Quelle: /home/claude/BuffSentinel (kein Git). Veröffentlichen mit Skripten im Arbeitsordner der Sitzung (scratchpad):
  rel.sh <alt> <neu> <msg> (baut, Offline 8 Läufe, addon_check, pub.sh), rep.sh <thema> <msg> < Text (Bericht + Push);
  Eingaben en.md/de.md/ann.md. Fehlt der Arbeitsordner: Skripte neu schreiben – announce/ NIE löschen.
- Locales aus Generator (scratchpad/loc: keys/manual/extra.json, genloc.py; extra überschreibt), 1232 Schlüssel je Sprache.
- Offline-Nachbau: berichte/BuffSentinel/offline/run_offline.lua (+ mock_wow.lua mit Settings-API); erwartet rot: T13 T23 T28 T45 T51
  T95 T266. Lauf: BS_ROOT=/home/claude/BuffSentinel BS_FLAVOR=forever|era|tbc|retail BS_LOCALE=deDE|enUS.
- Shared nur unverändert kopieren: Sync 3, Markt v10, Dev v2, Test 2; GoldSentinelTakt nicht genutzt.
- Marktspeicher kann BuffSentinelDB.gsMarkt sein (echte Daten ausserhalb der Sandbox) – T264 sichert/vergleicht/setzt zurück.
- Lua 5.1: nie über pcall hinweg yielden (Sliced statt pcall in Tests). Berichte nur "umgesetzt, zur Prüfung".
