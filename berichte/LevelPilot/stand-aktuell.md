# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 12:43 · Version 3.13.28 (veröffentlicht, Discord; Prüfung offen)

## Gerade in Arbeit
- Nichts angefangen. 3.13.28 = T217 behoben (Ursache belegt: Umweg-Messung am Stück wegen Jobs.sync in der Routine), Feld speicherPruefungen
  (Bericht 27.11. 12:43). 3.13.27 als Messversion angenommen (12:05).

## Nächste Schritte (Reihenfolge)
1. HOCH T155: erste Planung im Spiel 447 ms (Knoten 11239, Umkreis kalt 1105) – im Nachbau mit Daten 12:35 nicht nachgestellt (32 ms).
   Spiel-Zustand vor T155 nachbauen, die Wegsuche mit 11 239 Knoten finden.
2. Speicherbereinigung −159/−115 MB (T355/T136): mit Feld speicherPruefungen aus dem nächsten Ingametest belegen (Prüfungscode oder Ablauf).
3. MITTEL: T136, T355 (40–70 ms), T244, T386, T285. Im Nachbau prüfen: T32 48,4 ms (3.13.27: 35,7) – Rauschen?
4. LP-DL1 / DL-ABN: download/ erst nach Annahme mit Ingametest ohne offenes HOCH.
5. Entscheid "Wo war ich?" beim Einloggen (Frage ST1-Bericht Punkt 4).
6. LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte. Bereich J allein: T298–T300 474–512 ms im Nachbau – prüfen.

## Offen beim Nutzer
- Ingametest 3.13.28 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: ST1-Regeln A–E, Protokoll 60 Einträge, LP-DL1/DL-ABN (download/ nur angenommen).

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz; Bericht mit lupa aus
  LevelPilotDB.gsTest.reports (GSTEST1, Bereich "alle", Version wählen). Upload 12:35: /home/claude/lpdaten-2711d (bericht.json = 3.13.27).
- Nachbau mit Daten 12:35: m2d.sh (m2c.sh mit lpdaten-2711d). Damit T261 im Nachbau FEHLER (auch 3.13.27) – Daten, nicht Code.
- Messkopien: lpdbg3/ + run_lpdbg3.sh (Zeit je Unterfunktion in T217, io.stderr "PROF").
- In der Routine ist Jobs.sync an: Hintergrund-Aufträge rechnen dort sofort – in pcall-Prüfungen ohne Abgabe (vorher in Portionen messen).
- Offline: python3 berichte/LevelPilot/offline/run_offline.py <zip> (40 Läufe).
