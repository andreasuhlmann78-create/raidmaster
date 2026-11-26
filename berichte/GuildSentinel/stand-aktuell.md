# Stand GuildSentinel – 26.11.2026 10:07 · Version 0.9.64 (Discord); CurseForge 0.9.61

## Gerade in Arbeit
- Nichts. 0.9.64 auf Discord, Bericht 2026-11-26-1006-version-0.9.64-r1-realm-t4-g4a.txt.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.64 abwarten, dabei offen-guildsentinel.txt bei jedem "repo" lesen.
2. Ingametest 0.9.64 (siehe Bericht: Testroutine mit vorher angeschaltetem Testmodus, Meine Woche, Bank-Charakter, SEITE-Zeile).
3. Danach CurseForge 0.9.64 nur mit OK des Nutzers (0.9.63 durfte wegen GS-R1 nicht hinaus).
4. Offen: Entscheid T270 mit 250 statt 500 Mitgliedern (Portionen "nach T269" 18–23 ms); FRAGE L5 (reine Gegenstands-Tooltips).

## Offen beim Nutzer
- Ingametest 0.9.64; bestätigen, ob am 25.11. der Testmodus vor der Routine an war (Ursache GS-R1 nach dem Ende).
- GS-TAINT1: Knopf "Ränge im Spiel bearbeiten" im Spiel drücken, Fehlerliste ansehen.

## Entscheide des Nutzers seit letztem Stand
- 25.11. 11:09: Spieler auf CurseForge bekommen immer eine Antwort – im Bericht Zeile "Rückmeldung erledigt: …" je behobener Meldung.
- Supervisor: G-4a im Spiel ohne "LANGSAM Seite members" -> ERLEDIGT (Beleg-Zähler jetzt im Protokoll).

## Wichtig zu wissen
- 0.9.64: ns.RosterEntry (nur Tabellen), Roster:Compare übergeht beschädigte Einträge, RestoreState Testmodus neu an, T321, T118 mit
  Roster:Scan, ns.CharKey (Realm leer seit ~21.11. dauerhaft: vorhandener "Realm|Name"), UI.selStats/SelStatLine (G-4a), GoldSentinelTest 4.
- 0.9.63: UmgSuspect nur Hintergrund/Laden/Bereinigung, AddonMem nach Bereinigung, T320 (kein Blizzard-Fenster).
- Offline: test/run_alle.sh 271 Läufe, 21 703 Einzelprüfungen; Gegenproben gegen 0.9.63 aus git (_alt063, wird gelöscht).
- Testdateien NIE überschreiben: vor Write prüfen, ob es die Datei gibt (26.11. run_realm.lua versehentlich überschrieben, wiederhergestellt).
- Veröffentlichen (falls Skript im Arbeitsordner verloren): cmp shared/ (7 Dateien), Zip, GS-Repo push, addon_check (kein FEHLER,
  Zeile "luac5.1"), announce/<…>.md + .GuildSentinel.zip DAZULEGEN (nichts löschen), Bericht, stand-aktuell.md, push, origin/main prüfen.
- CurseForge: Zip nach download/ nur mit OK; alte Zip aus download/ entfernen und README-Link umstellen erst, wenn neue sichtbar ist.
