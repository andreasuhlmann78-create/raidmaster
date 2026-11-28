# LevelPilot – Stand der Sitzung

## Stand 28.11.2026 05:23 · Version 3.13.31 (angenommen 04:35, Code; Ingametest offen) · download/: 3.13.29

## Gerade in Arbeit
- Nichts angefangen. Neu: Route 1–60 ALT/NEU mit Startwegnetz aus Wegdaten (Bericht 28.11. 05:23): Konto +14 min (+0,2 %), neuer Spieler
  −3 h 56 (−2,0 %). Nichts veröffentlicht; Entscheid Supervisor/Nutzer, ob NEU als Version.
- Neuer Befund LP-UI-AC1 NIEDRIG (Befehlsliste durchscheinend/abgeschnitten) – erst nach T261.

## Nächste Schritte (Reihenfolge, Supervisor 22:37)
1. HOCH T261: Ingametest 3.13.31 (PC, Krieger) – Zeile "Starts je Auftrag"; reicht es nicht < 1000 ms: replan (504 ms) belegen und senken.
2. LP-ML1: Abnahme im Spiel (protokollTeile MarktLine, Stücke T34/T21/T355/T386).
3. MITTEL T150 (Replan Median 16,91 ms, Ziel < 16) / T155 (16,89 ms je Planung).
4. MITTEL Grundregeln 80 ms im Spiel (Übergang "Reisen svc–Grundregeln"), Nachbau 45,9 ms – Ursache belegen.
5. Wegdaten B / Startwegnetz: Route gemessen (05:23). Falls gewünscht: NEU (Scratchpad seedprobe2/Wege.lua) mit T261/T381 im Nachbau, dann Version;
   grösserer Nutzen: Zonen von B ins Werkzeug (Grössen messen). Danach LP-UI-AC1.
6. LP-DL1 nach jeder Annahme mit Ingametest ohne offenes HOCH. Entscheid "Wo war ich?" offen. W3D (HOCH) wartet auf GSWegMess.

## Offen beim Nutzer
- Ingametest 3.13.31 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?

## Entscheide des Nutzers seit letztem Stand
- 27.11. 22:37 "b ist gut": SH-M1 bleibt gebündelt -> LP-ML1 (Markt-Zeilen merken) freigegeben.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/<Rechner>/forever/konto-5cb3d536/LevelPilot.lua.gz (PC = DESKTOP-NVITMSE, Laptop =
  AUSPLUSLAPTOP). Bericht: lupa, gsTest.reports, GSTEST1, Bereich "alle", Version wählen. 3.13.30 PC: /home/claude/lpdaten-2711g.
- Einlog-Messung: "×" = Portionen; neu "Starts je Auftrag" = Läufe. Im Nachbau laufen Aufträge am Stück (Jobs.sync) – Wiederholungen im Spiel
  sind dort nicht nachstellbar.
- Wegdaten: seed_bauen.py zählt nur src "selbst", keine Doppelten. Berichtsfelder > 300 Zeichen als Liste.
