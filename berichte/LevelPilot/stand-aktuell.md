# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 11:51 · Version 3.13.20 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 3.13.20 (LP-R1 behoben, LP-R2 eingeordnet). Davor 3.13.19 (Reise nach Zeit, Wegprüfung schneller).

## Nächste Schritte (Reihenfolge)
1. Ingametest 3.13.19/3.13.20 auswerten: reiseBilder, Reisen <= 985 s, T155, langeStuecke ab 25 ms (T34, T136), T396.
2. LP-R2: lange Luftlinien über Orte der anderen Fraktion in der Planung meiden (Zwischenziel), Gegenprobe Route/Zeit.
3. Die 13 Stücke mit +3–5 MB je Stück nach Stapel einordnen.
4. LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.20 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK).
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2c.sh (Daten 26.11. 11:16), m2.sh (ganze Routine Priester 10), msl.sh (lange Reise ohne Hülle, SLICE=…), msl16alt.sh (3.13.16 als Bezug),
  mres.sh/mypc.sh (mit Messhülle – Kosten wachsen mit Portionen, nicht für Dauervergleiche), r3.lua (Reise am Stück, MAXL, NOCFP, COMODE),
  mcfp.sh/mcfpp.sh (Wegprüfung CheckFirstPath), lo395.lua (Empfang + Ausloggen in der Routine).
- Upload 26.11. 09:33 entpackt: /home/claude/lpdaten-2611b (bericht.json = 3.13.17 voll). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- Den lokalen main von goldsentinel-daten nicht zurücksetzen.
