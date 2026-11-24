# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 21:59 · Version 0.65.393 (Discord; Kandidat für CurseForge – NICHT dort, wartet auf Ingametest + OK des Nutzers)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.393: 341 PASS, 70 FAIL, keine neuen – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- nichts. FULL 0.65.393 fertig: keine neuen Fehler (Bericht 2026-11-24-2157-0.65.393-full.txt). 0.65.393 veröffentlicht: CF1-UI a/c/d, SG6, TR1-a, T750-Titel. Bericht 2026-11-24-2152-0.65.393-cf1ui-sg6-tr1a.txt.

## Nächste Schritte (AHS-CF1, Entscheid des Nutzers 19:19/19:21)
0. 0.65.394: AHS-SG6-a (Reiter Wächter 1 Neuaufbau je Runde, Ursache messen), T750-Titel: zu lange Namen kürzen + voller Name im Tooltip.
1. Ingametest 0.65.393 auswerten (Daten-Repo; PC = aktuell/DESKTOP-NVITMSE/forever/…): T1016 (Rahmen über der Abdeckung, AH offen), T750.
2. CurseForge erst, wenn Supervisor a–e geprüft UND der Nutzer im Spiel freigibt; dann Zip um 18:00 nach download/ (T459-Ausnahme nur 1×).
3. DANACH AHS-SP1 (HOCH, Entscheid 19:56): Speicher-Lösung Vollscan – Zahlen-Listen min/qty/auc, Stufen als Text (EncodeLadder-Format).
   Messen im Nachbau mit echten Daten, Gleichheitstest aller Leser, Bericht VOR Einbau, Freigabe Supervisor, dann Einbau.
4. Danach V4-Messung, G14-a, AHS-UMG1 (NIEDRIG; Klarstellung 20:50: "Rest grösser als eigene Arbeit" allein kein HINWEIS-Grund).

## Offen beim Nutzer
- Ingametest mit 0.65.393 ("testroutine alles") und eigene Durchsicht im Spiel (CF1 e) – ohne sein OK keine CurseForge-Veröffentlichung.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- 20:43 AHS-CF1-UI c: Wächter-Funde erscheinen nie von selbst im Sniper; nur nach Auswahl beim Item.
- 20:48 AHS-CF1-UI c: Rechtsklick "In den Sniper übernehmen"; Wächter-Kaufweg (Knopf, eigene Taste, gemeinsame Taste) kauft keine Funde.
- 21:07–21:13 AHS-SG6 Leuchten+Ton im Suchtakt, Wächter eigene Farbe (vor CurseForge). 21:25/21:27 AHS-TR1-a nur Testschritt, kein Blocker.
- 21:44 Discord vor Ende von FULL erlaubt (auto, server, geänderte Szenarien, addon_check grün); FULL ohne neue Fehler Pflicht vor CurseForge.
- Supervisor 21:38: NUR DEUTSCH an den Nutzer. 21:42: Schrift nie unter GameFontNormalSmall (L8).
- 20:17 (über Supervisor): Wächter-Schritt bleibt so, WAECHTER-LAST/-FUND bleiben im Schritttext (Antwort c).

## Wichtig zu wissen
- Wächter-Prüfziele "w:<id>" stehen nur in Sn.extra; Sn:GetTargets() ohne sie, GetTargets(true) mit (nur GetActiveTargets).
  FinishSearch: watch-Ergebnis -> nur W:OnVerified, Sn.result/hasPlan zurück auf vorher. Buy/Reserve sperren t.watch. W:Adopt -> SetTarget.
- Kopfzeile "Sniper: an/aus" = db.sniper.armed (Sn:IsArmed ist auch mit Wächter-Prüfziel wahr – treibt nur die Suche).
- AH-Abdeckung: UI:AHOverlayRaise einmal beim Einrichten; UI:AHBleed misst (T1016). Ursache a) noch "Verdacht, zu messen".
- T750-Regel: Zeilen ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- Letzter Test T1018 (T1017/T1018 = SG6). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
