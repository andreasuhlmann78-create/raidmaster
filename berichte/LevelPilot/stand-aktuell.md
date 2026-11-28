# LevelPilot – Stand der Sitzung

## Stand 28.11.2026 07:24 · Version 3.13.34 (veröffentlicht, Discord; Prüfung offen) · download/: 3.13.29

## Gerade in Arbeit
- Nichts angefangen. 3.13.34 = LP-FRZ1 (T222 misst Umweg-Faktoren vorher in Portionen, belegt + nachgestellt), T402 Spiel-Format
  "[tail call]", LP-PROT-N1 (T403). Bericht 07:24. T261 im Spiel kalt 671 / warm 682 bestanden (Supervisor 06:52).

## Nächste Schritte (Reihenfolge)
1. Ingametest 3.13.34 (kalt): LP-FRZ1 weg? Zeile "Neuplanung angestossen von" mit echtem Auslöser; "Planung dauerte bis zu 2314 ms" einordnen.
2. HOCH T155 beobachtet (3.13.33: 15,89 ms) – zweiter Lauf < 16 nötig; sonst kalte Wegsuchen (Zeit je Funktion) senken.
3. Protokoll-Hinweise 07:14: Abort-Stapel 05:08 belegen; Speicher "Sicherung 39,1 MB" erklären.
4. Startwegnetz mit Haralds Zonen (Entscheid 05:35): Zonen von B ins Werkzeug, Route 1–60 ALT/NEU, dann EINE Version (vorher T261/T381).
5. MITTEL Grundregeln-Übergang; NIEDRIG LP-UI-AC1, Planner.lua:784; LP-DL1 nach Annahme ohne offenes HOCH; "Wo war ich?" offen.

## Offen beim Nutzer
- Ingametest 3.13.33 kalt: /lp testroutine kalt, /reload, 60 s warten, /lp testroutine alles, danach /reload.
- Frage: "Wo war ich?" beim Einloggen – bleiben oder ab Werk aus?

## Entscheide des Nutzers seit letztem Stand
- 28.11. 05:35: Startwegnetz erst mit Haralds Zonen (B), dann Route ALT/NEU, dann eine Version.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/<Rechner>/forever/konto-5cb3d536/LevelPilot.lua.gz (PC DESKTOP-NVITMSE, Laptop AUSPLUSLAPTOP).
  3.13.31 PC: /home/claude/lpdaten-2811a. Nachbau damit: m2e.sh. Route 1–60: r3.lua MAXL=60 (Bedingungen im Bericht 05:23).
- Messkopien: lpdbg5 (Zeit je Funktion auf Reisen), lpdbg6 (Stichprobe Planung, nur äussere Coroutine – brauchbar), lpdbg7 verworfen.
- Einlog-Messung: "×" = Portionen; "Starts je Auftrag" = Läufe. Im Nachbau laufen Aufträge am Stück (Jobs.sync).
- Wegdaten: seed_bauen.py zählt nur src "selbst", keine Doppelten; Probebau seedprobe2/Wege.lua (9 Zonen).
