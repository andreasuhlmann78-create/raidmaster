# LevelPilot – Stand der Sitzung

## Stand 27.11.2026 13:31 · Version 3.13.29 (veröffentlicht, Discord; Messversion) · download/: 3.13.28 (angenommen)

## Gerade in Arbeit
- Nichts angefangen. Neu: LP-DL1 erledigt bis auf Discord-Prüfung (download/LevelPilot-3.13.28.zip, Bericht 13:15; Lauf zum Commit
  abgelöst/cancelled – nächsten durchlaufenden Lauf auswerten). 3.13.29 = speicherPruefungen als Zeilenliste, mit "P" und "zwischen".

## Nächste Schritte (Reihenfolge)
1. Discord-Prüfung: ersten durchlaufenden Lauf nach 13:31 auf download/LevelPilot-3.13.28.zip prüfen, Ergebnis in den nächsten Bericht.
2. MITTEL Speicher (T244–T251 72,7 ms mit −149 MB, T241–T244, T355, T136, T34): mit speicherPruefungen aus dem Ingametest 3.13.29 belegen.
3. MITTEL T155 17,3 ms je Planung (Ziel < 16), längste 66,4 ms; die 447 ms von 3.13.27 kamen nicht wieder.
4. LP-DL1 künftig: nach jeder Annahme mit Ingametest ohne offenes HOCH: neue Zip nach download/, ältere entfernen, addon_check, Workflow.
5. Entscheid "Wo war ich?" beim Einloggen (Frage ST1-Bericht Punkt 4).
6. LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte; NIEDRIG Graph.lua:1048 (keine Änderung ohne Beleg).

## Offen beim Nutzer
- Ingametest 3.13.29 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Frage: "Wo war ich?" beim Einloggen (eigener Schalter, ab Werk an, 2–5 Zeilen) – bleiben oder ab Werk aus?
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Supervisor 13:15: LP-DL1 freigegeben (3.13.28), T215–T217 im Spiel erledigt.

## Wichtig zu wissen
- Uploads: goldsentinel-daten origin/sicherung, aktuell/AUSPLUSLAPTOP/forever/konto-5cb3d536/LevelPilot.lua.gz; Bericht mit lupa aus
  LevelPilotDB.gsTest.reports (GSTEST1, Bereich "alle", Version wählen). Upload 13:10: /home/claude/lpdaten-2711e (3.13.28).
- Nachbau mit Daten 12:35: m2d.sh. Damit T261 im Nachbau FEHLER (Daten); T32 zuletzt 48–50 ms mit Bereinigung (Verdacht Zufall).
- Berichtsfelder als Text werden nach ~300 Zeichen gekürzt – lange Messungen als Liste von Zeilen ablegen (planungen, speicherPruefungen).
- Discord-Prüfung bricht bei jedem neuen Push ab (cancel-in-progress) – erst der letzte Lauf nach einer Ruhepause prüft durch.
- In der Routine ist Jobs.sync an: Hintergrund-Aufträge rechnen dort sofort – in pcall-Prüfungen ohne Abgabe.
