# LevelPilot – Stand der Sitzung

## Stand 26.11.2026 08:56 · Version 3.13.17 (veröffentlicht, vom Supervisor angenommen 08:26, Abnahme im Spiel offen)

## Gerade in Arbeit
- Nichts angefangen. Neu: Bericht 2026-11-26-0856-lp-i3-zwischenspeicher-hotfix.txt (Zwischenspeicher für LP-I3 widerlegt; Hotfix-Hinweis
  geprüft, nichts zu tun). Bericht 3.13.17: 2026-11-26-0749-3.13.17-reisebilder-i7-sb1c-tr1-r3-i3.txt.
- Inhalt: Reise-Bilder (Freigabe für ganzen Schritt, 8 Abgabestellen, Bildziel 12 ms), LP-I7 (Art "danger"), LP-SB1-c (+ Ausloggen),
  LP-TR1 b) (1800 s, Dauer im Chat), LP-R3 belegt (nicht die Wegprüfung), LP-I3 belegt (nicht behoben).

## Nächste Schritte (Reihenfolge)
1. LP-I3: belegen, warum die Wegsuche von CheckFirstPath in Undercity so teuer ist (Zwischenspeicher hilft nicht: 0 Wiederholungen je Reise),
   dann die Suche selbst billiger machen, ohne die Grenze zu senken.
2. Reise-Bilder: die 5 Bilder über 16 ms ohne Speicherbereinigung (Nachbau lange Reise) belegen.
3. LP-R1, LP-R2, LP-I1/I6/I8, LP-T31, LP-UMG1, Notbremse "Routenberechnung", Wegabschnitte.
4. Lange Testhilfen-Bilder je Schritt einordnen (T355/T244/T251 Speicherbereinigung).

## Offen beim Nutzer
- Ingametest 3.13.17 (/lp testroutine alles): reiseBilder, T263, T155, T395, Chat-Zeile "Dauer je Bereich (Wanduhr)".
- Datei der Testfigur – Weg klärt der Supervisor, nie ins Repo.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen. Gültig: Dauer der Routine nur ohne Nachteile verkürzen (25.11. 09:40); immer Deutsch (24.11. 18:51).

## Wichtig zu wissen
- Skripte im Scratchpad: m2.sh (ganze Routine Priester 10), mres.sh (lange Reise AREA=B LONG=1, Portionen mit Stapel),
  mypc.sh (Dauer je LP.YPCall), mgapf.sh/gap263.lua (Strecken zwischen Abgaben T263), r3.lua (Reise bis L17, NOCFP/COMODE),
  lo395.lua (Empfang + Ausloggen mitten in der Routine), mplan.sh/plan155.lua (Anteile je Planung).
- Ältere Versionen entpackt unter /home/claude/lpalt/<Version>.
- Prüfungen speisen über TR.Injecting ein; nur echter Empfang wartet (Comm.routineHeld).
- T261 im Nachbau: Rauschen um 1000 ms. Den lokalen main von goldsentinel-daten nicht zurücksetzen.
