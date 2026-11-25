# LevelPilot – Stand der Sitzung

## Stand 25.11.2026 15:59 · Version 3.13.15 (veröffentlicht, Discord, md5 d90dee86daed45bbfe54a085e7c7acef)

## Gerade in Arbeit
- Nichts angefangen. 3.13.15 gepusht. Bericht: berichte/LevelPilot/2026-11-25-1559-3.13.15-lp-y1-tr1-sb1b.txt (umgesetzt, zur Prüfung).
- Inhalt:
  - LP-Y1: LP.YPCall, LP.PCall in der Reise, LP.YieldBlocked/MarkYieldBase.
  - LP-TR1 a): Teilbericht bei Abbruch, T393; dauerBereiche; Zeitlimit vorläufig 3600 s.
  - LP-SB1-b: V:Abort spielt ein, beim Ausloggen sofort.
  - GoldSentinelTest v4.
  - Neue Prüfungen T392–T394.

## Nächste Schritte (Reihenfolge laut Auftrag 25.11. 14:08: LP-Y1 + LP-TR1 a) -> LP-SB1-b -> LP-R1 -> LP-R2 -> LP-I1 …)
1. LP-SB1-b Rest: Routine stellt am Ende LevelPilotDB ganz zurück -> Empfang während der Routine geht verloren (im Code belegt). Plan:
   Empfang am Netzeingang zurückhalten (nicht Comm:Receive, das rufen Prüfungen direkt), nach Restore einspielen, HINWEIS; Test im Nachbau.
2. LP-TR1 b): nach dem nächsten Bericht (dauerBereiche) Zeitlimit festlegen = gemessen im Hintergrund + Rand.
3. LP-R1 MITTEL: Koordinaten ausserhalb 0–100 im Reisebericht.
4. LP-R2 MITTEL: Orte der anderen Fraktion (Feralas 89.4,46.2).
5. LP-I1/I6/I7/I8 (Daten der Figur fehlen), LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.

## Offen beim Nutzer
- Ingametest 3.13.15 (Routine sollte fertig werden; dauerBereiche, abgabeGesperrt, T392–T394).
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
