# Stand GuildSentinel – 24.11.2026 20:34 · Version 0.9.62 (Discord); CurseForge 0.9.61 hochgeladen, Freigabe ausstehend

## Gerade in Arbeit
- Nichts. 0.9.62 (GS-UMG1) auf Discord, Bericht 2026-11-24-2033-version-0.9.62-umg1-umgebung-bedienung.txt.
- GS-CF2: 0.9.61 nach download/ (Commit 693927ee), Workflow grün, Datei-ID 9797187, uploaded.json mit 0.9.61. Auf curseforge.com noch
  nicht sichtbar (Freigabe durch CurseForge, Verdacht). Supervisor 20:27: angenommen, ERLEDIGT erst wenn sichtbar.

## Nächste Schritte (Reihenfolge)
1. Sobald 0.9.61 auf curseforge.com sichtbar: download/GuildSentinel-0.9.39.zip entfernen, README-Link auf 0.9.61 (Antwort Supervisor
   20:27). Lehnt CurseForge ab: alte Zip bleibt. announce/ nie anfassen.
2. Prüfung 0.9.62 abwarten, dabei offen-guildsentinel.txt bei jedem "repo" lesen.
3. Antworten: FRAGE L5 (reine Gegenstands-Tooltips in T317 nicht gewertet), FRAGE UMG1 c) (Speicher je Addon am Ende statt beim
   längsten Bild).
4. Hinweis Supervisor (Ingametest 0.9.61): 6 Portionen über 16 ms (T269, T295g ×3, T09) – beim nächsten Mal kleiner schneiden, kein Auftrag.

## Offen beim Nutzer
- Ingametest 0.9.62 (Testroutine normal und einmal mit Alt-Tab).
- G-4a gilt erst als erledigt, wenn im /gs protokoll keine "LANGSAM Seite members" > 16 ms mehr kommt.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 20:14: 0.9.61 sofort auf CurseForge (Ausnahme von 18:00) – umgesetzt.
- 24.11. 20:04: Umgebung/Bedienung in alle Testroutinen (ausser TS) – GS-UMG1 umgesetzt in 0.9.62.
- Ingametest 0.9.61 (24.11. 12:48): OK 339, FEHLER 0 – GS-K1/K2/L1/L5/P1 erledigt.

## Wichtig zu wissen
- 0.9.62: R.UmgStart/UmgStep/UmgJudge/UmgLines/AddonMem (TestRoutine.lua), Wächter "GuildSentinelUmgFrame"; Leistungsprüfungen R.PERF
  (T138–T144, T307e) -> HINWEIS bei Störung von aussen (Status nur in TestRoutine, GoldSentinelTest unverändert).
- 0.9.61: Ausweichen (UI:AvoidOthers), Gp:FitNote, ns.ClassHex hellt Schamane auf, UI.ItemTip, Activity:Grid ohne Tabellen.
- Offline: test/run_alle.sh 256 Läufe, 21 494 Einzelprüfungen (RO=1 Abgleich Lauf für Lauf).
- Veröffentlichen (falls Skript im Arbeitsordner verloren): cmp shared/ (7 Dateien), Zip, GS-Repo push, addon_check (kein FEHLER,
  Zeile "luac5.1"), announce/<…>.md + .GuildSentinel.zip DAZULEGEN (nichts löschen), Bericht, stand-aktuell.md, push, origin/main prüfen.
- CurseForge: Zip nach download/ nur mit OK; Workflow curseforge.yml lädt hoch; uploaded.json prüfen; Sichtbarkeit auf curseforge.com.
