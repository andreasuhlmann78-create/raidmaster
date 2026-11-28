# LevelPilot – Stand der Sitzung

## Stand 28.11.2026 11:10 · Version 3.13.35 (angenommen 11:05, Code) · download/: 3.13.34 (geprüft) · PAUSE bis Mo 30.11./Di 1.12.

## Gerade in Arbeit
- PAUSE (Entscheid 11:07): keine neue Version, keine Ingametests, bis Montag/Dienstag nicht weiterarbeiten.
- Nichts angefangen. 3.13.35 = T261: LP:Throttle plante je Ereignis doppelt (62 + 29 Nachholen in 60 s); neu LP:Coalesce, 3 s.
  Nachbau Ereignis-Sturm: 94 -> 29 Neuplanungen. T404. Bericht 10:47. LP-DL1: download/ = 3.13.34.

## Nächste Schritte (Reihenfolge)
1. Ingametest 3.13.35 (kalt): T261 < 1000? (Erwartung 600–700, Verdacht, zu messen); Zeile "Neuplanung angestossen von".
2. LP-T261-REST NIEDRIG: start 338 ms (Wegnetz, Gefahrenkarte), backup 159 ms – Nachbau 804, Ziel < 800 mit Reserve.
3. Die 2 eigenen ganzen Bilder > 40 ms mit Schritt nennen; LP-TAKT-16 NIEDRIG (T352 zuerst); LP-TAKT-ZU1 MITTEL.
4. Protokoll-Hinweise: "Planung bis 2314 ms", Abort-Stapel 05:08, "Sicherung 39,1 MB".
5. Startwegnetz mit Haralds Zonen (Entscheid 05:35): Zonen von B ins Werkzeug, Route 1–60 ALT/NEU, dann EINE Version.
6. MITTEL Grundregeln-Übergang; NIEDRIG LP-UI-AC1, Planner.lua:784; "Wo war ich?" offen.

## Offen beim Nutzer
- Ingametest 3.13.35 kalt: /lp testroutine kalt, /reload, 60 s warten, /lp testroutine alles, danach /reload.
- Frage: "Wo war ich?" beim Einloggen – bleiben oder ab Werk aus?

## Entscheide des Nutzers seit letztem Stand
- 28.11. 11:07: "wir machen mit LP Montag oder Dienstag weiter" – LevelPilot pausiert.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/<Rechner>/forever/konto-5cb3d536/LevelPilot.lua.gz (PC DESKTOP-NVITMSE, Laptop AUSPLUSLAPTOP).
  Upload 10:34: /home/claude/lpdaten-2811c. Nachbau: m2e.sh (Daten 2811a). Ereignis-Sturm: ev261.lua (EVGAP, EV). Route 1–60: r3.lua MAXL=60.
- LP:Throttle ruft sofort + nach Wartezeit immer (doppelt) – für 23 Nutzer unverändert; Neuplanung nutzt LP:Coalesce.
- Einlog-Messung: "×" = Portionen; "Starts je Auftrag" = Läufe. Im Nachbau laufen Aufträge am Stück (Jobs.sync), T261 dort ohne Ereignis-Sturm.
- Wegdaten: seed_bauen.py zählt nur src "selbst", keine Doppelten; Probebau seedprobe2/Wege.lua (9 Zonen).
