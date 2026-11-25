# Stand AHSentinel (Projekt-Sitzung)

## Stand 25.11.2026 13:55 · Version 0.65.399 (Discord); CurseForge 0.65.393 (Datei-ID 9799863)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.398: 353 PASS, 66 FAIL, keine neuen – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- 0.65.399 (AHS-OVF1: A.SafeFormat + "local string = A.SafeString" in 65 Dateien; T000 mit Stelle; TSK1h Scan-Nummer) auf Discord.
  Nachbau wirft jetzt wie WoW bei %d > 2^31 (wowsim.lua). FULL 0.65.399 allein als Nächstes (neue Funde möglich).
- T14 belegt (Item 274964, Verlauf ohne Vollscan-Einträge 14 Tage, gemessener Absatz 1972/Tag) – Fix nach Messung "warum keine Einträge".
- Scratch: /tmp/claude-0/sim2 (zz_ovf, zz_t14b mit NOW/FACTION/SVIN=/tmp/claude-0/ig/laptop_1330.lua), alte Versionen ahs396/397.

## Nächste Schritte (Supervisor 25.11. 13:06/13:26, 10:59)
1. FULL 0.65.399 allein, Bericht (Funde der WoW-Nachbildung einordnen).
2. AHS-T14 MITTEL: warum Item 274964 keine Vollscan-Preise bekommt; dann Fix (Absatz ohne Angebotsdaten nicht verwenden/deckeln).
3. AHS-T750 NIEDRIG: 1 Befund "abgeschnitten" – Ansicht finden.
4. SP2 h) (rein intern) -> AHS-S313 (Bereinigung + Namen-Aufbau < 6 ms ohne GC) -> k) falls nötig.
5. CurseForge: keine Version, bis OVF1 im Spiel bestätigt (Supervisor). Rückmeldung CF3 im Bericht 0.65.399.

## Offen beim Nutzer
- Ingametest: "testroutine alles" mit T1016 (AH offen), Vollscan zweimal (SP1 d / SP2 T459), T126 im Vordergrund. Teil auto 09:01 erledigt.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- Nutzer 11:09: jeder CurseForge-Kommentar bekommt eine Antwort -> im Bericht "Rückmeldung erledigt: …". Supervisor 13:06: 0.65.398 nicht auf CurseForge; 10:59: h zuerst, k freigegeben unter Bedingungen, S313 Regel. (Supervisor 10:00: SP2 iii Reihenfolge a,c,d,b + AHS-S313; 09:22: 0.65.397 angenommen; Zeit nur aus TZ=Europe/Zurich date. 08:51: SP2 ii Reihenfolge Tests -> Einbau, Zusatz T-e; 09:08: T750-Ansichten mit Spielzustand nicht als FEHLER).
- 25.11. 07:56 AHS-CF5: CurseForge-Lizenz GPL-3.0; 06:54 AHS-CF4 Beschreibung (beide erledigt).
- 24.11. 21:44 Discord vor Ende von FULL erlaubt; FULL ohne neue Fehler Pflicht vor CurseForge. Supervisor 21:38: NUR DEUTSCH an den Nutzer.

## Wichtig zu wissen
- Wächter-Prüfziele "w:<id>" stehen nur in Sn.extra; Sn:GetTargets() ohne sie, GetTargets(true) mit (nur GetActiveTargets).
  FinishSearch: watch-Ergebnis -> nur W:OnVerified, Sn.result/hasPlan zurück auf vorher. Buy/Reserve sperren t.watch. W:Adopt -> SetTarget.
- Kopfzeile "Sniper: an/aus" = db.sniper.armed (Sn:IsArmed ist auch mit Wächter-Prüfziel wahr – treibt nur die Suche).
- AH-Abdeckung: UI:AHOverlayRaise einmal beim Einrichten; UI:AHBleed misst (T1016). Ursache a) noch "Verdacht, zu messen".
- T750-Regel: Zeilen ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- Letzter Test T1027 (T1025–T1027 = SP2 iii a/c/b; T1023/T1024 = SP2 ii; T1022 = SP2 i). best: A.NewBest/BestGet/BestIDs/BestMarkU (alt+neu); VS:BestSpare/BestInUse. Vollscan: VS.cmp/cmpSpare (set.min/qty/auc/lad). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
