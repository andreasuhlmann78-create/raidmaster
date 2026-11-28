# LevelPilot – Stand der Sitzung

## Stand 28.11.2026 05:42 · Version 3.13.32 (veröffentlicht, Discord; Prüfung offen) · download/: 3.13.29

## Gerade in Arbeit
- Nichts angefangen. 3.13.32 = ExactOrder ohne Tabellenflut (T155 −7 %, Route gleich), T401 mit Stellvertretern. Bericht 05:42.

## Nächste Schritte (Reihenfolge, Supervisor 05:33/05:35)
1. HOCH T155: kalte Wegsuchen der Prüfung (CheckFirstPath/Graph:Path, 52 % der Neuplanung; Danger:Segment 166k Aufrufe) – Datei:Zeile belegen,
   senken ohne Routenänderung (Gegenprobe r3 Route 1–60). Ziel Spiel < 16 ms (Nachbau < ~8,6).
2. HOCH T261 kalt: erstes Einloggen nach Versionswechsel im Spiel (3.13.32) messen; replan 9 Starts in 60 s erklären (Auslöser zählen).
3. Startwegnetz (Entscheid Nutzer 05:35 "Erst Haralds Zonen dazu"): Zonen von B (Schlingendorntal, Arathi, Flusslande 2548 …) ins Werkzeug
   (Grössen messen/belegen), Route 1–60 ALT/NEU wieder messen, dann EINE Version. Bis dahin nichts am Startwegnetz veröffentlichen.
4. MITTEL Grundregeln 80 ms (Übergang Reisen->Grundregeln), Nachbau 43,5 ms. NIEDRIG LP-UI-AC1 (Befehlsliste). NIEDRIG Graph.lua:1048.
5. LP-DL1 nach Annahme mit Ingametest ohne offenes HOCH. "Wo war ich?" offen. W3D (HOCH) wartet auf GSWegMess.

## Offen beim Nutzer
- Ingametest 3.13.32: ERSTES Einloggen nach dem Einspielen (kalt) 60 s warten, dann /lp testroutine alles, danach /reload.
- Frage: "Wo war ich?" beim Einloggen – bleiben oder ab Werk aus?

## Entscheide des Nutzers seit letztem Stand
- 28.11. 05:35: Startwegnetz erst mit Haralds Zonen (B), dann Route ALT/NEU, dann eine Version.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/<Rechner>/forever/konto-5cb3d536/LevelPilot.lua.gz (PC DESKTOP-NVITMSE, Laptop AUSPLUSLAPTOP).
  3.13.31 PC: /home/claude/lpdaten-2811a. Nachbau damit: m2e.sh. Route 1–60: r3.lua MAXL=60 (Bedingungen im Bericht 05:23).
- Messkopien: lpdbg5 (Zeit je Funktion auf Reisen), lpdbg6 (Stichprobe Planung, nur äussere Coroutine – brauchbar), lpdbg7 verworfen.
- Einlog-Messung: "×" = Portionen; "Starts je Auftrag" = Läufe. Im Nachbau laufen Aufträge am Stück (Jobs.sync).
- Wegdaten: seed_bauen.py zählt nur src "selbst", keine Doppelten; Probebau seedprobe2/Wege.lua (9 Zonen).
