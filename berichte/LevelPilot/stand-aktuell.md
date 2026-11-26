# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 17:09 · Version 3.13.23 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 3.13.23 (LP-I3 Ursache belegt: kalte Gelände-/Gefahrenprüfungen; Gelände −31 %; NearSparse gibt ab).
- 3.13.22 angenommen 16:18. Träge Luftlinien versucht und verworfen (kaum weniger Prüfungen).

## Nächste Schritte (Reihenfolge)
1. LP-I3: Gefahrenprüfung je Strecke billiger (CellsOnLine, Speicher je neuem Startpunkt im segCache), Ergebnis gleich; Ingametest 3.13.23.
2. LP-TR3 abschliessen, wenn das Spiel keine Überschreitung > 6 ms mehr zeigt.
3. Anzeige-Texte +4 MB (T285/T136/T34/T386: Zentrale, Protokoll, Datenseite) messen – MITTEL (auch echte Nutzer).
4. LP-R2: lange Luftlinien über Orte meiden. 5. LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.23 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2c.sh (Daten 26.11. 11:16), m2.sh (ganze Routine Priester 10), msl.sh (lange Reise ohne Hülle, SLICE=…), msl16alt.sh (3.13.16 als Bezug),
  mres.sh/mypc.sh (mit Messhülle – Kosten wachsen mit Portionen, nicht für Dauervergleiche), r3.lua (Reise am Stück, MAXL, NOCFP, COMODE),
  mcfp.sh/mcfpp.sh (Wegprüfung CheckFirstPath), lo395.lua (Empfang + Ausloggen in der Routine).
- Upload 26.11. 09:33 entpackt: /home/claude/lpdaten-2611e (Upload 16:56, bericht.json = 3.13.22 voll mit planungen). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- Den lokalen main von goldsentinel-daten nicht zurücksetzen.
- T261 im Nachbau: auf der neu gestarteten Arbeitsmaschine 1 100–1 300 ms auch mit 3.13.19 – Rauschen.
