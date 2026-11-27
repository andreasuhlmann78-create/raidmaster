# Stand GuildSentinel – 27.11.2026 10:04 · Version 0.9.66 (Discord); CurseForge 0.9.61

## Gerade in Arbeit
- Nichts. 0.9.66 auf Discord (GS-REK1 + ST1), Bericht 2026-11-27-1003-version-0.9.66-rek1-st1.txt.
- 0.9.64 und 0.9.65 vom Supervisor angenommen, Abnahme im Spiel offen.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.66 abwarten, dabei offen-guildsentinel.txt bei jedem "repo" lesen.
2. Ingametest 0.9.66 (Einladung fremder Gilde -> keine Antwort; "ginv?" -> Antwort+Fragen; Einlog-Zeile; Meine Woche; Testroutine mit
   vorher angeschaltetem Testmodus; Bank-Charakter; SEITE-Zeile im Protokoll).
3. Danach CurseForge 0.9.66 nur mit OK des Nutzers.
4. Offen: Entscheid T270 250 statt 500 Mitglieder; FRAGE L5 (reine Gegenstands-Tooltips); FRAGE ST1 "Marktdaten teilen" nach "Mithelfen"?

## Offen beim Nutzer
- Ingametest; bestätigen, ob am 25.11. der Testmodus vor der Routine an war (Ursache GS-R1 nach dem Ende).
- GS-TAINT1: Knopf "Ränge im Spiel bearbeiten" drücken, Fehlerliste ansehen.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 08:27–09:23 ST1 Spieler-Texte (Einlog-Zeile mit Version, Mithelfen, Fehler 1×, Messwerte nur im Protokoll, Tipps einmal;
  nur ausserhalb des Testmodus) – umgesetzt in 0.9.66.
- 27.11. 08:49: Texte der Antwort und Bewerbungsfragen "so lassen"; Einladungen fremder Gilden nie beantworten (GS-REK1).

## Wichtig zu wissen
- 0.9.66: Rc:Classify (invite/apply/maybe), Rc.INVITE/APPLY/YOURS, Rc.HasWord/Lower, Rc:CleanInvites (ns:Listen GS_GUILD!),
  ns.LoginLine, ns.HintOnce (settings.hintSeen), ns.errorLineShown. TestRoutine flüstert "darf ich eurer gilde beitreten?".
- 0.9.65: GuildSentinelDB.myweekFixT, Meine Woche "Stand vom …". 0.9.64: ns.RosterEntry, ns.CharKey, T321, T118 mit Roster:Scan.
- Offline: test/run_alle.sh 283 Läufe, 21 946 Einzelprüfungen; Gegenproben 0.9.63 (f192579) und 0.9.65 (c30a398) aus git.
- Arbeitsordner wurde am 27.11. ersetzt: lua51 aus tools/lua51src bauen (make linux, cp lua /home/claude/lua51); Veröffentlichungs-Skript
  weg – Schritte von Hand (unten). Testdateien NIE überschreiben: vor Write prüfen, ob es die Datei gibt.
- GS-Repo umgezogen: github.com/andreasuhlmann78-create/GuildSentinel (Push geht noch über die Weiterleitung).
- Veröffentlichen: cmp shared/ (7 Dateien), GS commit+push, Zip (zip -r GuildSentinel), addon_check (kein FEHLER, Zeile "luac5.1"),
  announce/guildsentinel__guildsentinel-<V>.md + .GuildSentinel.zip DAZULEGEN (nichts löschen), Bericht, stand-aktuell.md, push,
  git show origin/main prüfen, Zip dem Nutzer schicken.
- CurseForge: Zip nach download/ nur mit OK; alte Zip aus download/ entfernen und README-Link umstellen erst, wenn neue sichtbar ist.
