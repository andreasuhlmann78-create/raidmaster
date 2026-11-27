# Stand GuildSentinel – 27.11.2026 18:20 · Version 0.9.66 (Discord, angenommen, im Spiel abgenommen 27.11. 11:19); CurseForge 0.9.66 hochgeladen 18:04 (Datei-ID 9850937)

## Gerade in Arbeit
- GS-CF3 umgesetzt, zur Prüfung: Bericht 2026-11-27-1820-curseforge-0.9.66.txt. download/ = nur GuildSentinel-0.9.66.zip
  (md5 1f5a743a9f920e0216cca17aafbae885, gleich wie announce/), 0.9.61 entfernt (Commit b704b3d0).
- Workflows zu b704b3d0: CurseForge-Upload success, Addon-Prüfung success; Discord-Prüfung lief bei 18:20 noch.
  uploaded.json GuildSentinel endet mit 0.9.61, 0.9.66.

## Nächste Schritte (Reihenfolge)
1. Sichtbarkeit von 0.9.66 auf curseforge.com bestätigen (Seite für diese Sitzung gesperrt -> Nutzer/Supervisor).
2. README-Link auf download/GuildSentinel-0.9.66.zip umstellen – zeigt noch auf die entfernte 0.9.61 (Link führt ins Leere).
   Laut Auftrag erst nach Sichtbarkeit; Vorschlag im Bericht: sofort umstellen. Wartet auf Entscheid.
3. Bei jedem "repo": offen-guildsentinel.txt lesen, neue Aufträge umsetzen.
4. Ingametest 0.9.66 (Einladung fremder Gilde -> keine Antwort; "ginv?" -> Antwort+Fragen; Einlog-Zeile; Meine Woche; Testroutine mit
   vorher angeschaltetem Testmodus; Bank-Charakter; SEITE-Zeile im Protokoll).
5. Offen: Entscheid T270 250 statt 500 Mitglieder; FRAGE L5 (reine Gegenstands-Tooltips).

## Offen beim Nutzer
- CurseForge-Seite: ist GuildSentinel 0.9.66 sichtbar? README-Link sofort umstellen?
- Ingametest; bestätigen, ob am 25.11. der Testmodus vor der Routine an war (Ursache GS-R1 nach dem Ende).
- GS-TAINT1: Knopf "Ränge im Spiel bearbeiten" drücken, Fehlerliste ansehen.

## Entscheide des Nutzers seit letztem Stand
- 27.11. 13:14: Wecker (geplante Nachricht in dieser Sitzung) auf 18:00 für GS-CF3 – ausgelöst 18:01, ausgeführt.
- 27.11. 11:21: GuildSentinel 0.9.66 heute 18:00 auf CurseForge; "Marktdaten teilen" bleibt unter "Daten & Abgleich".

## Wichtig zu wissen
- 0.9.66: Rc:Classify (invite/apply/maybe), Rc.INVITE/APPLY/YOURS, Rc.HasWord/Lower, Rc:CleanInvites (ns:Listen GS_GUILD!),
  ns.LoginLine, ns.HintOnce (settings.hintSeen), ns.errorLineShown. TestRoutine flüstert "darf ich eurer gilde beitreten?".
- 0.9.65: GuildSentinelDB.myweekFixT, Meine Woche "Stand vom …". 0.9.64: ns.RosterEntry, ns.CharKey, T321, T118 mit Roster:Scan.
- Offline: test/run_alle.sh 283 Läufe, 21 946 Einzelprüfungen; Gegenproben 0.9.63 (f192579) und 0.9.65 (c30a398) aus git.
- addon_check mit Syntaxprüfung: PATH=/home/claude/guildsentinel/tools:$PATH (luac5.1-Wrapper, braucht /home/claude/lua51;
  NICHT über Symlink aufrufen – dann besteht er den Probetest nicht). lua51 bauen: tools/lua51src, make linux, cp lua /home/claude/lua51.
- Testdateien NIE überschreiben: vor Write prüfen, ob es die Datei gibt.
- GS-Repo umgezogen: github.com/andreasuhlmann78-create/GuildSentinel (Push geht noch über die Weiterleitung).
- Veröffentlichen: cmp shared/ (7 Dateien), GS commit+push, Zip (zip -r GuildSentinel), addon_check (kein FEHLER, Zeile "luac5.1"),
  announce/guildsentinel__guildsentinel-<V>.md + .GuildSentinel.zip DAZULEGEN (nichts löschen), Bericht, stand-aktuell.md, push,
  git show origin/main prüfen, Zip dem Nutzer schicken.
- CurseForge: Zip nach download/ nur mit OK des Nutzers bzw. 18:00 nach Annahme (DL-ABN); README-Link nach Sichtbarkeit.
