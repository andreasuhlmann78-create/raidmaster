# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 22:00 · Version 3.13.30 (veröffentlicht, Discord; Messversion) · download/: 3.13.29 (angenommen)

## Gerade in Arbeit
- Nichts angefangen. 3.13.30 = Messung je Abschnitt im Protokolltext (Feld protokollTeile). Bericht 22:00 mit Auswertung Speicher 3.13.29
  und Wegdaten Rechner B (Bestand, Doppelte, Probebau Startwegnetz). LP-DL1 3.13.29 erledigt (Bericht 21:54, Addon-Prüfung grün).

## Nächste Schritte (Reihenfolge)
1. Wegdaten B / Startwegnetz (Entscheid 21:47): Probebau (Scratchpad seedprobe/Wege.lua) im Nachbau messen – Route (T381, L1–17), T261,
   Speicher; dann eigene Version mit Bericht. Danach weitere Zonen (Grössen messen; Flusslande 2548 Forever-Zone). Städte mit Ebenen aus (W3D).
2. MITTEL Speicher/T136: Feld protokollTeile aus dem Ingametest 3.13.30 -> welcher Abschnitt im Spiel ~4 MB / 25–35 ms; dann beheben.
3. MITTEL T155 16,89 ms je Planung (Ziel < 16), längste 63 ms (Zone 1458).
4. LP-DL1 künftig nach jeder Annahme mit Ingametest ohne offenes HOCH.
5. Entscheid "Wo war ich?" beim Einloggen (Frage ST1-Bericht Punkt 4).
6. LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte; W3D (HOCH, wartet auf Messung GSWegMess).

## Offen beim Nutzer
- Ingametest 3.13.30 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?

## Entscheide des Nutzers seit letztem Stand
- 27.11. 21:47: "die Addons sollen alles Nützliche verwenden" – Wegdaten Rechner B nutzen, nichts doppelt zählen.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz (Bericht: lupa,
  gsTest.reports, GSTEST1, Bereich "alle"). 3.13.29: /home/claude/lpdaten-2711f. Rechner B: /home/claude/lpdaten-b (Zweig nachlieferung-rechner-b-2026-11-27).
- Wegdaten: alle Pakete in testberichte/wege/LevelPilot/ (B = Version 3.12.31). Werkzeug seed_bauen.py zählt jetzt nur src "selbst", keine Doppelten.
- Nachbau mit Daten 12:35: m2d.sh (T261 dort FEHLER = Daten). Berichtsfelder als Text werden nach ~300 Zeichen gekürzt -> Listen.
- In der Routine ist Jobs.sync an: Hintergrund-Aufträge rechnen dort sofort – in pcall-Prüfungen ohne Abgabe.
