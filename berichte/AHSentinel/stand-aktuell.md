# Stand AHSentinel (Projekt-Sitzung)

## Stand 25.11.2026 09:48 · Version 0.65.397 (Discord); CurseForge 0.65.393 (Datei-ID 9799863)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.397: 349 PASS, 67 FAIL (neu nur s313, Streuung) – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- 0.65.397 vom Supervisor angenommen (09:22). FULL 0.65.397: 349/67, neu rot nur s313 (Bericht 0945) – streut 8–20 ms auch mit 0.65.396,
  höchster Schritt meist "names bis Names.lua:228"; Verdacht GC-Schritte, zu messen. CurseForge erst nach Klärung s313.
- Doppelte RecordPrice: belegt harmlos (VerifyPrice parallel, 2-Minuten-Sperre in RecordPrice).
- SP2 (iii) gemessen (Bericht 0948): forecast-eval Decode 2 274 KB, BroadcastScan 2 711 KB, MeasuredRate 1 280, D:Prior 1 160, Marktwert-
  Speicher 2 625 einmal je Scan. Vorschläge a) Decode wiederverwenden, c) MeasuredRate, d) Prior teilen, b) Sync-Liste. Beginne a) mit Gleichheitstest.
  Scratch: /tmp/claude-0/sim2 (zz_sp3 Messung, zz_t459real), alte Version /tmp/claude-0/ahs396.

## Nächste Schritte (Supervisor 25.11. 08:51/09:08)
1. s313/names: GC je Portion messen (Befund, Bericht 0945).
2. AHS-SP2 (iii) HOCH: Nachlauf je Aufgabe messen (forecast-eval, learn:factor, cache:itemlist, core:realcheck, BroadcastScan-Liste {id,p,q},
   suspicious-Liste) – Ziel T459 < 10 240 KB ab Scan 2. Erst messen + Bericht, dann bauen.
3. Doppelte RecordPrice (Nebenbefund) messen. CF1-UI-a1 nach T1016. UMG1 danach. TB138-2 Gold-Lücke 3,2 % bleibt im Masterplan.
4. CF4/CF5 ERLEDIGT (Supervisor 08:51).

## Offen beim Nutzer
- Ingametest: "testroutine alles" mit T1016 (AH offen), Vollscan zweimal (SP1 d / SP2 T459), T126 im Vordergrund. Teil auto 09:01 erledigt.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (Supervisor 09:22: 0.65.397 angenommen; Zeit nur aus TZ=Europe/Zurich date. 08:51: SP2 ii Reihenfolge Tests -> Einbau, Zusatz T-e; 09:08: T750-Ansichten mit Spielzustand nicht als FEHLER).
- 25.11. 07:56 AHS-CF5: CurseForge-Lizenz GPL-3.0; 06:54 AHS-CF4 Beschreibung (beide erledigt).
- 24.11. 21:44 Discord vor Ende von FULL erlaubt; FULL ohne neue Fehler Pflicht vor CurseForge. Supervisor 21:38: NUR DEUTSCH an den Nutzer.

## Wichtig zu wissen
- Wächter-Prüfziele "w:<id>" stehen nur in Sn.extra; Sn:GetTargets() ohne sie, GetTargets(true) mit (nur GetActiveTargets).
  FinishSearch: watch-Ergebnis -> nur W:OnVerified, Sn.result/hasPlan zurück auf vorher. Buy/Reserve sperren t.watch. W:Adopt -> SetTarget.
- Kopfzeile "Sniper: an/aus" = db.sniper.armed (Sn:IsArmed ist auch mit Wächter-Prüfziel wahr – treibt nur die Suche).
- AH-Abdeckung: UI:AHOverlayRaise einmal beim Einrichten; UI:AHBleed misst (T1016). Ursache a) noch "Verdacht, zu messen".
- T750-Regel: Zeilen ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- Letzter Test T1024 (T1023/T1024 = SP2 ii; T1022 = SP2 i). best: A.NewBest/BestGet/BestIDs/BestMarkU (alt+neu); VS:BestSpare/BestInUse. Vollscan: VS.cmp/cmpSpare (set.min/qty/auc/lad). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
