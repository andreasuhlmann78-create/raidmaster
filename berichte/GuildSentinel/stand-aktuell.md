# Stand GuildSentinel – 25.11.2026 09:12 · Version 0.9.63 (Discord); CurseForge 0.9.61 (sichtbar)

## Gerade in Arbeit
- Nichts. 0.9.63 auf Discord, Bericht 2026-11-25-0911-version-0.9.63-umg1a-speicher-taint1.txt.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.63 abwarten, dabei offen-guildsentinel.txt bei jedem "repo" lesen.
2. GS-TAINT1: Nutzer prüft im Spiel den Knopf "Ränge im Spiel bearbeiten" (Fehler in Blizzard-Code?). Wenn ja: Knopf durch Anleitung
   ersetzen ("Gildenfenster (Taste J) > Gildenverwaltung", Text vorhanden).
3. Offene Frage L5 (reine Gegenstands-Tooltips in T317 nicht gewertet).
4. CurseForge: nächste Version erst nach Ingametest und OK des Nutzers (download/ hat nur die neueste Zip, zurzeit 0.9.61).

## Offen beim Nutzer
- Ingametest 0.9.63: Zeile "Speicher je Addon … nach Bereinigung", T320, GS-TAINT1-Knopf (siehe oben).
- G-4a gilt erst als erledigt, wenn im /gs protokoll keine "LANGSAM Seite members" > 16 ms mehr kommt.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (Supervisor: UMG1 Klarstellung 24.11. 20:50 – Rest > eigene Arbeit allein kein Grund; Speicher je Addon am Ende richtig).
- Ingametest 0.9.62 (25.11. 08:55): OK 338, FEHLER 0, UMG1 im Spiel belegt (Alt-Tab 6–12 s erkannt).

## Wichtig zu wissen
- 0.9.63: R.UmgSuspect (nur Hintergrund/Laden/Bereinigung), R.AddonMem (Wert nach Bereinigung), R.GuardWindows + T320, T296-Vorlauf
  1 Flüsternachricht je Portion. Portionen "nach T269" = Zellen T270 (500er-Lage, nicht teilbar), "nach T09" = Seitenaufbau (G-4a).
- 0.9.62: Wächter "GuildSentinelUmgFrame", Leistungsprüfungen R.PERF (T138–T144, T307e) -> HINWEIS bei Störung von aussen.
- 0.9.61: Ausweichen (UI:AvoidOthers), Gp:FitNote, ns.ClassHex hellt Schamane auf, UI.ItemTip, Activity:Grid ohne Tabellen.
- Offline: test/run_alle.sh 259 Läufe, 21 573 Einzelprüfungen (RO=1 Abgleich Lauf für Lauf).
- Veröffentlichen (falls Skript im Arbeitsordner verloren): cmp shared/ (7 Dateien), Zip, GS-Repo push, addon_check (kein FEHLER,
  Zeile "luac5.1"), announce/<…>.md + .GuildSentinel.zip DAZULEGEN (nichts löschen), Bericht, stand-aktuell.md, push, origin/main prüfen.
- CurseForge: Zip nach download/ nur mit OK; alte Zip aus download/ entfernen und README-Link umstellen erst, wenn neue sichtbar ist.
