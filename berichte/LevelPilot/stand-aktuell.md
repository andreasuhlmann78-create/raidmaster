# LevelPilot – Stand der Sitzung

## Stand 25.11.2026 17:12 · Version 3.13.16 (veröffentlicht, Discord, md5 ccf6e5d41c316e6fa94a9c9410b84f73)

## Gerade in Arbeit
- Nichts angefangen. 3.13.16 gepusht. Bericht: berichte/LevelPilot/2026-11-25-1712-3.13.16-lp-tr2.txt (umgesetzt, zur Prüfung).
- Inhalt: LP-TR2 (Reise in der Routine: mehrere gezählte Portionen je Bild bis 8 ms), Feld reiseBilder.
- 3.13.15 vom Supervisor angenommen 16:03.

## Nächste Schritte (Reihenfolge laut Auftrag 25.11. 17:04)
1. LP-R3 MITTEL: Route bis L17 +34 % gegenüber 3.13.13 – Ursache belegen (Verdacht: CheckFirstPath läuft jetzt wirklich).
2. LP-SB1-c MITTEL: Empfang während der Routine am Netzeingang halten, nach Restore einspielen, HINWEIS, Test im Nachbau.
3. LP-TR1 b): Zeitlimit festlegen nach dauerBereiche aus dem Spiel.
4. LP-R1, LP-R2, LP-I1/I6/I7/I8, LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.16 (/lp testroutine alles): dauerBereiche, reiseBilder, abgabeGesperrt, T392–T394.
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).
- Supervisor: 3.13.14 angenommen 10:59 (Nachtrag LP-SB1-b); LP-TR1/LP-Y1 HOCH 14:08; SHARED-T4 14:26.

## Wichtig zu wissen
- Skripte im Scratchpad:
  - Ganze Routine: m3.sh (Stufe 30), m.sh (MININT), m2.sh (Priester 10).
  - Kleines Zeitlimit: mt2.sh (TRT=…). Gesperrte Abgaben mit Stapel: mb2/mb3.sh + blk_hook.lua.
  - Reise-Portionen: mj3.sh. Offline-Kopie: offl/.
- Nachbau = lupa Lua 5.1: Yield über pcall wird dort ebenso abgefangen (pcall gibt false), aber still – darum fiel LP-Y1 nicht auf.
  Jetzt zählt LP.yieldBlocked jede gesperrte Abgabe, LP.yieldErrors jeden gemeldeten Fehler (T392).
- T261 im Nachbau: Rauschen um 1000 ms.
- Daten Ingametest 3.13.12: /home/claude/lpdaten-2411b/. Den lokalen main von goldsentinel-daten nicht zurücksetzen.
