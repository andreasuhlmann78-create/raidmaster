# Stand AHSentinel (Projekt-Sitzung)

## Stand 26.11.2026 13:53 · Version 0.65.410 (Discord, Messzeilen /reload, Öffnen-Teile); CurseForge 0.65.400 (öffentlich, CF6 erledigt 08:01)
Repos: ahanalyzerpro (Code, schreiben; tests/ dort direkt pflegen), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur
 lesen; Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz – Testberichte "GSTEST1{…}", UI-Befunde db.uiFindingsLast).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle (Stunden bei Parallel-Last;
 0.65.403: 355 PASS, 67 FAIL, keine neuen (Bericht 0655) – nie parallel zu FULL rechnen, sonst Zeitüberschreitungen). T126 streut 6–10 ms. Neu: s9_watcher_tip (Wächter-Tipp -> Rechtsklick -> Sniper kauft).
 Eigene Szenarien /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_t459real, zz_tr1, zz_i6_sniper, zz_ui_buy).

## Gerade in Arbeit
- TB1/TB1-b im Spiel BESTANDEN (Supervisor 10:32), zweites Laden ohne TB1-B ok. GOLD-LOGOUT: 0 nicht immer -> 0.65.408 schreibt Art des Endes mit.
- AHS-W1 Teil 1 (0.65.409) im Spiel: keine WAECHTER-POLL > 8 ms (kurze Sitzung). Teil 2: 0.65.410 misst die Teile beim Öffnen -> dann Massnahme.
- FULL 409 nicht ganz allein gelaufen (berichtet); FULL 410 allein: 355/67, keine neuen.
- 0.65.407: AHS-W1 Messzeile WAECHTER-POLL (Nachbau: eigene Arbeit im Ereignis ≤0,1 ms) -> Ingame-Messung abwarten, dann a) oder b).
- KEINE CF-Veröffentlichung von 0.65.405/406 bis TB1-b abgenommen (Supervisor 09:35).

## Nächste Schritte
1. (FULL 0.65.406 erledigt: 355/67, keine neuen. AHS-DL1 erledigt: alte 0.65.393.zip weg.)
2. Weitere T459-Posten messen (Leitertexte Verdichtung, cache:today, learn:factor, core:realcheck), je Massnahme mit Messung.
3. AHS-BP1 MITTEL (bindType: gebundene Ware nicht als AH-Ware), AHS-S216, AHS-MK1 (nach Ingametest).
4. Ingametest: Gold (alle Figuren) = Summe Charakterauswahl (60g 49s 77c), Diagnose REALM/TB1-B/GOLD-LOGOUT, T459 zwei Werte, Vollscan zweimal.
5. Regel CF 18:00: CF-Entscheid im Repo -> sofort Auswahl-Frage im Chat; bis 17:30 Stand melden; ohne Bestätigung sofort melden.

## Offen beim Nutzer
- Ingametest: "testroutine alles" mit T1016 (AH offen), Vollscan zweimal (SP1 d / SP2 T459), T126 im Vordergrund. Teil auto 09:01 erledigt.
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- Supervisor 09:35/09:38: TB1-b HOCH (Realm leer seit 21.11., Doppel zusammenführen, Sicherung, Bank-Figur aus books.gold); bis dahin kein CF.
- Supervisor 26.11. 08:26: S313 Grenze Budget + gemessener längster Schritt (≤8); SP2 k) verworfen; weiter T459-Posten, dann S216. 08:57: TB1 HOCH (Nutzer schickte kein Gold an den Priester).
- Supervisor 26.11. 06:30: CF6 erledigt bis auf Sichtbarkeit; Regel CF-Frage sofort/17:30/18:00 sofort melden ANGENOMMEN; 0.65.403 angenommen (Abnahme im Spiel offen).
- 26.11. ~06:15 im Chat: "Ja, 0.65.400 hochladen" (CurseForge).
- Nutzer 11:09: jeder CurseForge-Kommentar bekommt eine Antwort -> im Bericht "Rückmeldung erledigt: …". Supervisor 13:06: 0.65.398 nicht auf CurseForge; 10:59: h zuerst, k freigegeben unter Bedingungen, S313 Regel. (Supervisor 10:00: SP2 iii Reihenfolge a,c,d,b + AHS-S313; 09:22: 0.65.397 angenommen; Zeit nur aus TZ=Europe/Zurich date. 08:51: SP2 ii Reihenfolge Tests -> Einbau, Zusatz T-e; 09:08: T750-Ansichten mit Spielzustand nicht als FEHLER).
- 25.11. 07:56 AHS-CF5: CurseForge-Lizenz GPL-3.0; 06:54 AHS-CF4 Beschreibung (beide erledigt).
- 24.11. 21:44 Discord vor Ende von FULL erlaubt; FULL ohne neue Fehler Pflicht vor CurseForge. Supervisor 21:38: NUR DEUTSCH an den Nutzer.

## Wichtig zu wissen
- Wächter-Prüfziele "w:<id>" stehen nur in Sn.extra; Sn:GetTargets() ohne sie, GetTargets(true) mit (nur GetActiveTargets).
  FinishSearch: watch-Ergebnis -> nur W:OnVerified, Sn.result/hasPlan zurück auf vorher. Buy/Reserve sperren t.watch. W:Adopt -> SetTarget.
- Kopfzeile "Sniper: an/aus" = db.sniper.armed (Sn:IsArmed ist auch mit Wächter-Prüfziel wahr – treibt nur die Suche).
- AH-Abdeckung: UI:AHOverlayRaise einmal beim Einrichten; UI:AHBleed misst (T1016). Ursache a) noch "Verdacht, zu messen".
- T750-Regel: Zeilen ohne " – Grund" nach "Text x px)" sind "gekürzt (Tooltip)" = kein FEHLER.
- s313 = Bewertung je Bild mit GC je Portion (Gegenprobe S313_NB=20). Letzter Test T1032 (T1032 API2-b; T1031 API2; T1030 SB1; T1028 OVF1, T1029 Trend Höchstpreis; T1025–T1027 = SP2 iii a/c/b; T1023/T1024 = SP2 ii; T1022 = SP2 i). best: A.NewBest/BestGet/BestIDs/BestMarkU (alt+neu); VS:BestSpare/BestInUse. Vollscan: VS.cmp/cmpSpare (set.min/qty/auc/lad). Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-CF1-UI", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
