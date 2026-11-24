# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 22:42 · Version 0.65.393 (Discord UND CurseForge seit 24.11. 22:25, Datei-ID 9799863, "Wichtiges Update")
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.393: 341 PASS, 70 FAIL, keine neuen – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- AHS-SP1: Mess-Fassung in der Arbeitskopie (Vollscan.lua VS.COMPACT=false, DigestC/DecodeBody/NewSet, Ladder mit Zwischenspeicher 400,
  Finish/Track/FeedNetRun mit Satz). Bericht "sp1-messung-vor-einbau" abgelegt – WARTET auf Freigabe Supervisor. Nachbau-Szenarien zz_sp1eq,
  zz_t459real (SP1C=0/1, ZC=23520, REAL_SV=/tmp/claude-0/ahs_sv3.lua) in /tmp/claude-0/sim – nach Freigabe ins Repo.
- Bis dahin: AHS-SG6-a (Reiter Wächter 1 Neuaufbau je Runde) und Titel-Tooltip (T750) für 0.65.394.

## Nächste Schritte (AHS-CF1, Entscheid des Nutzers 19:19/19:21)
0. 0.65.394: AHS-SG6-a (Reiter Wächter 1 Neuaufbau je Runde, Ursache messen), T750-Titel: zu lange Namen kürzen + voller Name im Tooltip.
1. Ingametest 0.65.393 auswerten (Daten-Repo; PC = aktuell/DESKTOP-NVITMSE/forever/…): T1016 (Rahmen über der Abdeckung, AH offen), T750.
2. CurseForge: 0.65.393 hochgeladen (AHS-CF2). Künftig wieder 18:00-Regel; Sichtbarkeit auf curseforge.com vom Nutzer prüfen.
3. DANACH AHS-SP1 (HOCH, Entscheid 19:56): Speicher-Lösung Vollscan – Zahlen-Listen min/qty/auc, Stufen als Text (EncodeLadder-Format).
   Messen im Nachbau mit echten Daten, Gleichheitstest aller Leser, Bericht VOR Einbau, Freigabe Supervisor, dann Einbau.
4. Danach V4-Messung, G14-a, AHS-UMG1 (NIEDRIG; Klarstellung 20:50: "Rest grösser als eigene Arbeit" allein kein HINWEIS-Grund).

## Offen beim Nutzer
- Ingametest mit 0.65.393 ("testroutine alles"): T1016, T750, Vollscan zweimal, T126 im Vordergrund.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
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
- Letzter Test T1018 (T1017/T1018 = SG6). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
