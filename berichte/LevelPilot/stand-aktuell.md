# LevelPilot – Stand der Sitzung

## Stand 25.11.2026 10:33 · Version 3.13.14 (veröffentlicht, Discord, md5 bd69e02a56b05c954bdb5a169545a23e)

## Gerade in Arbeit
- Nichts angefangen. 3.13.14 gepusht. Bericht: berichte/LevelPilot/2026-11-25-1033-3.13.14-lp-sb1.txt (umgesetzt, zur Prüfung).
- Inhalt LP-SB1:
  - Empfang während der Reise wartet (Comm.held) und wird danach eingespielt.
  - HINWEIS im Bericht; Schreibzugriffe mit Herkunft (Graph.NoteWrite) als FEHLER.
  - Neue Prüfungen T389–T391.

## Nächste Schritte (Reihenfolge laut Auftrag 25.11. 10:10: LP-SB1 vor LP-I1; danach MITTEL)
1. LP-R1 MITTEL: Koordinaten ausserhalb 0–100 im Reisebericht (Undercity 132.5,187.6; Verwüstete Lande 83.7,-295.2) – Ursache belegen.
2. LP-R2 MITTEL: Wege/Ziele an Orten der anderen Fraktion (Theramore, Seenhain, Thelsamar, Teufelswald, Bergung der Welle); Verdacht
   Fehltreffer Feralas 89.4,46.2 (Zonenübergang).
3. LP-I1/I6/I7/I8: ganzer Testroutine-Bericht 3.13.13 (noch nicht hochgeladen) bzw. Datei der Figur (Weg klärt Supervisor).
4. LP-T31 (Entscheid Supervisor 18:58): T31/T32 Schalter ohne Neuplanung je Schalter, einmal am Ende; Stichprobe 3; Messungen.
   Zusammen mit "Dauer der Testroutine" – nur ohne Nachteile verkürzen (Entscheid des Nutzers 25.11. 09:40).
5. LP-UMG1 MITTEL: Umgebung/Bedienung in der Testroutine erkennen (Klarstellung 20:50: "Rest > eigene Arbeit" allein kein Grund).
6. Offen wie bisher: Notbremse "Routenberechnung" 22.11., Zeile Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.14 und Upload des ganzen Testroutine-Berichts (3.13.13 fehlt noch).
- Datei der Testfigur – Weg klärt der Supervisor mit dem Nutzer, NIE ins öffentliche Repo.

## Entscheide des Nutzers seit letztem Stand
- 25.11. 09:40: Dauer der Testroutine nur verkürzen, wenn es keine Nachteile bringt (keine Reisen kürzen/weglassen, keine kleineren
  Stichproben, keine gröberen Grenzen; je Änderung Ergebnis vorher = nachher belegen; im Zweifel nicht verkürzen).
- 24.11. 20:04: Umgebung/Bedienung in allen Addons erkennen (LP-UMG1).
- 24.11. 18:51: immer Deutsch.
- Supervisor (Nutzer kann ändern): LP-K1 nicht ausweichen (18:56, erledigt); LP-T31 ja mit Bedingungen (18:58).

## Wichtig zu wissen
- Daten Ingametest 3.13.12: /home/claude/lpdaten-2411b/ (aus goldsentinel-daten origin/sicherung). Den lokalen main nicht zurücksetzen.
- Skripte im Scratchpad:
  - Ganze Routine: m3.sh (Stufe 30), m.sh (MININT), m2.sh (Priester 10).
  - mj*.sh/prof_journey.lua: Reise-Portionen. mp3.sh: Stapel langes Bild.
  - offl/: Kopie der Offline-Lua für Einzelläufe (run_offline.py --lupa test40.lua <LevelPilot> 0 Orc WARRIOR Horde, mit
    FOREVER=1 LVL=6 MAP=1411 PX=43.3 PY=68.5 BRAKE=1 PACKDIR=…).
- Offline-Ersatzwelt liegt bei Weltkoordinate −51070, Comm nimmt nur −40000..40000 an (T389 berücksichtigt das).
- T261 im Nachbau: Rauschen um 1000 ms.
- 3.13.14 neu: Comm.HoldDuringJourney/ReplayHeld(now), Graph.NoteWrite/writeOrigin, V.SandboxLines, V.WritesText.
