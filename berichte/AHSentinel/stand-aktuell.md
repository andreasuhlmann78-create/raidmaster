# Stand AHSentinel (Projekt-Sitzung)

## Stand 25.11.2026 06:39 · Version 0.65.395 (Discord); CurseForge 0.65.393 (Datei-ID 9799863)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.393: 341 PASS, 70 FAIL, keine neuen – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- 0.65.395 = AHS-SP1 eingebaut (kompakt, Bedingungen a–c im Nachbau, d = Ingametest). Danach FULL 0.65.395 allein, dann AHS-J1 (messen).

## Nächste Schritte (Supervisor 25.11. 06:25/06:31)
1. FULL 0.65.395 (allein); s313 weiter nennen (zweimal rot = Befund).
2. AHS-J1 MITTEL: Journal-Ring 3000 (D/P/B) – Tage je Art auf PC/Laptop messen, Verlust zwischen Lieferungen?, Kern-Abgleich 28/29/36 Ursache je
   Art, Vorschlag mit Speicherkosten VOR Einbau.
3. AHS-SP2 HOCH: T459 < 10 240 KB ab Scan 2 – (i) Text ohne "p:c", (ii) Bestpreise als Listen, (iii) Nachlauf-Aufgaben einzeln messen; je Bericht.
4. AHS-CF4 NIEDRIG: "What's new" der CurseForge-Beschreibung (zeigt 0.65.165) mit dem nächsten Upload. CF1-UI-a1 nach T1016 im Spiel. UMG1 danach.

## Offen beim Nutzer
- Ingametest mit 0.65.393 ("testroutine alles"): T1016, T750, Vollscan zweimal, T126 im Vordergrund.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- 25.11. 06:31 Markt-Tabelle Stand 16.11. behalten (Fallzahl-Regel gilt).
- 22:17/22:23 AHS-CF2: 0.65.393 sofort auf CurseForge, "Wichtiges Update"; T459 (c) und Ingametest bewusst in Kauf genommen.
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
- Letzter Test T1021 (T1011–T1013 = SP1 zwei Sätze, T1019/T1020 = SG6-a/Titel). Vollscan: VS.cmp/cmpSpare (set.min/qty/auc/lad). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
