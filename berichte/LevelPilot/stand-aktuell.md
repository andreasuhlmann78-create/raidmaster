# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 10:05 · Version 3.13.18 (veröffentlicht, Discord, md5 ab177f6f374ec2ed5338682398a06000)

## Gerade in Arbeit
- Nichts angefangen. Bericht: berichte/LevelPilot/2026-11-26-1005-3.13.18-lp-tr3-i3-protokoll.txt (umgesetzt, zur Prüfung).
- Inhalt: LP-TR3 (16 Abgabestellen, Ursache YieldBlocked belegt), reiseBilder in Chat/Teilbericht, Protokoll-Messung ohne Pausen,
  D.PlaceHit-Vorprüfung, Einordnung 26 Auffälligkeiten und langsame Stücke.
- 3.13.17 vom Supervisor angenommen 08:26; im Spiel: LP-I7 bestanden, Dauer im Chat erledigt, Logout-Weg belegt.

## Nächste Schritte (Reihenfolge)
1. LP-I3: NearSparse und Abgabeprüfungen in der Wegsuche von CheckFirstPath messen und senken, Speicher je Planung mitsenken (Route gleich).
2. Mitschrift langeStuecke ab 25 ms statt 40 ms (13 Stücke mit +3–5 MB im Spiel, Ursache zu messen).
3. LP-R1, LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.18 (/lp testroutine alles, zwischendurch eine Taste drücken wegen AFK): Reisen <= 992 s, reiseBilder, T155.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2.sh (ganze Routine Priester 10), msl.sh (lange Reise ohne Hülle, SLICE=…), msl16alt.sh (3.13.16 als Bezug),
  mres.sh/mypc.sh (mit Messhülle – Kosten wachsen mit Portionen, nicht für Dauervergleiche), r3.lua (Reise am Stück, MAXL, NOCFP, COMODE),
  mcfp.sh/mcfpp.sh (Wegprüfung CheckFirstPath), lo395.lua (Empfang + Ausloggen in der Routine).
- Upload 26.11. 09:33 entpackt: /home/claude/lpdaten-2611b (bericht.json = 3.13.17 voll). Ältere Versionen: /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- Den lokalen main von goldsentinel-daten nicht zurücksetzen.
