# Stand GuildSentinel – 24.11.2026 11:05 · Version 0.9.61 (Discord; CurseForge erst nach Ingametest)

## Gerade in Arbeit
- Nichts. 0.9.61 veröffentlicht (Discord), Bericht berichte/GuildSentinel/2026-11-24-1100-version-0.9.61-ausweichen-kontrast-l5-leistung-shv3.txt.

## Nächste Schritte (Reihenfolge)
1. Auf Prüfung des Supervisors warten – dabei weiterarbeiten: offen-guildsentinel.txt bei jedem "repo" lesen.
2. Antwort auf FRAGE L5 (reine Gegenstands-Tooltips des Spiels in T317 nicht gewertet – richtig?). Ändern = eine Zeile in T317.
3. Ingametest 0.9.61 durch den Nutzer: T183 (LevelPilot offen), T319, T311, T317, neue Zeile "längste Portionen (Ort, Speicher)" ->
   Ursachen GS-P1 im Spiel belegen (Speicherbereinigung ja/nein, "in Txx"/"nach Txx").
4. Danach CurseForge (nur mit OK des Nutzers), RP/RV im Client bestätigen (Nutzer), CH-G (später, nach AHSentinel).

## Offen beim Nutzer
- Ingametest 0.9.61 (Schrift bei 99,4 % wegen Ausweichen ansehen; andere Auflösung/UI-Grösse).
- G-4a gilt erst als erledigt, wenn im /gs protokoll keine "LANGSAM Seite members" > 16 ms mehr kommt.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (Supervisor 24.11. 07:20: SH-V3 GoldSentinelTest 3 – umgesetzt in 0.9.61).

## Wichtig zu wissen
- 0.9.61: UI:AvoidOthers (Ausweichen, Massstab min. 95 %, framePoint bleibt), Gp:FitNote, ns.ClassHex hellt zu dunkle Klassenfarben
  auf (nur Schamane 0070dd -> 3d92e5), UI.ItemTip (Hauptzahl Zeile 1; ohne Zahl = UI.tipPureItem), Activity:Grid ohne Tabellen,
  Testroutine: R.Where/R.NotePortion/R.SlowLine, T21/T22 in Portionen, BankCases über T.PCall, SH-NIL in eigener Check-Hülle
  (SKIP nur genau "return nil, Grund").
- Offline: test/run_alle.sh 253 Läufe, 21 386 Einzelprüfungen (RO=1 Abgleich Lauf für Lauf). Neue Läufe: run_ausweichen, run_klassen,
  run_l5, run_grid; Testroutine mit GEOM_W/GEOM_H=1365/768, LP=1 (LevelPilot geladen+offen), KLASSEN=1, AVOIDOFF=1 (Gegenprobe K1).
- Veröffentlichen (Skript im Arbeitsordner kann beim Zusammenfassen verloren gehen): cmp shared/ (7 Dateien), Zip bauen, GS-Repo
  committen+pushen, addon_check (kein FEHLER, Zeile "luac5.1"), announce/guildsentinel__guildsentinel-<V>.md + .GuildSentinel.zip
  DAZULEGEN (nichts löschen, Entscheid 23.11. 11:36), Bericht, stand-aktuell.md, push, Ankunft mit git show origin/main prüfen.
- Gildenschlüssel "@Fraktion|Gilde"; alte Daten in guildsOld. RaidReady: < 3 Spieler oder < 7 Tage -> keine Wochenzahl.
- Locales: tools/loc/new/v0XXX.py + tools/en7.py + python3 tools/en.py + tools/loc/check.py <loc>; Beschriftungen <= 28 Zeichen.
