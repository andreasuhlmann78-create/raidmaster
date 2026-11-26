# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 16:14 · Version 3.13.22 (veröffentlicht, Discord)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 3.13.22 (T155 ungekürzt im Feld "planungen", Stelle der Überschreitung korrigiert, Stücke eingeordnet).
- Ingametest 3.13.21: LP-TR3 erledigt (Supervisor 16:07); LP-I3 offen (T155 Ø 19,9 ms, 189 µs je Knoten).

## Nächste Schritte (Reihenfolge)
1. Ingametest 3.13.22 auswerten: Feld "planungen" (kalt Gelände/Gefahr je Planung) -> Ursache 189 µs je Knoten belegen, dann beheben.
2. Stelle der grössten Budget-Überschreitung aus "Reisen: …" (jetzt richtige Zeile) -> Abgabe dort setzen, wenn ohne Umbau.
3. Stücke +4 MB (T285/T136/T34/T386 – Fenstertexte) im Code lesen und messen.
4. LP-R2: lange Luftlinien über Orte meiden. 5. LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse, Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.22 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK), danach /reload für den Upload.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2c.sh (Daten 26.11. 11:16), m2.sh (ganze Routine Priester 10), msl.sh (lange Reise ohne Hülle, SLICE=…), msl16alt.sh (3.13.16 als Bezug),
  mres.sh/mypc.sh (mit Messhülle – Kosten wachsen mit Portionen, nicht für Dauervergleiche), r3.lua (Reise am Stück, MAXL, NOCFP, COMODE),
  mcfp.sh/mcfpp.sh (Wegprüfung CheckFirstPath), lo395.lua (Empfang + Ausloggen in der Routine).
- Upload 26.11. 09:33 entpackt: /home/claude/lpdaten-2611d (Upload 16:08, bericht.json = 3.13.21 voll). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- Den lokalen main von goldsentinel-daten nicht zurücksetzen.
- T261 im Nachbau: auf der neu gestarteten Arbeitsmaschine 1 100–1 300 ms auch mit 3.13.19 – Rauschen.
