# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 13:27 · Version 3.13.21 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 3.13.21 (Messzeile T155 im Spiel, Stelle des längsten Reise-Bilds).
- 3.13.19 und 3.13.20 angenommen; Ingametest 3.13.20: LP-TR3 bestanden bis auf 1 Bild (17,5 ms), LP-I3 Rückschritt (T155 29,2 ms).

## Nächste Schritte (Reihenfolge)
1. Ingametest 3.13.21 auswerten: T155-Messzeile (Knoten, µs je Knoten, kalt, geleert) -> Ursache LP-I3 im Spiel belegen, dann beheben.
2. LP-TR3: Stelle der grössten Überschreitung aus "Reisen: …" benennen.
3. LP-R2: lange Luftlinien über Orte der anderen Fraktion in der Planung meiden (Zwischenziel), Gegenprobe Route/Zeit.
4. Die 13 Stücke mit +3–5 MB je Stück nach Stapel einordnen (langeStuecke ab 25 ms).
5. LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.21 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK).
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
- T261 im Nachbau: auf der neu gestarteten Arbeitsmaschine 1 100–1 300 ms auch mit 3.13.19 – Rauschen.
